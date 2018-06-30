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
LISTENER_URL = 'http://ec2-35-177-142-96.eu-west-2.compute.amazonaws.com'

@app.route("/health", methods=['GET'])
def health():
    resp = app.response_class(status=200, response =json.dumps({'status':'ok'}), mimetype='application/json')
    return resp

@app.route("/analysis", methods=['POST'])
def analysis():

    # Fix base64 paddinggi
    #Remove base64 "header"
    base64audio = request.get_json()['audio']
    files = []
    classifications = []
    for x in base64audio:
        # Audio in webm opus format
        audio = base64.b64decode(x.split(",")[1])
        mp3 =  convertAudioToMp3(audio)
        files.append(mp3)
        music, classificationConfidence =  classify(mp3)
        if music  and classificationConfidence > 0.2 :
            classifications.append(True)
        else:
            classifications.append(False)

    #find first and last speech fragemnt
    firstMusic = len(classifications)
    lastMusic = 0
    for index, classification in enumerate(classifications):
        if index < firstMusic and classification:
            firstMusic = index
        if index > lastMusic and classification:
            lastMusic = index
    musicfiles = files[firstMusic:(lastMusic+1)]
    if len(musicfiles) == 0:
        return app.response_class(
            status=400,
        )
    #Request to classifier

    concatedAudio = concatAudio(musicfiles)
    

    songname, artist, confidence, songID = fingerprint(concatedAudio)

    station = getStation(songID, request.get_json()['timestamp'])



    for file in files:
        os.remove(file)
    
    data = {'classification': {'music': music, 'confidence': classificationConfidence}, 'song': {'confidence':confidence, 'name': songname, 'artist':artist}, 'stationname': station}
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
        return response.json()['song_name'], response.json()['song_artist'], response.json()['confidence'], response.json()['song_id']
    return 'Not found', 0

def getStation(audioId, timestamp):
    params = {'songid': audioId, 'timestamp': timestamp}
    response = requests.get(LISTENER_URL + '/lastplayed', params=params)
    if response.status_code == 200:
        print(response.json())
        return response.json()['station']
    return 'Not found'

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
        file = open(files[0], 'rb')
        out = file.read()
        file.close()
        return out
    outfile = next(tempfile._get_candidate_names())
    cmd = 'ffmpeg -i concat:"'
    for f in files :
        cmd = cmd + f + '|'
    cmd = cmd[:-1]
    cmd = cmd + '" -acodec copy '+  outfile + '.mp3'
    os.system(cmd)
    file = open(outfile + '.mp3', 'rb')
    out = file.read()
    file.close()
    os.remove(outfile + '.mp3')
    return out



    

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  
    return response


app.run( host='10.164.0.3',port=5000,ssl_context =('/etc/letsencrypt/live/backend.mmsr-fingerprint.nl/fullchain.pem', '/etc/letsencrypt/live/backend.mmsr-fingerprint.nl/privkey.pem'))