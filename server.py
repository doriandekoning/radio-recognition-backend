from flask import Flask
from flask import json
from flask import request
import requests
import base64
app = Flask(__name__)

CLASSIFIER_URL = "https://741b00e5-db75-4cab-8380-0903c0299980.mock.pstmn.io"
FINGERPRINTER_URL = 'https://c028d11f-1a21-4d72-a5c5-f5e80b1591e1.mock.pstmn.io'

@app.route("/analysis", methods=['POST'])
def analysis():

    # Fix base64 padding
    #Remove base64 "header"
    base64audio = request.get_json()['audio'].split(",")[1]
    # Audio in webm opus format
    audio = base64.b64decode(base64audio)
    #TODO convert audio to wav


    #Request to classifier

    classify(audio)

    songname, confidence = fingerprint(audio)
    if confidence < 0.7:
        return app.response_class(status=404)
    
    data = {'stationname':'3fm', 'song': {'name':songname, 'artist':'IDLES'}, 'dj':'dorian'}

    response = app.response_class(
        response =json.dumps(data),
        status=200, 
        mimetype='application/json'
    )
    return response

    
def classify(audio):
    request =  requests.get(CLASSIFIER_URL+ "/classify")
    if request.status_code == 200 :
        if request.json()['label'] == 'speech' :
            return False
        elif request.json()['label'] == 'music' :
            return True


def fingerprint(audio):
    file = open('audio.webm')
    file.write(audio)
    file.close()
    request = requests.get(FINGERPRINTER_URL + '/fingerprint')
    if request.status_code == 200 :
        return request.json()['songname'], request.json()['confidence']
    return ''

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response
