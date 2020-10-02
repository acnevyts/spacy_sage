# This is the file that implements a flask server to do inferences. It's the file that you will modify to
# implement the scoring for your own algorithm.

from __future__ import print_function

import os
import json
import dill as pickle
from io import StringIO 
import sys
import signal
import traceback
import spacy
import process_json

import flask
from flask import jsonify

import pandas as pd

prefix = '/opt/ml/'
model_path = os.path.join(prefix, 'model')

# A singleton for holding the model. This simply loads the model and holds it.
# It has a predict function that does a prediction based on the model and the input data.

class ScoringService(object):
    model = None                # Where we keep the model when it's loaded

    @classmethod
    def get_model(cls):
        """Get the model object for this instance, loading it if it's not already loaded."""
        if cls.model == None:
            target = os.path.join(model_path, r'spacy_ner')
#             target = os.path.join(model_path, r'spacy_ner.pkl')
#             if os.path.getsize(target) > 0:
#                 print(os.path.getsize(target))
#                 with open(target, 'rb') as f:
#                     print(f)
#                     cls.model = pickle.Unpickler(f).load()
#             else: 
#                 print('FILE EMPTY!')
#                 return None
            cls.model = spacy.load(target)
        return cls.model

    @classmethod
    def predict(cls, input):
        """For the input, do the predictions and return them.

        Args:
            input (a pandas dataframe): The data on which to do the predictions. There will be
                one prediction per row in the dataframe"""
        nlp = cls.get_model()
        if not nlp:
            print('NO NLP FOUND')
            return None
        lines = process_json.convert_json_to_lines(None, None, input)
        print(lines)
        if lines:
            line = '. '.join(lines)
            print(line)
            return nlp(line).ents

# The flask app for serving predictions
app = flask.Flask(__name__)

@app.route('/ping', methods=['GET'])
def ping():
    """Determine if the container is working and healthy. In this sample container, we declare
    it healthy if we can load the model successfully."""
    print('Getting Model')
    health = ScoringService.get_model() is not None  # You can insert a health check here
    print('Model Retrieved')

    status = 200 if health else 404
    return flask.Response(response='\n', status=status, mimetype='application/json')

@app.route('/invocations', methods=['POST'])
def transformation():
    """Do an inference on a single batch of data. In this sample server, we take data as CSV, convert
    it to a pandas data frame for internal use and then convert the predictions back to CSV (which really
    just means one prediction per line, since there's a single column.
    """
    data = None

    # Convert from CSV to pandas
    if flask.request.content_type == 'application/json':
        data = flask.request.get_json()
        payload = json.dumps(data)
    else:
        return flask.Response(response='This predictor only supports JSON data', status=415, mimetype='text/plain')

    print('Invoked with {} records'.format(data))

    # Do the prediction
    predictions = ScoringService.predict(data)
    print(predictions)
    # reformat 
    ents = process_json.map_entities(payload, predictions)
    for ent in ents: 
        print(payload[ent['start']:ent['end']])

    # Convert from numpy back to CSV
    response = {}
    # ents = [(e.text, e.start_char, e.end_char, e.label_) for e in predictions]
    response['entities'] = ents
    return jsonify(response) 
