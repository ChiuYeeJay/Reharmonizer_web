# %%
import numpy as np
import random
from mido import Message, MidiFile, MidiTrack
from mido import MetaMessage
from mido import MidiFile

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
TENSION_INTERVAL_NOTATION = ['unison', 'b9', "9", "#9", "3", "11", "#11", "5", "b13", "13", "b7", "7"]
CHORD_TYPE_ABBREVIATION_TO_FULLNAME = {"maj":"maj7", "min":"min7", "dom":"7", "domsus":"7sus", "dim":"dim7", 
                                       "hdim":"ø7","mM":"minmaj", "aug+7":"aug+7", "aug7":"aug7"}

# index is the interval (measure in half tone), value is the lowest lower note number accepted
LOW_INTERVAL_LIMIT = [-1, 52, 51, 48, 46, 46, 46, 34, 43, 41, 41, 41, -1, 40, 39, 36, 35]
LOW_INTERVAL_PUNISHMENT = 10000
OVER_SPACING_PUNISHMENT = 10000

# %% [markdown]
# ### Global Variable

# %%
OCTAVE = 4

CHORD_TYPE_TREND_ARGS = {"maj":1.5, "min":1.25, "dom":1, "domsus":1, "dim":0.75, "hdim":0.75,"mM":0.75, "aug+7":0.75, "aug7":0.75}
CHORD_TYPE_SELECTION_RANGE = 5

ANTIDIRECTION_AWARD = 0.8
FIFTH_CIRCLE_AWARD = 150
VOICING_OPENCLOSE_STABILITY = 50

SPLIT_TIME = 200
MAX_SUSTAIN_TIME = 2400
OUTPUT_MIDINOTE_VELOCITY = 100

# %% [markdown]
# ## harmonization

# %% [markdown]
# #### utility

# %%
def positive_normalize_list(arr, mul=1):
    s = 0
    for v in arr:
        if v > 0: 
            s += v
    for i in range(len(arr)):
        if arr[i]>0: arr[i] = arr[i]*mul/s
        else: arr[i] = -10
    return arr

def fold_into_an_octave(midi_num):
    return (midi_num+12)%12

def print_chord_record_tuple(record):
    for tp in record:
        print(f"{NOTES[tp[1]]} {tp[2]}: {tp[0]}")

def generate_chord_extension_notation(all_chord_notes:list, additional_notes:list)->str:
    assert len(additional_notes) == 2, "addition notes more than 2"
    tension_notations = []
    for note in additional_notes:
        if all_chord_notes.index(note) == 2:
            continue
        tension_notations.append(TENSION_INTERVAL_NOTATION[note])
    tension_notations.sort(key=lambda item: TENSION_INTERVAL_NOTATION.index(item))
    return "(" + ",".join(tension_notations) +")"

# %% [markdown]
# #### chord scoring

# %%
def generate_all_chordtype_score_templates():
    Cmaj_chord_score = positive_normalize_list([8, -10, 9, -10, 9, -10, 9, 7, -10, 6, -10, 9], CHORD_TYPE_TREND_ARGS["maj"])
    Cmin_chord_score = positive_normalize_list([9, -10, 9, 9, -10, 9, -10, 7, -10, 6, 9, -10], CHORD_TYPE_TREND_ARGS["min"])
    Cdom_chord_score = positive_normalize_list([9, 5, 7, 5, 9, -10, 5, 7, 5, 7, 9, -10], CHORD_TYPE_TREND_ARGS["dom"])
    Cdomsus_chord_score = positive_normalize_list([9, 5, 7, 5, 5, 9, -10, 7, 5, 7, 9, -10], CHORD_TYPE_TREND_ARGS["domsus"])
    Cdim_chord_score = positive_normalize_list([9, -10, 5, 9, -10, 5, 9, -10, 5, 9, -10, 5], CHORD_TYPE_TREND_ARGS["dim"])
    Chdim_chord_score = positive_normalize_list([9, -10, 5, 9, -10, 5, 9, -10, 5, -10, 9, -10], CHORD_TYPE_TREND_ARGS["hdim"])
    CmM_chord_score = positive_normalize_list([9, -10, 7, 9, -10, 5, -10, 7, -10, 5, -10, 9], CHORD_TYPE_TREND_ARGS["mM"])
    Caug_add7_chord_score = positive_normalize_list([9, -10, 7, -10, 9, -10, 5, -10, 9, -10, -10, 9], CHORD_TYPE_TREND_ARGS["aug+7"])
    Caug7_chord_score = positive_normalize_list([9, 5, 7, 5, 9, -10, 5, -10, 9, 5, 9, -10], CHORD_TYPE_TREND_ARGS["aug7"])

    C_chord_scores = {"maj":Cmaj_chord_score, "min":Cmin_chord_score, "dom":Cdom_chord_score, 
                    "domsus":Cdomsus_chord_score, "dim":Cdim_chord_score, "hdim":Chdim_chord_score,
                    "mM":CmM_chord_score, "aug+7":Caug_add7_chord_score, "aug7":Caug7_chord_score}
    return C_chord_scores

