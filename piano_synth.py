# %%
import pydub
import pydub.effects
import pretty_midi

import sys
import os

FRAME_RATE = 44100
pitch_dict = {"C":0, "C#":1, "Db":1,"D":2,"D#":3, "Eb":3,"E":4,"F":5,
            "F#":6, "Gb":6,"G":7,"G#":8, "Ab":8,"A":9,"A#":10, "Bb":10,"B":11}

# %% [markdown]
# ## sample mapping

# %%
def build_keymap(sample_path)->list:
    keymap = [None] * 128
    for i in range(21, 111):
        if not os.path.exists(f"{sample_path}/sample_{i}.wav"):
            print(f"'{sample_path}/sample_{i}.wav' do not exist!")
        keymap[i] = pydub.effects.normalize(pydub.AudioSegment.from_wav(f"{sample_path}/sample_{i}.wav"), 10)
    return keymap

# %% [markdown]
# ## constants and utilities

# %%
VELOCITY_CONSTANT = 1.75
EXPRESSION_CONSTANT = 2
CROSS_FADE_TIME = 50
NOTE_INTERNAL_CROSSFADE_TIME = 25

def cc11_to_db_change(val)->float:
    return pydub.utils.ratio_to_db((val/127)**VELOCITY_CONSTANT+0.000001)

def velocity_to_db_change(val)->float:
    return pydub.utils.ratio_to_db((val/127)**EXPRESSION_CONSTANT+0.000001)

def get_certain_type_cc_list(all_cc, cc_number)->list[pretty_midi.ControlChange]:
    result = []
    for cc in all_cc:
        if cc.number == cc_number:
            result.append(cc)
    return result

# %% [markdown]
# ## midi note to sound

# %%
def make_single_note_sound_with_duration(duration, sample:pydub.AudioSegment)->pydub.AudioSegment:
    sound:pydub.AudioSegment
    if duration <= len(sample):
        sound = sample[:duration]
    else:
        sound = sample
    return sound

def midi_note_to_sound(note :pretty_midi.Note, keymap: list)->pydub.AudioSegment:
    duration = round((note.end - note.start)*1000) + CROSS_FADE_TIME   # we here add crossfade time for outer crossfade 
    sample = keymap[note.pitch]
    if sample == None:
        print(f"Warn: no sample at midi num: {note.pitch}")
        return pydub.AudioSegment.silent(duration=duration, frame_rate=FRAME_RATE)

    sound = make_single_note_sound_with_duration(duration, sample)
    
    intensity_db = velocity_to_db_change(note.velocity)
    sound = sound + intensity_db
    
    sound = sound.fade_out(CROSS_FADE_TIME)
    return sound

# %% [markdown]
# ## combine midi notes

# %%
def placing_midi_notes(midi_data, keymap)->pydub.AudioSegment:
    whole_duration = round(midi_data.get_end_time()*1000)
    sound:pydub.AudioSegment = pydub.AudioSegment.silent(duration=whole_duration, frame_rate=FRAME_RATE)
    for note in midi_data.instruments[0].notes:
        note :pretty_midi.Note
        note_start_time = round(note.start*1000)
        sound = sound.overlay(midi_note_to_sound(note, keymap), position=note_start_time)
    return sound


# %% [markdown]
# ## midi_file_to_wav

# %%
def midi_file_to_wav(input_path, output_path, piano_path):
    keymap = build_keymap(piano_path)
    midi_data = pretty_midi.PrettyMIDI(input_path)
    sound = placing_midi_notes(midi_data, keymap)
    sound.export(output_path, "wav", bitrate="312k")

# %% [markdown]
# ## run

# %%
# SOURCE_PATH = "processed/"
# sound = midi_file_to_wav("harmony.mid", "result.wav", SOURCE_PATH)


