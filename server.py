from flask import Flask
from flask import json
from flask import request
import base64
app = Flask(__name__)


@app.route("/analysis", methods=['POST'])
def analysis():
    #Dummy output
    data = {'stationname':'3fm', 'song': {'name':'Colossus', 'artist':'IDLES'}, 'dj':'dorian'}
    # Fix base64 padding
    #Remove base64 "header"
    base64audio = request.get_json()['audio'].split(",")[1]
    # Audio in webm opus format
    audio = base64.b64decode(base64audio)
    response = app.response_class(
        response =json.dumps(data),
        status=200, 
        mimetype='application/json'
    )
    return response

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response