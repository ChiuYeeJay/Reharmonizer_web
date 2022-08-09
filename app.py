import audio2midi_modified as audio2midi
import harmonizer
import midi_to_sound
import time
import os
from flask import Flask, abort, jsonify, redirect, render_template, send_file, url_for
from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix

PYTHON = "python3.9"
AUDIO2MIDI_PATH = "audio_to_midi/audio2midi.py"
LOCAL_TEMPFILE_PATH = "tempfiles/"
outer_file_name = ''
temp_path = ''
midi_to_sound_file_paths = None

def save_chord_record(chord_record: list, path: str):
    chord_file = open(path, 'w')
    chord_file.write("\n".join(chord_record))
    chord_file.close()

def generate_temp_path():
    inner_name = str(hash(time.time()))
    counts = 1
    if not os.path.exists(LOCAL_TEMPFILE_PATH):
        os.mkdir(LOCAL_TEMPFILE_PATH)
    while os.path.exists(LOCAL_TEMPFILE_PATH + inner_name):
        inner_name = inner_name.removesuffix(f"_{counts-1}") + f"_{counts}"
        counts += 1
    return LOCAL_TEMPFILE_PATH + inner_name
    
app = Flask(__name__)
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

@app.route("/")
def entry_page():
    return render_template('entry.htm', entry_js_url=url_for('static', filename='entry.js'))

@app.route("/second")
def second_page():
    if temp_path == '':
        return redirect(url_for("entry_page"))
    return render_template("second.htm", second_js_url=url_for('static', filename='second.js'))

@app.post("/upload")
def get_uploaded_audio():
    global outer_file_name
    global temp_path
    outer_file_name = request.files['original_audio'].filename
    temp_path = generate_temp_path()
    os.mkdir(temp_path)

    print(f"id:{temp_path} upload")
    assert os.path.exists(temp_path), f"temp_path({temp_path}) doesn't exist!"

    request.files["original_audio"].save(temp_path+"/origin.wav")
    return jsonify({"status":"audio uploaded!"})

@app.post("/audio2midi")
def go_audio2midi():
    print(f"id:{temp_path} audio2midi")
    assert os.path.exists(temp_path), f"temp_path({temp_path}) doesn't exist!"
    
    audio2midi.run(temp_path+'/origin.wav', temp_path+'/melody.mid')
    return jsonify({"status":"audio processed!"})

@app.post("/harmonize")
def go_harmonizing():
    original_sound_path = temp_path + '/origin.wav'
    melody_midi_path = temp_path + '/melody.mid'
    harmony_midi_path = temp_path + '/harmony.mid'
    result111_path = temp_path + '/result111.wav'
    if not os.path.exists(melody_midi_path):
        return url_for("second_page")
    chord_record = harmonizer.run(input_name=melody_midi_path, output_name=harmony_midi_path, arg=request.json)
    save_chord_record(chord_record, temp_path + '/chord.txt')
    
    global midi_to_sound_file_paths
    midi_to_sound_file_paths = midi_to_sound.midis_to_sound(original_sound_path, melody_midi_path, harmony_midi_path)
    midi_to_sound.combine_sounds(midi_to_sound_file_paths, [True, True, True], result111_path)
    return url_for("second_page")

def generate_mix_audio_name(would_be_combined):
    name = "result"
    for checked in would_be_combined:
        if checked:
            name = name + "1"
        else:
            name = name + "0"
    return name + ".wav"

def generating_harmony_wav_is_needed(harmony_included):
    if not harmony_included:
        return False
    else:
        return os.path.getmtime(temp_path + '/harmony.wav') < os.path.getmtime(temp_path + '/harmony.mid')

def generating_audio_mix_is_needed(result_path, harmony_included):
    if not os.path.exists(result_path):
        return True
    elif not harmony_included:
        return False
    else:
        return os.path.getmtime(result_path) < os.path.getmtime(temp_path + '/harmony.wav')

@app.post("/second/mix_audio")
def go_mixing_audio():
    would_be_combined = request.json.get("would_be_combined")
    result_path = temp_path + "/" + generate_mix_audio_name(would_be_combined)
    harmony_included = would_be_combined[2]
    if generating_harmony_wav_is_needed(harmony_included):
        midi_to_sound.turn_midi_file_into_wav(temp_path + '/harmony.wav')
    if generating_audio_mix_is_needed(result_path, harmony_included):
        midi_to_sound.combine_sounds(midi_to_sound_file_paths, would_be_combined, result_path)
    return send_file(result_path, mimetype="audio/wav", download_name="mixed_audio.wav")

@app.post("/second/get_midi_file")
def get_midi_file_blob():
    which_midi = request.get_data(as_text=True)
    midi_path = ""
    if which_midi == "melody":
        midi_path = temp_path + '/melody.mid'
    elif which_midi == "harmony":
        midi_path = temp_path + '/harmony.mid'
    else:
        abort(400)
    return send_file(midi_path, "audio/midi")

@app.post("/second/get_chords")
def get_chords():
    chord_path = temp_path + "/chord.txt"
    chord_file = open(chord_path, "r")
    chord_txt = chord_file.read()
    chord_file.close()
    return chord_txt

@app.post("/second/hamonize_again")
def hamonize_again():
    harmonization_args = request.get_json()
    print(harmonization_args)
    melody_midi_path = temp_path + '/melody.mid'
    harmony_midi_path = temp_path + '/harmony.mid'
    harmony_wav_path = temp_path + '/harmony.wav'
    if not os.path.exists(melody_midi_path):
        abort(400)
    chord_record = harmonizer.run(input_name=melody_midi_path, output_name=harmony_midi_path, arg=harmonization_args)
    save_chord_record(chord_record, temp_path + '/chord.txt')
    
    midi_to_sound.turn_midi_file_into_wav(harmony_midi_path, harmony_wav_path)
    return ""