def score_all_kinds_of_chords(distribution, last_root):
    C_chord_scores = generate_all_chordtype_score_templates()
    record = []
    last_root = last_root%12
    last_fifth = last_root + 5
    for root in range(12):
        for chord_type in C_chord_scores:
            chord_score = np.roll(C_chord_scores[chord_type], root)
            score = np.dot(distribution, chord_score)
            if root == last_fifth:
                score *= FIFTH_CIRCLE_AWARD
            record.append((score, root, chord_type))
    return record

def notes_to_distribution(notes):
    distribution = [0]*12
    distribution[fold_into_an_octave(notes[0][0])] += notes[0][1]     #first note extra point
    for note_num, duration in notes:
        distribution[fold_into_an_octave(note_num)] += duration
    return distribution

# %% [markdown]
# #### chord generation

# %%
def build_chord_and_tension_notation(root_note, octave, chord_note_basic: list, high_tension: list)->list:
    # get pure root note
    root_note = fold_into_an_octave(root_note)

    # get random 2 notes from chord and tension notes
    chord_note_without_the_used_one = list.copy(chord_note_basic)
    chord_note_without_the_used_one.remove(chord_note_basic[0])
    chord_note_without_the_used_one.remove(chord_note_basic[1])
    chord_note_without_the_used_one.remove(chord_note_basic[3])
    random_additional_notes_1 = random.sample(chord_note_without_the_used_one, 1)[0]
    chord_note_without_the_used_one.remove(random_additional_notes_1)
    random_additional_notes_2 = random.sample(chord_note_without_the_used_one+high_tension, 1)[0]
    
    # tension notation
    tension_notation = generate_chord_extension_notation(chord_note_basic+high_tension, [random_additional_notes_1, random_additional_notes_2])

    # assign and place notes
    root_note = root_note + 12*octave
    third_note = root_note + fold_into_an_octave(chord_note_basic[1])
    seventh_note = root_note + fold_into_an_octave(chord_note_basic[3])
    additional_note1 = root_note + fold_into_an_octave(random_additional_notes_1)
    additional_note2 = root_note + fold_into_an_octave(random_additional_notes_2)
    output_list = [root_note, third_note, seventh_note, additional_note1, additional_note2]
    output_list.sort()
    return output_list, tension_notation

def generate_chord_with_root_and_type_and_provide_tension_notation(root_note, chord_type, octave):
    if chord_type == "maj":
        chord_note = [0, 4, 7, 11, 2, 6, 9]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:5], chord_note[5:])

    elif chord_type == "min":
        chord_note = [0, 3, 7, 10, 2, 5, 8]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:5], chord_note[5:])
    
    elif chord_type == "dom":
        chord_note = [0, 4, 7, 10, 2, 5, 9]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:5], chord_note[5:])
    
    elif chord_type == "domsus":
        chord_note = [0, 5, 7, 10, 2, 9]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:5], chord_note[5:])
    
    elif chord_type == "dim":
        chord_note = [0, 3, 6, 9, 2, 5, 8]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:4], chord_note[4:])

    elif chord_type == "hdim":
        chord_note = [0, 3, 6, 10, 2, 5, 8]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:4], chord_note[4:])
    
    elif chord_type == "mM":
        chord_note = [0, 3, 7, 11, 2, 5, 9]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:4], chord_note[4:])

    elif chord_type == "aug+7":
        chord_note = [0, 4, 8, 11, 2, 6]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:4], chord_note[4:])
    
    elif chord_type == "aug7":
        chord_note = [0, 4, 8, 10, 2, 6, 9]
        return build_chord_and_tension_notation(root_note, octave, chord_note[:4], chord_note[4:])

def random_select_from_record(record):
    score_sum = 0
    for tp in record: score_sum += tp[0]
    normalized = [(tp[0]/score_sum) for tp in record]
    rd_num = random.random()
    count = 0
    for v in normalized:
        rd_num -= v
        if rd_num <= 0: break
        count += 1
    return record[count][1], record[count][2]

# %% [markdown]
# #### voicing and voiceleading

# %%
def considering_8th_note(note_list: list, index: int, cur: list):
    result = []
    for pitch_num in [note_list[index], note_list[index]+12]:
        cur.append(pitch_num)
        if index == 4:
            temp = cur.copy()
            temp.sort()
            if temp[0] == note_list[0] or temp[0] == note_list[0]+12:
                result.append(temp)
        else:
            result.extend(considering_8th_note(note_list, index+1, cur))
        cur.pop()
    return result

