import celery
import harmonizer
import midi_to_sound
import audio2midi_modified as audio2midi
import audioread.ffdec

LOCAL_TEMPFILE_PATH = "tempfiles/"

celery_app = celery.Celery('celery_tasks', backend='rpc://', broker='pyamqp://guest@localhost//')

def save_chord_record(chord_record: list, path: str):
    chord_file = open(path, 'w')
    chord_file.write("\n".join(chord_record))
    chord_file.close()

@celery_app.task
def audio2midi_background(workspace_path):
    # In order to avoid exception in audio2midi.run(), using audioread directly.
    audioread_obj = audioread.ffdec.FFmpegAudioFile(workspace_path+'/origin.wav')
    audio2midi.run(audioread_obj, workspace_path+'/melody.mid')

@celery_app.task
def harmonizing_background(workspace_path, harmonization_args):
    original_sound_path = workspace_path + '/origin.wav'
    melody_midi_path = workspace_path + '/melody.mid'
    harmony_midi_path = workspace_path + '/harmony.mid'
    result111_path = workspace_path + '/result111.mp3'
    chord_record = harmonizer.run(input_name=melody_midi_path, output_name=harmony_midi_path, arg=harmonization_args)
    save_chord_record(chord_record, workspace_path + '/chord.txt')

    midi_to_sound_file_paths = midi_to_sound.midis_to_sound(original_sound_path, melody_midi_path, harmony_midi_path)
    midi_to_sound.combine_sounds(midi_to_sound_file_paths, [True, True, True], result111_path)

@celery_app.task
def harmonize_again_background(workspace_path, harmonization_args):
    melody_midi_path = workspace_path + '/melody.mid'
    harmony_midi_path = workspace_path + '/harmony.mid'
    chord_record = harmonizer.run(input_name=melody_midi_path, output_name=harmony_midi_path, arg=harmonization_args)
    save_chord_record(chord_record, workspace_path + '/chord.txt')

@celery_app.task
def mixing_audio_background(workspace_path, result_path, would_be_combined, harmony_wav_needed, audio_mix_needed):
    original_sound_path = workspace_path + '/origin.wav'
    melody_midi_path = workspace_path + '/melody.mid'
    harmony_midi_path = workspace_path + '/harmony.mid'

    if harmony_wav_needed:
        midi_to_sound.turn_midi_file_into_wav(harmony_midi_path, workspace_path + '/harmony.wav')
    if audio_mix_needed:
        midi2sound_file_paths = midi_to_sound.process_file_paths(original_sound_path, melody_midi_path, harmony_midi_path)
        midi_to_sound.combine_sounds(midi2sound_file_paths, would_be_combined, result_path)