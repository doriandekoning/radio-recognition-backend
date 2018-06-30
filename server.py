from flask import Flask
from flask import json
from flask import request
import requests
import base64
import os
import ffmpeg
import tempfile
app = Flask(__name__)

CLASSIFIER_URL = "http://classifier.mmsr-fingerprint.nl"
FINGERPRINTER_URL = 'http://mmsr-fingerprint.nl'

@app.route("/health", methods=['GET'])
def health():
    resp = app.response_class(status=200, response =json.dumps({'status':'ok'}), mimetype='application/json')
    return resp

@app.route("/analysis", methods=['POST'])
def analysis():

    # Fix base64 paddinggi
    #Remove base64 "header"
    base64audio = request.get_json()['audio']
    musicfiles = []
    for x in base64audio:
        # Audio in webm opus format
        audio = base64.b64decode(x.split(",")[1])
        mp3 =  convertAudioToMp3(audio)
        music, classificationConfidence =  classify(mp3)
        print("FUCK YOU", music, classificationConfidence)
        if music == 'music' and classificationConfidence > 0.2 :
            musicfiles.append(mp3)
        else:
            os.remove(mp3)
    if len(musicfiles) == 0:
        return app.response_class(
            status=400,
        )
    #Request to classifier

    concatedAudio = concataAudio(musicfiles)
    

    songname, artist, confidence = fingerprint(concatedAudio)
    
    data = {'stationname':'3fm', 'classification': {'music': music, 'confidence': classificationConfidence}, 'song': {'confidence':confidence, 'name': songname, 'artist':artist}, 'dj':'dorian'}
    response = app.response_class(
        response =json.dumps(data),
        status=200, 
        mimetype='application/json'
    )
    return response

    
def classify(audio):
    response =  requests.post(CLASSIFIER_URL+ "/classify", files ={"file": (audio, open(audio, "rb"), "audio/mpeg")})
    if response.status_code == 200 :
        print(response.json())
        if response.json()['label'] == 'speech' :
            return False, response.json()['confidence']
        elif response.json()['label'] == 'music' :
            return True, response.json()['confidence']
    else :
        print("Something went wrong when classifying", response.status_code)

def fingerprint(audio):
    base64audio = base64.b64encode(audio)
    body = {'extension':'mp3', 'file': base64audio.decode('UTF-8') }
    response = requests.post(FINGERPRINTER_URL + '/recognize', json=body)
    if response.status_code == 200 :
        print( response.json())
        return response.json()['song_name'], response.json()['song_artist'], response.json()['confidence']
    return '', 0.8

def convertAudioToMp3(audio):
    filename = next(tempfile._get_candidate_names())
    file = open(filename +'.webm', 'wb')
    file.write(audio)
    file.close()
    stream  = ffmpeg.input(filename +'.webm')
    stream = ffmpeg.output(stream,  filename + '.mp3', ar=44100, ac=2, acodec='libmp3lame')
    ffmpeg.run(stream)
    os.remove(filename + '.webm')
    return filename + '.mp3'

def concatAudio(files):
    if len(files) == 1 :
        return files[0]
    streams = []
    for x in files:
        streams.append(ffmpeg.input(x))
    concated = ffmpeg.concat(streams)
    outfile = next(tempfile._get_candidate_names())
    ffmpeg.output(concated, outfile + '.mp3')
    file = open(outfile + '.mp3', 'rb')
    out = file.read()
    os.remove(outfile + '.mp3')
    return out



    

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  
    return response


app.run( host='10.164.0.3',port=5000,ssl_context =('/etc/letsencrypt/live/backend.mmsr-fingerprint.nl/fullchain.pem', '/etc/letsencrypt/live/backend.mmsr-fingerprint.nl/privkey.pem'))