def outer_voices_are_contrary_motion(cur, last):
    upper_dir = 0
    if cur[-1] > last[-1]: upper_dir = 1
    elif cur[-1] < last[-1]: upper_dir = -1
    else: upper_dir = 0
    lower_dir = 0
    if cur[0] > last[0]: lower_dir = 1
    elif cur[0] < last[0]: lower_dir = -1
    else: lower_dir = 0
    return upper_dir * lower_dir == -1

def consider_voicing(variation, last_chord):
    bad_voicing_score = 0
    # Low Interval Limit
    for note in variation:
        for interval, lowest_accepted in enumerate(LOW_INTERVAL_LIMIT):
            if note < lowest_accepted and (note+interval) in variation:
                bad_voicing_score += LOW_INTERVAL_PUNISHMENT
    
    # neighbor note interval
    for i in range(len(variation)-1):
        neighbor_interval = variation[i+1]-variation[i]
        if neighbor_interval > 12 and i != 0:
            bad_voicing_score += OVER_SPACING_PUNISHMENT
    
    # open close stability
    if last_chord[-1]-last_chord[0]<12 and variation[-1]-variation[0]<12:
        bad_voicing_score += VOICING_OPENCLOSE_STABILITY * 4
    elif last_chord[-1]-last_chord[0]>12 and variation[-1]-variation[0]>12:
        bad_voicing_score += VOICING_OPENCLOSE_STABILITY
    return bad_voicing_score

def consider_voice_leading(variation: list, last_chord: list):
    minus = np.subtract(np.array(variation), np.array(last_chord))
    diff = np.sum(np.square(minus[:-1])) + minus[-1]**4
    if outer_voices_are_contrary_motion(variation, last_chord):
        diff *= ANTIDIRECTION_AWARD
    return diff

def voicing_and_voice_leading(note_list: list, last_chord: list) ->list:
    for i in range(4):
        note_list.append(note_list[i]+12)
    min_value = 1000000
    min_list = []
    for variation in considering_8th_note(note_list, 0, []):
        diff = consider_voice_leading(variation, last_chord)
        bad_voicing_score = consider_voicing(variation, last_chord)
        score = diff + bad_voicing_score
        if min_value > score:
            min_value = score
            min_list = list(variation)
    return min_list


# %% [markdown]
# #### many_notes_harmonization module

# %%
def many_notes_harmonize(notes, octave, last_chord):
    distribution = notes_to_distribution(notes)
    record = score_all_kinds_of_chords(distribution, last_chord[0])
    top_records = sorted(record, key=lambda s: s[0], reverse=True)[:CHORD_TYPE_SELECTION_RANGE]
    root_note, selected_chord_type = random_select_from_record(top_records)
    note_list, tension_name = generate_chord_with_root_and_type_and_provide_tension_notation(root_note, selected_chord_type, octave)
    output = voicing_and_voice_leading(note_list, last_chord)
    chord_notation = NOTES[root_note] + CHORD_TYPE_ABBREVIATION_TO_FULLNAME[selected_chord_type] + " " + tension_name
    return output, chord_notation

# %% [markdown]
# ## midi io and melody segmentation and run

# %% [markdown]
# ### utilities

# %%
def generate_output_file_name(input_name: str)->str:
    output_name = ""
    if input_name.endswith("_melody.mid"): 
        output_name = input_name.removesuffix("_melody.mid") + "_harmony.mid"
    else:
        output_name = input_name.removesuffix(".mid") + "_harmony.mid"
    return output_name

# %% [markdown]
# ### midi io and melody segmentation

# %%
def make_a_fake_last_chord_for_the_first_chord(octave):
    fake = [0]*5
    fake[0] = random.randint(0,11) + octave*12
    fake[1] = random.randint(0,17) + octave*12
    fake[2] = random.randint(6,17) + octave*12
    fake[3] = random.randint(6,23) + octave*12
    fake[4] = random.randint(12,23) + octave*12
    fake.sort()
    return fake

def add_chord_notes_on_midi_track(newtrack: MidiTrack, chord, on_time, time_acc)->MidiTrack:
    newtrack.append(Message('note_on', note = chord[0], velocity = OUTPUT_MIDINOTE_VELOCITY, time = on_time))
    for note in chord[1:]:
        newtrack.append(Message('note_on', note = note, velocity = OUTPUT_MIDINOTE_VELOCITY, time = 0))

    newtrack.append(Message('note_off', note = chord[0], velocity = OUTPUT_MIDINOTE_VELOCITY, time = time_acc))
    for note in chord[1:]:
        newtrack.append(Message('note_off', note = note, velocity = OUTPUT_MIDINOTE_VELOCITY, time = 0))
    
