# %%
import os
import pydub
import pydub.effects
import piano_synth

# %%
def process_file_paths(original_sound_path, melody_midi_path, harmony_midi_path):
    result_file_path = original_sound_path.removesuffix(".wav") + "_result.wav"
    melody_wav_file_path = melody_midi_path.removesuffix(".mid") + ".wav"
    harmony_wav_file_path = harmony_midi_path.removesuffix(".mid") + ".wav"
    file_paths = {"original_wav":original_sound_path, "melody_midi": melody_midi_path, 
                "harmony_midi":harmony_midi_path, "result":result_file_path, 
                "melody_wav": melody_wav_file_path, "harmony_wav":harmony_wav_file_path}
    return file_paths
    

# %%
PIANO_SOUND_PATH = "piano_sound/"

def turn_midi_file_into_wav(midi_file_path, wav_file_path):
    # print(f"start render {midi_file_path} to {wav_file_path}...")
    piano_synth.midi_file_to_wav(midi_file_path, wav_file_path, PIANO_SOUND_PATH)
    # print("render finish!")

# %%
def combine_sounds(file_paths:dict, would_be_combined:list[bool] = [True, True, True], output_path = ""):
    assert type(would_be_combined) == list, f"type(would_be_combined)={type(would_be_combined)}"
    assert len(would_be_combined) == 3, f"len(would_be_combined)={len(would_be_combined)} != 3"
    
    original_sound = pydub.AudioSegment.from_file(file_paths["original_wav"])
    melody_sound = pydub.AudioSegment.from_wav(file_paths["melody_wav"])
    harmony_sound = pydub.AudioSegment.from_wav(file_paths["harmony_wav"])
    original_sound = pydub.effects.normalize(original_sound, 10)
    melody_sound = pydub.effects.normalize(melody_sound, 10)
    harmony_sound = pydub.effects.normalize(harmony_sound, 10)
    sound_list = [original_sound, melody_sound, harmony_sound]

    # print("start combine...")
    combined_sound: pydub.AudioSegment = pydub.AudioSegment.silent(len(original_sound))
    for i, sound in enumerate(sound_list):
        if not would_be_combined[i]: continue
        combined_sound = combined_sound.overlay(sound)
    combined_sound = pydub.effects.normalize(combined_sound, headroom=1)

    if output_path == "":
        output_path = file_paths["result"]
    combined_sound.export(output_path, format="mp3", bitrate="312k")
    # print("combine finish!")

# %%
def midis_to_sound(original_sound_path:str, melody_midi_path:str, harmony_midi_path:str):
    file_paths = process_file_paths(original_sound_path, melody_midi_path, harmony_midi_path)
    turn_midi_file_into_wav(file_paths["melody_midi"], file_paths["melody_wav"])
    turn_midi_file_into_wav(file_paths["harmony_midi"], file_paths["harmony_wav"])
    return file_paths

# %%
# file_paths = midis_to_sound("mouse_origin.wav", "mouse_melody.mid", "mouse_harmony.mid")
# combine_sounds(file_paths, [True, True, True], "result111.wav")


