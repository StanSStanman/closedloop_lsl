# from remedy.utils.common_functions import check_os
# if check_os() in ['Linux']:
#     import ctypes
#     xlib = ctypes.cdll.LoadLibrary("libX11.so")
#     xlib.XInitThreads()
from psychopy import gui
import os
import os.path as op
from datetime import datetime
import numpy as np
import json
import sounddevice as sd
import scipy.io.wavfile as sw
# from remedy.config.config import read_config
from closedloop_lsl.config.config import read_config
from closedloop_lsl.report.questlist import questlist
# from remedy.utils.audio_recorder import save_recording_audio


cfg = read_config()


def colored_print(color, text):
    colors = {
        'cyan': '\033[96m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def conv2sec(hours, minutes, seconds):
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

def dreamquestrc(subject_id, session, sex, fs=44100):
    
    while True:
        dlg = gui.Dlg(title='Start questionnaire', labelButtonOK='Start', labelButtonCancel='Quit')
        dlg.addText('Select the audio devices and start the questionnaire.',)
        dlg.addField('Speaker:', choices=[dev['name'] for dev in sd.query_devices()], 
                     initial=cfg['DEVICES']['PlayRecDev'])
        dlg.addField('Microphone:', choices=[dev['name'] for dev in sd.query_devices()], 
                     initial=cfg['DEVICES']['PlayRecDev'])
        params = dlg.show()
        
        if dlg.OK:
            spk, mic = params.values()
            print("Starting the questionnaire.")
            break
        else:
            dlg = gui.Dlg(title='Are you sure?', labelButtonOK='Yes', labelButtonCancel='No')
            dlg.addText('Do you REALLY want to interrupt the questionnaire?')
            dlg.show()
            
            if dlg.OK:
                print("Questionnaire interrupted by the user.")
                return
            else:
                print("Starting the questionnaire.")
    
    if not spk or not mic:
        print("Error: No audio devices selected.")
        return
    
    spk_idx = [dev['name'] for dev in sd.query_devices()].index(spk)
    mic_idx = [dev['name'] for dev in sd.query_devices()].index(mic)
    
    sd.default.device = [mic_idx, spk_idx]
    # sd.default.samplerate = fs
    n_input_ch = sd.query_devices(mic_idx)['max_input_channels']
    max_answ_len = 60 * 15 # 15 minutes of recording
    
    questions_path = op.join(cfg['DEFAULT']['SoundsPath'], 'questions')
    output_path = op.join(cfg['PATHS']['ResultsPath'], subject_id, session)
    if not op.exists(output_path):
        os.makedirs(output_path)
    
    files = ['qst01', 'qst02_1', 'qst02_2', 'qst02_3', 'qst03', 'qst04', 
             'qst05', 'qst05_1', 'qst06', 'qst07', 'qst08', 'qst09', 'qst10', 
             'qst10_1', 'qst10_2', 'qst10_3', 'qst10_4', 'qst10_5',
             'qst11', 'qst12', 'qst13', 'qst14', 'qst15']
    cmp = {'Female': ['', '', '', '', 'f', 'f', '', '', '', '', '', '', '', 
                      '', '', '', '', '', '', '', '', '', 'f'],
           'Male': ['', '', '', '', 'm', 'm', '', '', '', '', '', '', '', '', 
                    '', '', '', '', '', '', '', '', 'm']}

    questions = {file: os.path.join(questions_path, f"{file}{cmp[sex][nx]}.wav") 
                 for nx, file in enumerate(files)}

    responses = {}
    
    # Configure audio recording
    duration = 3600  # Record for one hour (you can modify this value)
    recorded_data = []

    print("Starting the questionnaire")
    print(f"Participant: {subject_id}, Session: {session}, Sex: {sex}")
    print(f"Output directory: {output_path}")
    # print('Press \'q\' at any time to interrupt the questionnaire ',
    #       'and save the data.')
    
    question_count = 0
    answers = []
    try:
        for qn in range(1, 16):
            sq = f"{qn:02d}"
            colored_print('cyan', f'*** Question {sq} ***')

            # Play the question audio
            if f'qst{sq}' in questions:
                if qn != 1:
                    answers.append(answ[~np.isnan(answ)[:, 0]])
                sf, question = sw.read(questions[f'qst{sq}'])
                qst = np.full((question.shape[0], n_input_ch), np.nan)
                sd.playrec(question, samplerate=sf, channels=1, 
                           dtype='int16', out=qst, 
                           input_mapping=np.array(range(1, n_input_ch + 1)),
                           output_mapping=np.array([1, 2]))
                answ = np.full((max_answ_len * sf, n_input_ch), np.nan)
                sd.wait()
                answers.append(qst)
                sd.rec(samplerate=sf, channels=n_input_ch, out=answ,
                       mapping=np.array(range(1, n_input_ch+1)), dtype='int16')

            # Check if the user wants to interrupt
            # keys = kb.getKeys(['q'])
            # if 'q' in keys:
            #     print("Interruption requested by the user.")
            #     break
            # if event.getKeys(['q']):
            #     print("Interruption requested by the user.")
            #     break
            
            # GUI for question 1
            if qn == 1:
                dlg = gui.Dlg(title=f"Question {sq}")
                dlg.addText(questlist(qn))
                dlg.addField('Answer:', choices=['ER', 'EWR', 'NE'])
                result = dlg.show()
                
                if result[0] == 'ER':
                    responses['qst01'] = 2
                    audio_key = 'qst02_1'
                elif result[0] == 'EWR':
                    responses['qst01'] = 1
                    audio_key = 'qst02_2'
                else:  # NE
                    responses['qst01'] = 0
                    audio_key = 'qst02_3'
                
                # Debug: verifica il valore di responses['qst01']
                print(f"Answer to question 1: {responses['qst01']}")

                # Play the corresponding audio
                if audio_key in questions:
                    answers.append(answ[~np.isnan(answ)[:, 0]])
                    print(f"Playing audio: {audio_key}")
                    sf, question = sw.read(questions[audio_key])
                    qst = np.full((question.shape[0], n_input_ch), np.nan)
                    sd.playrec(question, samplerate=sf, channels=1, 
                               dtype='int16', out=qst, 
                               input_mapping=np.array(range(1, n_input_ch+1)),
                               output_mapping=np.array([1, 2]))
                    answ = np.full((max_answ_len * sf, n_input_ch), np.nan)
                    sd.wait()
                    answers.append(qst)
                    answ = sd.rec(samplerate=sf, channels=n_input_ch, out=answ, 
                                  mapping=np.array(range(1, n_input_ch+1)),
                                  dtype='int16')
                else:
                    print(f"Audio {audio_key} non trovato")
                
                # Handle the answer to question 2 based on the answer to question 1
                if result[0] == 'ER':
                    dlg = gui.Dlg(title="Duration")
                    dlg.addField('Hours:', initial='0')
                    dlg.addField('Minutes:', initial='0')
                    dlg.addField('Seconds:', initial='0')
                    duration = dlg.show()
                    # Convert the values to integers, using 0 if the field is empty
                    hours = int(duration[0]) if duration[0] else 0
                    minutes = int(duration[1]) if duration[1] else 0
                    seconds = int(duration[2]) if duration[2] else 0
                    responses['qst02'] = conv2sec(hours, minutes, seconds)
                elif result[0] == 'EWR':
                    dlg = gui.Dlg(title=f"Question {sq}")
                    dlg.addText(questlist(2_2))
                    dlg.addField('Answer:', choices=['Yes', 'No'])
                    responses['qst02'] = 1 if dlg.show()[0] == 'Yes' else 0
                elif result[0] == 'NE':
                    dlg = gui.Dlg(title=f"Question {sq}")
                    dlg.addText(questlist(2_3))
                    dlg.addField('Answer:', choices=['Yes', 'No'])
                    responses['qst02'] = 1 if dlg.show()[0] == 'Yes' else 0
                
                # Add some print for debugging
                print(f"Answer to question 1: {responses['qst01']}")
                print(f"Answer to question 2: {responses['qst02']}")

            # Verify the interruption condition after question 5
            
            if qn in [3, 4, 6, 7, 8, 9, 11, 12, 13, 14, 15]:
                dlg = gui.Dlg(title=f"Question {sq}")
                dlg.addText(questlist(qn))
                dlg.addField('Answer:', choices=['1', '2', '3', '4', '5'])
                responses[f'qst{sq}'] = int(dlg.show()[0])
            elif qn == 5:
                dlg = gui.Dlg(title=f"Question {sq}")
                dlg.addText(questlist(qn))
                dlg.addField('Answer:', choices=['Yes', 'No'])
                responses['qst05'] = 1 if dlg.show()[0] == 'Yes' else 0
                if responses.get('qst01') != 2:
                    print("Questionnaire interrupted after question 5.")
                    break
                elif responses['qst05'] == 1:
                    dlg = gui.Dlg(title="Type of stimulus")
                    dlg.addField('Description:')
                    responses['qst05_desc'] = dlg.show()[0]
            elif qn == 10:
                responses['qst10'] = np.full((1, 5), np.nan)
                sensi = ['Visual', 'Auditory', 'Tactile', 'Olfactory', 'Gustatory']
                for ns, senso in enumerate(sensi, start=1):
                    answers.append(answ[~np.isnan(answ)[:, 0]])
                    print(f"Playing audio: {audio_key}")
                    sf, question = sw.read(questions[f'qst10_{ns}'])
                    qst = np.full((question.shape[0], n_input_ch), np.nan)
                    sd.playrec(question, samplerate=sf, channels=1, 
                               dtype='int16', out=qst, 
                               input_mapping=np.array(range(1, n_input_ch+1)),
                               output_mapping=np.array([1, 2]))
                    answ = np.full((max_answ_len * sf, n_input_ch), np.nan)
                    sd.wait()
                    answers.append(qst)
                    answ = sd.rec(samplerate=sf, channels=n_input_ch, out=answ, 
                                  mapping=np.array(range(1, n_input_ch+1)),
                                  dtype='int16')
                    
                    dlg = gui.Dlg(title=f"Question 10.{ns}: {senso}")
                    dlg.addText(f"Have you had an experience {senso.lower()}?")
                    dlg.addField('Answer:', choices=['Yes', 'No'])
                    responses['qst10'][0, ns - 1] = 1 if dlg.show()[0] == 'Yes' else 0
                    
            question_count += 1
            print(f"Question {sq} completed")
            print(f"Answer saved: {responses.get(f'qst{sq}', 'Not available')}")

        answers.append(answ[~np.isnan(answ)[:, 0]])
        sd.stop()
        print(f"Total questions presented: {question_count}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Stop the recording
        recorded_data = np.vstack(answers)
        
        # Save the recording audio
        
        cdate = datetime.now().strftime("%d%m%Y")
        ctime = datetime.now().strftime("%H%M%S")
        if recorded_data.shape[0] > 0:
            try:
                # audio_file = save_recording_audio(recorded_data, outpath, 
                #                                   subject_id, session, 
                #                                   cdate, ctime, fs)
                audio_file = os.path.join(output_path, f"{subject_id}_{session}_{cdate}_{ctime}.wav")
                sw.write(audio_file, sf, recorded_data)
                
                if audio_file and os.path.exists(audio_file):
                    print(f"Audio file created: {audio_file}")
                else:
                    print(f"Error: Audio file NOT created or NOT found. Expected path: {audio_file}")
            except Exception as e:
                print(f"Error during audio saving: {e}")
        else:
            print("No data recorded.")

    data_to_save = {
        "cdate": cdate,
        "ctime": ctime,
        "participant_id": subject_id,
        "session": session,
        "sex": sex,
        "responses": {k: v.tolist() if isinstance(v, np.ndarray) else v for k, v in responses.items()}
    }
    foutname = os.path.join(output_path, f"{subject_id}_{session}_{cdate}_{ctime}.json")
    with open(foutname, 'w') as json_file:
        json.dump(data_to_save, json_file, indent=4)

    if os.path.exists(foutname):
        print(f"JSON file created: {foutname}")
    else:
        print("Error: JSON file NOT created")
    
    return

if __name__ == "__main__":
    dreamquestrc('Mario', 'N1', 'Male')