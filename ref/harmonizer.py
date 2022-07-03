import numpy as np
import librosa
import random
from mido import Message, MidiFile, MidiTrack
from mido import MetaMessage
from mido import MidiFile
import sys

input_file_name = sys.argv[1]
melody_midi_name = input_file_name.replace(".wav", "_melody.mid")
harmony_midi_name = input_file_name.replace(".wav", "_harmony.mid")

"""Audio-to-MIDI converter using librosa"""
import numpy as np
import librosa
import midiutil
import sys

def transition_matrix(note_min, note_max, p_stay_note, p_stay_silence):
    """
    Returns the transition matrix with one silence state and two states
    (onset and sustain) for each note.

    Parameters
    ----------
    note_min : string, 'A#4' format
        Lowest note supported by this transition matrix
    note_max : string, 'A#4' format
        Highest note supported by this transition matrix
    p_stay_note : float, between 0 and 1
        Probability of a sustain state returning to itself.
    p_stay_silence : float, between 0 and 1
        Probability of the silence state returning to itselt.

    Returns
    -------
    T : numpy 2x2 array
        Trasition matrix in which T[i,j] is the probability of
        going from state i to state j

    """
    
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi(note_max)
    n_notes = midi_max - midi_min + 1
    p_ = (1-p_stay_silence)/n_notes
    p__ = (1-p_stay_note)/(n_notes+1)
    
    # Transition matrix:
    # State 0 = silence
    # States 1, 3, 5... = onsets
    # States 2, 4, 6... = sustains
    T = np.zeros((2*n_notes+1, 2*n_notes+1))

    # State 0: silence
    T[0,0] = p_stay_silence
    for i in range(n_notes):
        T[0, (i*2)+1] = p_
    
    # States 1, 3, 5... = onsets
    for i in range(n_notes):
        T[(i*2)+1, (i*2)+2] = 1

    # States 2, 4, 6... = sustains
    for i in range(n_notes):
        T[(i*2)+2, 0] = p__
        T[(i*2)+2, (i*2)+2] = p_stay_note
        for j in range(n_notes):        
            T[(i*2)+2, (j*2)+1] = p__
    
    return T


def probabilities(y, note_min, note_max, sr, frame_length, window_length, hop_length, pitch_acc, voiced_acc, onset_acc, spread):
    """
    Estimate prior (observed) probabilities from audio signal
    

    Parameters
    ----------
    y : 1-D numpy array
        Array containing audio samples
        
    note_min : string, 'A#4' format
        Lowest note supported by this estimator
    note_max : string, 'A#4' format
        Highest note supported by this estimator
    sr : int
        Sample rate.
    frame_length : int 
    window_length : int
    hop_length : int
        Parameters for FFT estimation
    pitch_acc : float, between 0 and 1
        Probability (estimated) that the pitch estimator is correct.
    voiced_acc : float, between 0 and 1
        Estimated accuracy of the "voiced" parameter.
    onset_acc : float, between 0 and 1
        Estimated accuracy of the onset detector.
    spread : float, between 0 and 1
        Probability that the singer/musician had a one-semitone deviation
        due to vibrato or glissando.

    Returns
    -------
    P : 2D numpy array.
        P[j,t] is the prior probability of being in state j at time t.

    """
    
    fmin = librosa.note_to_hz(note_min)
    fmax = librosa.note_to_hz(note_max)
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi(note_max)
    n_notes = midi_max - midi_min + 1
    
    # F0 and voicing
    f0, voiced_flag, voiced_prob = librosa.pyin(y, fmin*0.9, fmax*1.1, sr, frame_length, window_length, hop_length)
    tuning = librosa.pitch_tuning(f0)
    f0_ = np.round(librosa.hz_to_midi(f0-tuning)).astype(int)
    onsets = librosa.onset.onset_detect(y, sr=sr, hop_length=hop_length, backtrack=True)


    P = np.ones( (n_notes*2 + 1, len(f0)) )

    for t in range(len(f0)):
        # probability of silence or onset = 1-voiced_prob
        # Probability of a note = voiced_prob * (pitch_acc) (estimated note)
        # Probability of a note = voiced_prob * (1-pitch_acc) (estimated note)
        if voiced_flag[t]==False:
            P[0,t] = voiced_acc
        else:
            P[0,t] = 1-voiced_acc

        for j in range(n_notes):
            if t in onsets:
                P[(j*2)+1, t] = onset_acc
            else:
                P[(j*2)+1, t] = 1-onset_acc

            if j+midi_min == f0_[t]:
                P[(j*2)+2, t] = pitch_acc

            elif np.abs(j+midi_min-f0_[t])==1:
                P[(j*2)+2, t] = pitch_acc * spread

            else:
                P[(j*2)+2, t] = 1-pitch_acc

    return P

