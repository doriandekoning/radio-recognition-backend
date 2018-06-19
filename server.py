from flask import Flask
from flask import json
from flask import request
import requests
import base64
import os
import ffmpeg
app = Flask(__name__)

CLASSIFIER_URL = "https://741b00e5-db75-4cab-8380-0903c0299980.mock.pstmn.io"
FINGERPRINTER_URL = 'http://mmsr-fingerprint.nl'

@app.route("/health", methods=['GET'])
def health():
    resp = app.response_class(status=200, response =json.dumps({'status':'ok'}), mimetype='application/json')
    return resp

@app.route("/analysis", methods=['POST'])
def analysis():

    # Fix base64 padding
    #Remove base64 "header"
    base64audio = request.get_json()['audio'].split(",")[1]
    # Audio in webm opus format
    audio = base64.b64decode(base64audio)


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
    file = open('audio.webm', 'wb')
    file.write(audio)
    file.close()
    stream  = ffmpeg.input('audio.webm')
    stream = ffmpeg.output(stream, 'out.wav', ac=1, acodec='pcm_s16le')
    ffmpeg.run(stream)
    file = open('out.wav', 'rb')
    b = base64.b64encode(file.read())
    file.close()
    body = {'extension':'wav'}#, 'file': b }
    response = requests.post(FINGERPRINTER_URL + '/recognize', json=body)
    if response.status_code == 200 :
        os.remove('out.wav')
        print( response.json()['song_name'], response.json()['confidence']/100.0)
    return '', 0.8

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  
    return response
