from flask import Flask
from flask import json
from flask import request
import requests
import base64
import os
import ffmpeg
app = Flask(__name__)

CLASSIFIER_URL = "http://classifier.mmsr-fingerprint.nl/classify"
FINGERPRINTER_URL = 'http://mmsr-fingerprint.nl'
filenumber = 0

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

    
    music =  classify(audio)
    

    songname, artist, confidence = fingerprint(audio)
    
    data = {'stationname':'3fm', 'song': {'confidence':confidence, 'name': songname, 'artist':artist}, 'dj':'dorian'}
    response = app.response_class(
        response =json.dumps(data),
        status=200, 
        mimetype='application/json'
    )
    return response

    
def classify(audio):
    response =  requests.post(CLASSIFIER_URL+ "/classify", {"audio.wav": audio})
    if response.status_code == 200 :
        print(response.json())
        if response.json()['label'] == 'speech' :
            return False
        elif response.json()['label'] == 'music' :
            return True
    else :
        print("Something went wrong while classyifing", response)


def fingerprint(audio):
    filename = 'audio' + filenumber
    file = open(filename +'.webm', 'wb')
    file.write(audio)
    file.close()
    stream  = ffmpeg.input(filename +'.webm')
    stream = ffmpeg.output(stream,  filename + '.wav', ac=1, acodec='pcm_s16le')
    ffmpeg.run(stream)
    file = open(filename + '.wav', 'rb')
    b = base64.b64encode(file.read())
    file.close()
    body = {'extension':'wav', 'file': b.decode('UTF-8') }
    response = requests.post(FINGERPRINTER_URL + '/recognize', json=body)
    if response.status_code == 200 :
        print( response.json())
        return response.json()['song_name'], response.json()['song_artist'], response.json()['confidence']
    return '', 0.8

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  
    return response


app.run( host='10.164.0.3',port=5000,ssl_context =('/etc/letsencrypt/live/backend.mmsr-fingerprint.nl/fullchain.pem', '/etc/letsencrypt/live/backend.mmsr-fingerprint.nl/privkey.pem'))