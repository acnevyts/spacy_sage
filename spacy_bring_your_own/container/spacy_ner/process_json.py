import json
import re 
import os
from os import listdir
from os.path import isfile, join
import spacy

file_name = '00_PatientAppointmentHL7.json'
test_json_directory= '../../data'
local_path = os.path.dirname(__file__)


def loadInputFile(file_name, dir=None, load_json=True):
    if dir:
        file_name = join(local_path, dir) + '/' + file_name
    else:
        file_name = join(local_path, file_name)
    text = open(file_name, "r").read()
    if load_json: 
        return json.loads(text)
    else: 
        return text

def getSourceFiles():
    rel_path = test_json_directory
    path = join(local_path, rel_path)
    print(path)
    return sorted([join(path,f) for f in listdir(path) if isfile(join(path, f))])
        
  
def camel_case_split(str, join_char=' '):
    arr = re.findall(r'[a-zA-Z](?:[a-z]+|[A-Z]*(?=[A-Z]|$))', str)
    if len(arr) > 0:
        return join_char.join(arr)
    else:
        return arr

def process_leaf(leafs_arr, key, val):
    if val:
        if key:
            leafs_arr.append(key + ' is "' + str(val)+ '"')
        else:
            leafs_arr.append('"' + str(val)+ '"')


def recurive_gen_path(data, curr_string, results):
    local_leafs = []
    if isinstance(data, (dict, list)):
        prev_string = curr_string
        if len(curr_string) > 0:
            curr_string = curr_string + ' ' 
        for key in data:
            if isinstance(data, dict):
                split_key = camel_case_split(key)
                if isinstance(data[key], (list, dict)):
                    recurive_gen_path(data[key], curr_string + split_key, results)
                else:
                    process_leaf(local_leafs, split_key, data[key])
            elif isinstance(key, dict):
                recurive_gen_path(key, prev_string, results)
            else:
                process_leaf(local_leafs, None, key)
    else: 
        process_leaf(local_leafs, split_key, data[key])
    if len(local_leafs) > 0:
        results.append(curr_string + ', '.join(local_leafs))

def convert_json_to_lines(file_name, dir=None, json_data=None):
    if not json_data:
        json_data = loadInputFile(file_name, dir)
    results = []
    recurive_gen_path(json_data,'', results)
    return results


def process_data(input_files=None):
    labels = [] 
    if not input_files:
        input_files = getSourceFiles()
    print(input_files)
    results = []
    for file in input_files:
        results_local = convert_json_to_lines(file)
        for local_res in results_local:
            results.append(local_res)    
    pii_data_list = loadInputFile('PII_Data.json')

    formatted_data = []
    first_run = True
    used_labels = {}

    for res in results:
        entities = []
        for pii_data in pii_data_list:
            label = camel_case_split(pii_data[1], '_').upper()
            if first_run and not used_labels.get(label):
                labels.append(label)
                used_labels[label] = True
            start = None
            try:
                start = res.index('"'+pii_data[0]+'"') + 1
            except ValueError as identifier:
                pass

            if start:
                end = start + len(pii_data[0])
                entities.append((start,end,label))
        formatted_data.append((res, {"entities": entities}))
        first_run = False
    return formatted_data, labels

def traverse_tree(data, path, results):
    if isinstance(data, (list, dict)):
        if isinstance(data, list):
            for num, obj in enumerate(data):
                new_path = ['{}'.format(num)]
                new_path.extend(path)
                traverse_tree(obj, new_path, results)
        else:
        # continue
            for key in data:
                new_path = [key]
                new_path.extend(path)
                traverse_tree(data[key], new_path, results)
    else:
        if data:
            new_path = ['{}'.format(data)]
            new_path.extend(path)
            results.append(new_path)

def map_entities(payload, entities):
    retval = []
    for entity in entities:
        print(entity)
        print(entity.text)
        x = [{
            "start": m.start(), 
            "end":m.end(),
            "text": entity.text,
            "label": entity.label_
        } for m in re.finditer(entity.text, payload)]
        retval.extend(x)
    return retval

def append_jsonp(path, new):
    return "{}['{}']".format(path,new)

def build_jsonp(data, entities, path, results):
    if isinstance(data, dict):
        for key in data:
            build_jsonp(data[key], entities, append_jsonp(path, key), results)
    elif isinstance(data, list):
        for num, obj in enumerate(data):
            build_jsonp(obj, entities, append_jsonp(path, num), results)
    elif isinstance(data, str):
        tmp = map_entities(data, entities)
        for obj in tmp:
            obj['json_path'] = path
        results = results.extend(tmp)

def map_entities_jsonp(payload, entities):
    json_data = json.loads(payload)
    results = []
    build_jsonp(json_data, entities, "$", results)
    return results


# data = loadInputFile('70_Flightdata_return.json', '../../data/testing_data', False)
# sample = [{
#     "text": "PID45678",
#     "label_": "PASSENGER_ID"
# }]
# y = map_entities(data, sample)
# print(y)
# print(data[:88])



# results = []
# traverse_tree(data, [], results)
# print(results)
