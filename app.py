import celery_tasks
import time
import os
import pydub
from flask import Flask, abort, jsonify, redirect, render_template, send_file, url_for
from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix

PYTHON = "python3.9"
LOCAL_TEMPFILE_PATH = "tempfiles/"

def generate_audio_id():
    inner_name = str(hash(time.time()))
    counts = 1
    if not os.path.exists(LOCAL_TEMPFILE_PATH):
        os.mkdir(LOCAL_TEMPFILE_PATH)
    while os.path.exists(LOCAL_TEMPFILE_PATH + inner_name):
        inner_name = inner_name.removesuffix(f"_{counts-1}") + f"_{counts}"
        counts += 1
    return inner_name
    
app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

@app.route("/")
def entry_page():
    return render_template('entry.htm', 
                           entry_js=url_for('static', filename='entry.js'),
                           entry_css=url_for('static', filename="entry.css"),
                           upload_svg=url_for('static', filename='upload.svg'),
                           audio_svg=url_for('static', filename='audio.svg'),
                           arrowright_svg=url_for('static', filename='arrow-right.svg'))

@app.route("/en")
def entry_page_en():
    return render_template('entry_en.htm',
                           entry_js=url_for('static', filename='entry.js'),
                           entry_css=url_for('static', filename="entry.css"),
                           upload_svg=url_for('static', filename='upload.svg'),
                           audio_svg=url_for('static', filename='audio.svg'),
                           arrowright_svg=url_for('static', filename='arrow-right.svg'))

@app.route("/second")
def second_page():
    return render_template("second.htm", second_js_url=url_for('static', filename='second.js'))

@app.route("/second/en")
def second_page_en():
    return render_template("second_en.htm", second_js_url=url_for('static', filename='second.js'))

@app.post("/upload")
def get_uploaded_audio():
    audio_id = generate_audio_id()
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    os.mkdir(workspace_path)

    assert os.path.exists(workspace_path), f"workspace_path({workspace_path}) doesn't exist!"
    uploaded_audio = request.files["original_audio"]
    file_extension = uploaded_audio.filename[uploaded_audio.filename.rfind("."):]
    uploaded_audio.save(workspace_path+"/origin"+file_extension)
    if file_extension != ".wav":
        would_be_converted = pydub.AudioSegment.from_file(workspace_path+"/origin"+file_extension)
        would_be_converted.export(out_f=workspace_path+"/origin.wav", format="wav")
        os.remove(workspace_path+"/origin"+file_extension)
    return jsonify({"audio_id":audio_id})

@app.post("/audio2midi")
def go_audio2midi():
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    assert os.path.exists(workspace_path), f"workspace_path({workspace_path}) doesn't exist!"
    celery_tasks.audio2midi_background.delay(workspace_path)
    return jsonify({"status":"audio2midi start!"})

@app.post("/whether_audio2midi_completed")
def whether_audio2midi_completed():
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    assert os.path.exists(workspace_path), f"workspace_path({workspace_path}) doesn't exist!"
    return jsonify({"status":os.path.exists(workspace_path+'/melody.mid')})

@app.post("/harmonize")
def go_harmonizing():
    harmonization_args = request.json.get("args")
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id

    assert os.path.exists(workspace_path + '/melody.mid'), f"{workspace_path + '/melody.mid'} doesn't exist!"
    celery_tasks.harmonizing_background.delay(workspace_path, harmonization_args)
    return jsonify({"status":"harmonizing start!"})

@app.post("/whether_harmonize_completed")
def whether_harmonize_completed():
    audio_id = request.json.get("audio_id")
    lang = request.json.get("lang")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    assert os.path.exists(workspace_path), f"workspace_path({workspace_path}) doesn't exist!"
    if not os.path.exists(workspace_path + '/result111.mp3'):
        return jsonify({"status":False, "second_url":""})
    if os.path.getsize(workspace_path + '/result111.mp3') == 0:
        return jsonify({"status":False, "second_url":""})
    
    if lang == "en":
        return jsonify({"status":True, "second_url":url_for("second_page_en", audio_id=audio_id)})
    
    return jsonify({"status":True, "second_url":url_for("second_page", audio_id=audio_id)})

def generate_mix_audio_name(would_be_combined):
    name = "result"
    for checked in would_be_combined:
        if checked:
            name = name + "1"
        else:
            name = name + "0"
    return name + ".mp3"