def melody_segmentation_ad_midiIO(melody_midi_name: str, output_name: str):
    input_midi = MidiFile(melody_midi_name, clip=True)
    newmid = MidiFile()
    newtrack = MidiTrack()
    newmid.tracks.append(newtrack)
    newmid.ticks_per_beat = input_midi.ticks_per_beat

    chord_notation_record = []
    note_list = []
    time_acc = 0
    on_time = 0
    last_chord = make_a_fake_last_chord_for_the_first_chord(OCTAVE)
    for track_iteration, track in enumerate(input_midi.tracks):
        print('Track {}: {}'.format(track_iteration, track.name))
        for msg_iteration, msg in enumerate(track):
            print("round "+ str(msg_iteration) + " : " + str(msg))
            if msg.is_meta:
                if(msg.type == 'end_of_track' and len(note_list)!=0):
                    chord, chord_notation = many_notes_harmonize(note_list, OCTAVE, last_chord)
                    add_chord_notes_on_midi_track(newtrack, chord, on_time, time_acc)
                    chord_notation_record.append(chord_notation)
                    last_chord = chord
                    time_acc = 0
                newtrack.append(msg)
            elif (msg_iteration == 0) and (msg.type == 'note_on'):
                note_list.append((msg.note, msg.time))
                on_time = msg.time
            elif msg.type == 'note_on' and (msg.time > SPLIT_TIME or time_acc > MAX_SUSTAIN_TIME):
                if(len(note_list) != 0):
                    chord, chord_notation = many_notes_harmonize(note_list, OCTAVE, last_chord)
                    add_chord_notes_on_midi_track(newtrack, chord, on_time, time_acc)
                    chord_notation_record.append(chord_notation)
                    last_chord = chord
                    note_list = []
                    time_acc = 0
                on_time = msg.time
            else:
                if(msg.type == 'note_off'):
                    note_list.append((msg.note, msg.time))
                # also add note_on but not excess limit
                time_acc += msg.time
    # output_name = generate_output_file_name(melody_midi_name)
    newmid.save(output_name)
    return chord_notation_record

# %% [markdown]
# ### set global variables

# %%
def set_global_variables(arg: dict):
    global OCTAVE
    global CHORD_TYPE_TREND_ARGS
    global CHORD_TYPE_SELECTION_RANGE
    global ANTIDIRECTION_AWARD
    global FIFTH_CIRCLE_AWARD
    global VOICING_OPENCLOSE_STABILITY
    global SPLIT_TIME
    global MAX_SUSTAIN_TIME
    global OUTPUT_MIDINOTE_VELOCITY

    OCTAVE = 4
    CHORD_TYPE_TREND_ARGS = {"maj":1.5, "min":1.25, "dom":1, "domsus":1, "dim":0.75, "hdim":0.75,"mM":0.75, "aug+7":0.75, "aug7":0.75}
    CHORD_TYPE_SELECTION_RANGE = 5
    ANTIDIRECTION_AWARD = 0.8
    FIFTH_CIRCLE_AWARD = 150
    VOICING_OPENCLOSE_STABILITY = 50
    SPLIT_TIME = 200
    MAX_SUSTAIN_TIME = 2400
    OUTPUT_MIDINOTE_VELOCITY = 100
    
    if arg.get("octave") != None: OCTAVE = arg.get("octave")
    if arg.get("chord_type_trend_args") != None: CHORD_TYPE_TREND_ARGS = arg.get("chord_type_trend_args")
    if arg.get("chord_type_selection_range") != None: CHORD_TYPE_SELECTION_RANGE = arg.get("chord_type_selection_range")
    if arg.get("antidirection_award") != None: ANTIDIRECTION_AWARD = arg.get("antidirection_award")
    if arg.get("fifth_circle_award") != None: FIFTH_CIRCLE_AWARD = arg.get("fifth_circle_award")
    if arg.get("voicing_openclose_stability") != None: VOICING_OPENCLOSE_STABILITY = arg.get("voicing_openclose_stability")
    if arg.get("split_time") != None: SPLIT_TIME = arg.get("split_time")
    if arg.get("max_sustain_time") != None: MAX_SUSTAIN_TIME = arg.get("max_sustain_time")
    if arg.get("output_midinote_velocity") != None: OUTPUT_MIDINOTE_VELOCITY = arg.get("output_midinote_velocity")

# %% [markdown]
# ### run

# %%
def run(input_name, output_name, arg):
    set_global_variables(arg)
    chord_record = melody_segmentation_ad_midiIO(input_name, output_name)
    return chord_record

# %%
# print(run("mouse_melody.mid", "mouse_harmony.mid", {"octave":4}))


