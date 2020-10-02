import spacy
import os
from os.path import isfile, join
from pathlib import Path
import time
import re
import json
import process_json
import random
from spacy.util import minibatch, compounding

local_path = os.path.dirname(__file__)

output_dir = join(local_path, '../local_test/tmp_models')
iterations = 20
new_model_name = "PII_JSON_MODEL"
train= False
test_text_arr = process_json.convert_json_to_lines('70_Flightdata_return.json', '../../data/testing_data')
print(test_text_arr)
test_text = '. '.join(test_text_arr)

start = time.time()

def debug(msg):
    ts = round(time.time() - start, 3)
    print('[{}]: {}'.format(ts, msg))

jsonObj = {
    "Passenger": {
        "PassengerID" : "PID1234",
        "name": "Jim Bob"
    }
}

debug('starting ...')
if train:
    debug('Loading large model...')
    nlp = spacy.blank('en')
    debug('Model loaded.')

    ner = nlp.create_pipe('ner')
    nlp.add_pipe(ner)
    data, labels = process_json.process_data()
    print(data)

    for label in labels:  
        ner.add_label(label)

    optimizer = nlp.begin_training()

    pipe_exceptions = ["ner"]
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]

        # only train NER
    with nlp.disable_pipes(*other_pipes):
        TRAIN_DATA = data
        # show warnings for misaligned entity spans once
        sizes = compounding(1.0, 4.0, 1.001)
        # batch up the examples using spaCy's minibatch
        for itn in range(iterations):
            random.shuffle(TRAIN_DATA)
            batches = minibatch(TRAIN_DATA, size=sizes)
            losses = {}
            for batch in batches:
                texts, annotations = zip(*batch)
                nlp.update(texts, annotations, sgd=optimizer, drop=0.1, losses=losses)
            print("Loss:", losses['ner'])
    doc = nlp(test_text)
    print("Entities in '%s'" % test_text)
    for ent in doc.ents:
        print(ent.label_, ent.text)

    if output_dir is not None:
        output_dir = Path(output_dir)
        if not output_dir.exists():
            output_dir.mkdir()
        nlp.meta["name"] = new_model_name  # rename model
        nlp.to_disk(output_dir)
        print("Saved model to", output_dir)

# test the saved model
print("Loading from", output_dir)
nlp2 = spacy.load(output_dir)
# Check the classes have loaded back consistently
doc2 = nlp2(test_text)
for ent in doc2.ents:
    print(ent.label_, ent.text)
for word in doc2:
    print(word.text + '  ===>', word.lemma_)