def states_to_pianoroll(states, note_min, note_max, hop_time):
    """
    Converts state sequence to an intermediate, internal piano-roll notation

    Parameters
    ----------
    states : int
        Sequence of states estimated by Viterbi
    note_min : string, 'A#4' format
        Lowest note supported by this estimator
    note_max : string, 'A#4' format
        Highest note supported by this estimator
    hop_time : float
        Time interval between two states.

    Returns
    -------
    output : List of lists
        output[i] is the i-th note in the sequence. Each note is a list
        described by [onset_time, offset_time, pitch].

    """
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi(note_max)
    
    states_ = np.hstack( (states, np.zeros(1)))
    
    # possible types of states
    silence = 0
    onset = 1
    sustain = 2

    my_state = silence
    output = []
    
    last_onset = 0
    last_offset = 0
    last_midi = 0
    for i in range(len(states_)):
        if my_state == silence:
            if int(states_[i]%2) != 0:
                # Found an onset!
                last_onset = i * hop_time
                last_midi = ((states_[i]-1)/2)+midi_min
                last_note = librosa.midi_to_note(last_midi)
                my_state = onset


        elif my_state == onset:
            if int(states_[i]%2) == 0:
                my_state = sustain

        elif my_state == sustain:
            if int(states_[i]%2) != 0:
                # Found an onset.                
                # Finish last note
                last_offset = i*hop_time
                my_note = [last_onset, last_offset, last_midi, last_note]
                output.append(my_note)
                
                # Start new note
                last_onset = i * hop_time
                last_midi = ((states_[i]-1)/2)+midi_min
                last_note = librosa.midi_to_note(last_midi)
                my_state = onset
            
            elif states_[i]==0:
                # Found silence. Finish last note.
                last_offset = i*hop_time
                my_note = [last_onset, last_offset, last_midi, last_note]
                output.append(my_note)
                my_state = silence

    return output


def pianoroll_to_midi(y, pianoroll):
    """
    

    Parameters
    ----------
    y : 1D numpy array.
        Audio signal (used to estimate BPM)
        
    pianoroll : list
        A pianoroll list as estimated by states_to_pianoroll().

    Returns
    -------
    None.

    """
    bpm = librosa.beat.tempo(y)[0]
    print(bpm)
    quarter_note = 60/bpm
    ticks_per_quarter = 1024
    
    onsets = np.array([p[0] for p in pianoroll])
    offsets = np.array([p[1] for p in pianoroll])
    
    onsets = onsets / quarter_note
    offsets = offsets  / quarter_note
    durations = offsets-onsets
    
    
    MyMIDI = midiutil.MIDIFile(1)
    MyMIDI.addTempo(0, 0, bpm)
    
    for i in range(len(onsets)):
        MyMIDI.addNote(0, 0, int(pianoroll[i][2]), onsets[i], durations[i], 100)

    return MyMIDI
        

def run(file_in, file_out):
    #sr=22050
    note_min='A2'
    note_max='E6'
    voiced_acc = 0.9
    onset_acc = 0.8
    frame_length=2048
    window_length=1024
    hop_length=256
    pitch_acc = 0.99
    spread = 0.6
    
    y, sr = librosa.load(file_in)

    T = transition_matrix(note_min, note_max, 0.9, 0.2)
    P = probabilities(y, note_min, note_max, sr, frame_length, window_length, hop_length, pitch_acc, voiced_acc, onset_acc, spread)
    p_init = np.zeros(T.shape[0])
    p_init[0] = 1
    
    states = librosa.sequence.viterbi(P, T, p_init=p_init)
    #print(states)
    pianoroll=states_to_pianoroll(states, note_min, note_max, hop_length/sr)
    #print(pianoroll)
    MyMIDI = pianoroll_to_midi(y, pianoroll)
    with open(file_out, "wb") as output_file:
        MyMIDI.writeFile(output_file)

run(input_file_name, melody_midi_name)

NOTES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
RANGE = 5
used_chord_list = []

def positive_normalize_list(arr, mul=1):
    s = 0
    for v in arr:
        if v > 0: 
            s += v
    # print(s)
    for i in range(len(arr)):
        if arr[i]>0: arr[i] = arr[i]*mul/s
        else: arr[i] = -10
    # print(arr)
    return arr

def fold_into_an_octave(midi_num):
    return (midi_num+12)%12

def print_chord_record_tuple(record):
    for tp in record:
        print(f"{NOTES[tp[1]]} {tp[2]}: {tp[0]}")

