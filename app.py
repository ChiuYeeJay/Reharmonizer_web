import json
import audio2midi_modified as audio2midi
import harmonizer
import midi_to_sound
import time
import os
import sys
from crypt import methods
from flask import Flask, jsonify, redirect, render_template, url_for
from flask import request

PYTHON = "python3.9"
AUDIO2MIDI_PATH = "audio_to_midi/audio2midi.py"
LOCAL_TEMPFILE_PATH = "tempfiles/"
outer_file_name = ''
temp_path = ''

def generate_temp_path():
    inner_name = str(hash(time.time()))
    counts = 1
    while os.path.exists(LOCAL_TEMPFILE_PATH + inner_name):
        inner_name = inner_name.removesuffix(f"_{counts-1}") + f"_{counts}"
        counts += 1
    return LOCAL_TEMPFILE_PATH + inner_name
    
app = Flask(__name__)

@app.route("/")
def entry_page():
    return render_template('entry.htm', entry_js_url=url_for('static', filename='entry.js'))

@app.route("/second")
def second_page():
    return render_template("second.htm")

@app.post("/upload")
def get_uploaded_audio():
    global outer_file_name
    global temp_path
    outer_file_name = request.files['original_audio'].filename
    temp_path = generate_temp_path()
    os.mkdir(temp_path)
    request.files["original_audio"].save(temp_path+"/origin.wav")
    return jsonify({"status":"audio uploaded!"})

@app.post("/audio2midi")
def go_audio2midi():
    audio2midi.run(temp_path+'/origin.wav', temp_path+'/origin.mid')
    return url_for("second_page")