def generating_harmony_wav_is_needed(harmony_included, workspace_path):
    if not harmony_included:
        return False
    else:
        return os.path.getmtime(workspace_path + '/harmony.wav') < os.path.getmtime(workspace_path + '/harmony.mid')

def generating_audio_mix_is_needed(harmony_wav_needed, result_path, harmony_included, workspace_path):
    if harmony_wav_needed:
        return True
    elif not os.path.exists(result_path):
        return True
    elif not harmony_included:
        return False
    else:
        return os.path.getmtime(result_path) < os.path.getmtime(workspace_path + '/harmony.wav')

@app.post("/second/validate_audio_id")
def validate_audio_id():
    audio_id = request.json.get("audio_id")
    return jsonify({"is_valid":os.path.exists(LOCAL_TEMPFILE_PATH + audio_id)})

@app.post("/second/mix_audio")
def go_mixing_audio():
    audio_id = request.json.get("audio_id")
    would_be_combined = request.json.get("would_be_combined")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id


    result_path = workspace_path + "/" + generate_mix_audio_name(would_be_combined)
    harmony_included = would_be_combined[2]
    harmony_wav_needed = generating_harmony_wav_is_needed(harmony_included, workspace_path)
    audio_mix_needed = generating_audio_mix_is_needed(harmony_wav_needed, result_path, harmony_included, workspace_path)
    if harmony_wav_needed or audio_mix_needed:
        if os.path.exists(result_path):
            last_mtime = os.path.getmtime(result_path)
        else:
            last_mtime = 0
        celery_tasks.mixing_audio_background.delay(workspace_path, result_path, would_be_combined, harmony_wav_needed, audio_mix_needed)
    else:
        last_mtime = 0

    return jsonify({"status":"start mixing audio", "last_mtime":last_mtime})

@app.post("/second/whether_mix_audio_completed")
def whether_mix_audio_completed():
    audio_id = request.json.get("audio_id")
    would_be_combined = request.json.get("would_be_combined")
    last_mtime = request.json.get("last_mtime")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    result_path = workspace_path + "/" + generate_mix_audio_name(would_be_combined)

    assert os.path.exists(workspace_path), f"workspace_path({workspace_path}) doesn't exist!"
    content = ""
    if os.path.exists(result_path) and os.path.getmtime(result_path) > last_mtime and os.path.getsize(result_path):
        content = send_file(result_path, mimetype="audio/mp3", download_name="mixed_audio.mp3")

    return content

@app.post("/second/get_midi_file")
def get_midi_file_blob():
    which_midi = request.json.get("which_midi")
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    midi_path = ""
    if which_midi == "melody":
        midi_path = workspace_path + '/melody.mid'
    elif which_midi == "harmony":
        midi_path = workspace_path + '/harmony.mid'
    else:
        abort(400)
    return send_file(midi_path, "audio/midi")

@app.post("/second/get_chords")
def get_chords():
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    chord_path = workspace_path + "/chord.txt"
    chord_file = open(chord_path, "r")
    chord_txt = chord_file.read()
    chord_file.close()
    return chord_txt

@app.post("/second/hamonize_again")
def hamonize_again():
    harmonization_args = request.json.get("args")
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    assert os.path.exists(workspace_path + '/melody.mid'), f"{workspace_path + '/melody.mid'} doesn't exist!"

    if os.path.exists(workspace_path + '/chord.txt'):
        last_chord_mtime = os.path.getmtime(workspace_path + '/chord.txt')
    else:
        last_chord_mtime = 0
    
    celery_tasks.harmonize_again_background.delay(workspace_path, harmonization_args)
    return jsonify({"status":"hamonize_again start!", "last_mtime":last_chord_mtime})

@app.post("/whether_harmonize_again_completed")
def whether_harmonize_again_completed():
    audio_id = request.json.get("audio_id")
    last_mtime = request.json.get("last_mtime")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    assert os.path.exists(workspace_path), f"workspace_path({workspace_path}) doesn't exist!"

    if os.path.exists(workspace_path + '/chord.txt'):
        is_completed = os.path.getmtime(workspace_path + '/chord.txt') > last_mtime
    else:
        is_completed = False
    
    return jsonify({"status":is_completed})
# def whether_sth_completed():