Cmaj_chord_score = positive_normalize_list([8, -10, 9, -10, 9, -10, 9, 7, -10, 6, -10, 9], 1.5)
Cmin_chord_score = positive_normalize_list([9, -10, 9, 9, -10, 9, -10, 7, -10, 6, 9, -10], 1.25)
Cdom_chord_score = positive_normalize_list([9, 5, 7, 5, 9, -10, 5, 7, 5, 7, 9, -10], 1)
Cdomsus_chord_score = positive_normalize_list([9, 5, 7, 5, 5, 9, -10, 7, 5, 7, 9, -10], 1)
Cdim_chord_score = positive_normalize_list([9, -10, 5, 9, -10, 5, 9, -10, 5, 9, -10, 5], 0.75)
Chdim_chord_score = positive_normalize_list([9, -10, 5, 9, -10, 5, 9, -10, 5, -10, 9, -10], 0.75)
CmM_chord_score = positive_normalize_list([9, -10, 7, 9, -10, 5, -10, 7, -10, 5, -10, 9], 0.75)
Caug_add7_chord_score = positive_normalize_list([9, -10, 7, -10, 9, -10, 5, -10, 9, -10, -10, 9], 0.75)
Caug7_chord_score = positive_normalize_list([9, 5, 7, 5, 9, -10, 5, -10, 9, 5, 9, -10], 0.75)

C_chrod_scores = {"maj":Cmaj_chord_score, "min":Cmin_chord_score, "dom":Cdom_chord_score, 
                  "domsus":Cdomsus_chord_score, "dim":Cdim_chord_score, "hdim":Chdim_chord_score,
                  "mM":CmM_chord_score, "aug+7":Caug_add7_chord_score, "aug7":Caug7_chord_score}

def score_all_kinds_of_chords(distribution):
    record = []
    for root in range(12):
        for chord_type in C_chrod_scores:
            chord_score = np.roll(C_chrod_scores[chord_type], root)
            score = np.dot(distribution, chord_score)
            record.append((score, root, chord_type))
    return record

def notes_to_distribution(notes):
    distribution = [0]*12
    distribution[fold_into_an_octave(notes[0][0])] += notes[0][1]     #first note extra point
    for note_num, duration in notes:
        distribution[fold_into_an_octave(note_num)] += duration
    return distribution

def build_chord(root_note, octave, chord_note_basic: list, high_tension: list)->list:
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

    # assign and place notes
    root_note = root_note + 12*octave
    third_note = root_note + fold_into_an_octave(chord_note_basic[1])
    seventh_note = root_note + fold_into_an_octave(chord_note_basic[3])
    additional_note1 = root_note + fold_into_an_octave(random_additional_notes_1)
    additional_note2 = root_note + fold_into_an_octave(random_additional_notes_2)
    output_list = [root_note, third_note, seventh_note, additional_note1, additional_note2]
    output_list.sort()
    return output_list

def generate_chord_with_root_and_type(root_note, chord_type, octave):
    if chord_type == "maj":
        chord_note = [0, 4, 7, 11, 2, 6, 9]
        return build_chord(root_note, octave, chord_note[:5], chord_note[5:])

    elif chord_type == "min":
        chord_note = [0, 3, 7, 10, 2, 5, 8]
        return build_chord(root_note, octave, chord_note[:5], chord_note[5:])
    
    elif chord_type == "dom":
        chord_note = [0, 4, 7, 10, 2, 5, 9]
        return build_chord(root_note, octave, chord_note[:5], chord_note[5:])
    
    elif chord_type == "domsus":
        chord_note = [0, 5, 7, 10, 2, 9]
        return build_chord(root_note, octave, chord_note[:5], chord_note[5:])
    
    elif chord_type == "dim":
        chord_note = [0, 3, 6, 9, 2, 5, 8]
        return build_chord(root_note, octave, chord_note[:4], chord_note[4:])

    elif chord_type == "hdim":
        chord_note = [0, 3, 6, 10, 2, 5, 8]
        return build_chord(root_note, octave, chord_note[:4], chord_note[4:])
    
    elif chord_type == "mM":
        chord_note = [0, 3, 7, 11, 2, 5, 9]
        return build_chord(root_note, octave, chord_note[:4], chord_note[4:])

    elif chord_type == "aug+7":
        chord_note = [0, 4, 8, 11, 2, 6]
        return build_chord(root_note, octave, chord_note[:4], chord_note[4:])
    
    elif chord_type == "aug7":
        chord_note = [0, 4, 8, 10, 2, 6, 9]
        return build_chord(root_note, octave, chord_note[:4], chord_note[4:])

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

def considering_8th_note(note_list: list, index: int, cur: list):
    result = []
    cur.append(note_list[index])
    if index == 4:
        result.append(cur.copy())
    else:
        result.extend(considering_8th_note(note_list, index+1, cur))

    cur.pop()
    cur.append(note_list[index]+12)
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

