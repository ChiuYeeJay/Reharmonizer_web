import sys
import audio2midi_modified as audio2midi
import harmonizer
import midi_to_sound
import time
import os
import pydub
from flask import Flask, abort, jsonify, redirect, render_template, send_file, url_for,  send_from_directory
from flask import request
from werkzeug.middleware.proxy_fix import ProxyFix
PYTHON = "python3.9"
AUDIO2MIDI_PATH = "audio_to_midi/audio2midi.py"
LOCAL_TEMPFILE_PATH = "tempfiles/"


def save_chord_record(chord_record: list, path: str):
    chord_file = open(path, 'w', encoding="utf-8")
    chord_file.write("\n".join(chord_record))
    chord_file.close()


def generate_audio_id():
    inner_name = str(hash(time.time()))
    counts = 1
    if not os.path.exists(LOCAL_TEMPFILE_PATH):
        os.mkdir(LOCAL_TEMPFILE_PATH)
    while os.path.exists(LOCAL_TEMPFILE_PATH + inner_name):
        inner_name = inner_name.removesuffix(f"_{counts-1}") + f"_{counts}"
        counts += 1
    return inner_name


app = Flask(__name__, static_folder='reharm/.next/static/', template_folder='reharm/.next/server/pages',
            static_url_path='/_next/static')

app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)


@app.route("/")
def index():
    return render_template('index.html')
    # def entry_page():
    #     return render_template('entry.htm', entry_js_url=url_for('static', filename='entry.js'))


@app.route("/second")
def second_page():
    return render_template('second.html')


@app.post("/upload")
def get_uploaded_audio():
    print('post upload', file=sys.stderr)
    audio_id = generate_audio_id()
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    os.mkdir(workspace_path)

    assert os.path.exists(
        workspace_path), f"workspace_path({workspace_path}) doesn't exist!"
    uploaded_audio = request.files["original_audio"]
    file_extension = uploaded_audio.filename[uploaded_audio.filename.rfind(
        "."):]
    uploaded_audio.save(workspace_path+"/origin"+file_extension)
    if file_extension != ".wav":
        would_be_converted = pydub.AudioSegment.from_file(
            workspace_path+"/origin"+file_extension)
        would_be_converted.export(
            out_f=workspace_path+"/origin.wav", format="wav")
        os.remove(workspace_path+"/origin"+file_extension)
    return jsonify({"audio_id": audio_id})


@app.post("/audio2midi")
def go_audio2midi():
    clk_start = time.time()
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    assert os.path.exists(
        workspace_path), f"workspace_path({workspace_path}) doesn't exist!"

    audio2midi.run(workspace_path+'/origin.wav', workspace_path+'/melody.mid')
    print(f"audio2midi time: {time.time()-clk_start}")
    return jsonify({"status": "audio processed!"})


@app.post("/harmonize")
def go_harmonizing():
    args = request.json.get("args")
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id

    original_sound_path = workspace_path + '/origin.wav'
    melody_midi_path = workspace_path + '/melody.mid'
    harmony_midi_path = workspace_path + '/harmony.mid'
    result111_path = workspace_path + '/result111.mp3'
    if not os.path.exists(melody_midi_path):
        return url_for("second_page")
    chord_record = harmonizer.run(
        input_name=melody_midi_path, output_name=harmony_midi_path, arg=args)
    save_chord_record(chord_record, workspace_path + '/chord.txt')

    midi_to_sound_file_paths = midi_to_sound.midis_to_sound(
        original_sound_path, melody_midi_path, harmony_midi_path)
    midi_to_sound.combine_sounds(midi_to_sound_file_paths, [
                                 True, True, True], result111_path)
    return url_for("second_page", audio_id=audio_id)


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


def generating_audio_mix_is_needed(result_path, harmony_included, workspace_path):
    if not os.path.exists(result_path):
        return True
    elif not harmony_included:
        return False
    else:
        return os.path.getmtime(result_path) < os.path.getmtime(workspace_path + '/harmony.wav')


@app.post("/second/validate_audio_id")
def validate_audio_id():
    audio_id = request.json.get("audio_id")
    return jsonify({"is_valid": os.path.exists(LOCAL_TEMPFILE_PATH + audio_id)})


@app.post("/second/mix_audio")
def go_mixing_audio():
    audio_id = request.json.get("audio_id")
    would_be_combined = request.json.get("would_be_combined")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id

    original_sound_path = workspace_path + '/origin.wav'
    melody_midi_path = workspace_path + '/melody.mid'
    harmony_midi_path = workspace_path + '/harmony.mid'

    result_path = workspace_path + "/" + \
        generate_mix_audio_name(would_be_combined)
    harmony_included = would_be_combined[2]
    if generating_harmony_wav_is_needed(harmony_included, workspace_path):
        midi_to_sound.turn_midi_file_into_wav(workspace_path + '/harmony.wav')
    if generating_audio_mix_is_needed(result_path, harmony_included, workspace_path):
        midi2sound_file_paths = midi_to_sound.process_file_paths(
            original_sound_path, melody_midi_path, harmony_midi_path)
        midi_to_sound.combine_sounds(
            midi2sound_file_paths, would_be_combined, result_path)
    return send_file(result_path, mimetype="audio/wav", download_name="mixed_audio.wav")


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
    chord_file = open(chord_path, "r", encoding="utf-8")
    chord_txt = chord_file.read()
    chord_file.close()
    return chord_txt


@app.post("/second/hamonize_again")
def hamonize_again():
    harmonization_args = request.json.get("args")
    audio_id = request.json.get("audio_id")
    workspace_path = LOCAL_TEMPFILE_PATH + audio_id
    melody_midi_path = workspace_path + '/melody.mid'
    harmony_midi_path = workspace_path + '/harmony.mid'
    harmony_wav_path = workspace_path + '/harmony.wav'
    if not os.path.exists(melody_midi_path):
        abort(400)
    chord_record = harmonizer.run(
        input_name=melody_midi_path, output_name=harmony_midi_path, arg=harmonization_args)
    save_chord_record(chord_record, workspace_path + '/chord.txt')

    midi_to_sound.turn_midi_file_into_wav(harmony_midi_path, harmony_wav_path)
    return ""