# index is the interval (measure in half tone), value is the lowest lower note number accepted
LOW_INTERVAL_LIMIT = [-1, 52, 51, 48, 46, 46, 46, 34, 43, 41, 41, 41, -1, 40, 39, 36, 35]
LOW_INTERVAL_PUNISHMENT = 10000
OVER_SPACING_PUNISHMENT = 10000


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
    
    # open or close
    if last_chord[-1]-last_chord[0]<12 and variation[-1]-variation[0]<12:
        bad_voicing_score += 100
    elif last_chord[-1]-last_chord[0]>12 and variation[-1]-variation[0]>12:
        bad_voicing_score += 50
    return bad_voicing_score

ANTIDIRECTION_AWARD = 0.8
# minvaluehistory = []
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
    # minvaluehistory = []
    for variation in considering_8th_note(note_list, 0, []):
        diff = consider_voice_leading(variation, last_chord)
        bad_voicing_score = consider_voicing(variation, last_chord)
        score = diff + bad_voicing_score
        # minvaluehistory.append((score, variation, outer_voices_are_contrary_motion(variation, last_chord)))
        if min_value > score:
            min_value = score
            min_list = list(variation)
    # minvaluehistory.sort()
    # for item in minvaluehistory[:10]:
    #     print(item)
    return min_list

def many_notes_harmonize(notes, octave, last_chord):
    distribution = notes_to_distribution(notes)
    record = score_all_kinds_of_chords(distribution)
    top_records = sorted(record, key=lambda s: s[0], reverse=True)[:RANGE]
    root_note, selected_chord_type = random_select_from_record(top_records)
    # print(NOTES[root_note], selected_chord_type)
    # used_chord_list.append(NOTES[root_note] + " " + selected_chord_type)
    note_list = generate_chord_with_root_and_type(root_note, selected_chord_type, octave)
    output = voicing_and_voice_leading(note_list, last_chord)
    # print(f"note_list={note_list}, output={output}")
    return output

used_chord_list = []
OCTAVE = 4
mid = MidiFile(melody_midi_name, clip=True)
newmid = MidiFile()
newtrack = MidiTrack()
newmid.tracks.append(newtrack)
newmid.ticks_per_beat = mid.ticks_per_beat

split_time = 200
max_sustain_time = 2400
note_list = []
onset_list = []
time_acc = 0
on_time = 0
last_chord = []
for i, track in enumerate(mid.tracks):
    print('Track {}: {}'.format(i, track.name))
    for m, msg in enumerate(track):
        print("round "+ str(m) + " : " + str(msg))
        if msg.is_meta:
            
            if(msg.type == 'end_of_track' and len(note_list)!=0):
                if(len(note_list) != 0):
                    chord = many_notes_harmonize(note_list, OCTAVE, last_chord)
                    for i, note in enumerate(chord):
                        # former
                        if(i==0):
                            newtrack.append(Message('note_on', note = note, velocity = 100, time = on_time))  
                        else:
                            newtrack.append(Message('note_on', note = note, velocity = 100, time = 0)) 
                        
                    for i, note in enumerate(chord): 
                        if(i==0):   
                            newtrack.append(Message('note_off', note = note, velocity = 100, time = time_acc))  
                        else:
                            newtrack.append(Message('note_off', note = note, velocity = 100, time = 0))  
                    time_acc = 0
                newtrack.append(msg)
            else:
                newtrack.append(msg)
            continue
        if((m == 0) and (msg.type == 'note_on')):
            note_list.append((msg.note, msg.time))
            on_time = msg.time
            continue   
        if((msg.type == 'note_on' and msg.time > split_time) or (msg.type == 'note_on' and time_acc > max_sustain_time)):
            if(len(note_list) != 0):
                if(len(last_chord)==0):
                    fake = [v[0] for v in note_list][0:5]
                    if len(fake) < 5:
                        fake.extend([np.median(note_list)] * (5-len(fake)))
                    chord = many_notes_harmonize(note_list, OCTAVE, fake)
                else:
                    chord = many_notes_harmonize(note_list, OCTAVE, last_chord)
                last_chord = chord
                for i, note in enumerate(chord):
                    if(i==0):
                        newtrack.append(Message('note_on', note = note, velocity = msg.velocity, time = on_time))  # append orgin to new
                    else:
                        newtrack.append(Message('note_on', note = note, velocity = msg.velocity, time = 0))  # append orgin to new
                    
                for i, note in enumerate(chord): 
                    if(i==0):   
                        newtrack.append(Message('note_off', note = note, velocity = msg.velocity, time = time_acc))  # append orgin to new
                    else:
                        newtrack.append(Message('note_off', note = note, velocity = msg.velocity, time = 0))  # append orgin to new
                note_list = []
                time_acc = 0
            on_time = msg.time
        else:
            if(msg.type == 'note_off'):
                note_list.append((msg.note, msg.time))
            # also add note_on but not excess limit
            time_acc += msg.time
        # print(note_list)
        

newmid.save(harmony_midi_name)