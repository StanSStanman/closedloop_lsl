import os
import os.path as op
import time
import numpy as np

from closedloop_lsl.config.config import read_config
from closedloop_lsl.utils.utils import high_precision_sleep
from closedloop_lsl.core.manager_lsl import ClosedLoopLSL
from closedloop_lsl.core.stimulation import Stimulator


def trig_detect(data, triggers, stimulations):
    # _data = data.sel({'times': data.times.values[-66:], 
    #                   'channels': ['TRIG1', 'TRIG2']})
    _data = data.sel({'times': data.times.values[-750:], 'channels': ['TRIG1']})
    for _ch in _data.channels:
        channel_data = _data.sel({'channels': _ch}).values
        channel_data = np.round(channel_data, 2)
        # channel_data = np.round(channel_data).astype(int)
        # print(np.round(channel_data.max(), 2))
        # if triggers['sender_1'] in channel_data:
        if  0.24 < channel_data.max() < 0.26:
            print('sender_1 found in', _ch.values)
            snd = 'sender_1'
        # elif triggers['sender_2'] in channel_data:
        elif 0.36 < channel_data.max() < 0.38:
            print('sender_2 found in', _ch.values)
            snd = 'sender_2'
        else:
            snd = None
            
    if snd is not None:
        if snd == 'sender_1':
            return stimulations['receiver_1']
        elif snd == 'sender_2':
            return stimulations['receiver_2']
    else:
        return None
        

if __name__ == '__main__':
    
    # p = psutil.Process(os.getpid())
    # p.nice(-20)
    
    # Initialize configuration
    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    cfg = read_config()
    
    # Build fake stimulations:
    stimulations = {'sender_1': ['sender_1', 0, 0, 0],
                    'sender_2': ['sender_2', 0, 0, 0],
                    'receiver_1': ['receiver_1', 0, 0, 0],
                    'receiver_2': ['receiver_2', 0, 0, 0]}
    prev_stim = 'sender_2'
    stim_time = np.random.uniform(1.5, 2.)
    
    # Initialize EEG stream
    streams_name = 'EE225-000000-000625'
    # streams_name = 'EE225-020034-000625_on_MININT-A894NL4'
    streams_type = 'EEG'
    
    eeg_channels = ['0Z', '1Z', '2Z', '3Z', '4Z', '1L', '1R', 
                    '1LB', '1RB', '2L', '2R', '3L', '3R', 
                    '4L', '4R', '1LC', '1RC', '2LB', '2RB', 
                    '1LA', '1RA', '1LD', '1RD', '2LC', '2RC', 
                    '3LB', '3RB', '3LC', '3RC', '2LD', '2RD', 
                    '3RD', '3LD', '9Z', '8Z', '7Z', '6Z', 'EOG',
                    '10L', '10R', '9L', '9R', '8L', '8R', 
                    '7L', '7R', '6L', '6R', '5L', '5R', 
                    '4LD', '4RD', '5LC', '5RC', '5LB', '5RB', 
                    '3LA', '3RA', '2LA', '2RA', '4LC', '4RC', 
                    '4LB', '4RB', 'BIP1', 'BIP2', 'BIP3',
                    'TRIG1', 'TRIG2']
    # eeg_channels = ['0Z', '1Z', '2Z', '3Z', '4Z', '1L', '1R', 
    #                 '1LB', '1RB', '2L', '2R', '3L', '3R', 
    #                 '4L', '4R', '1LC', '1RC', '2LB', '2RB', 
    #                 '1LA', '1RA', '1LD', '1RD', '2LC', '2RC', 
    #                 '3LB', '3RB', '3LC', '3RC', '2LD', '2RD', 
    #                 '3RD', '3LD', '9Z', '8Z', '7Z', '6Z', 'EOG',
    #                 '10L', '10R', '9L', '9R', '8L', '8R', 
    #                 '7L', '7R', '6L', '6R', '5L', '5R', 
    #                 '4LD', '4RD', '5LC', '5RC', '5LB', '5RB', 
    #                 '3LA', '3RA', '2LA', '2RA', '4LC', '4RC', 
    #                 '4LB', '4RB', 'TRIG1']
    
    task = ClosedLoopLSL(sfreq=500., ch_names=eeg_channels,)
    task.search_stream(sname=streams_name, stype=streams_type)
    task.open_stream(bufsize=5.)
    task.connect_stream()
    # Add channels' names here
    task.apply_filter(low_freq=.5, high_freq=4.)
    # task.set_reference_channels(['3LD', '3RD']) # Reference channels' names
    task.start_acquisition(interval=0.005)
    
    # Initialize stimulator
    stim_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'PN_44100Hz_50ms.wav')
    alarm_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'alarm.wav')
    speakers = cfg['DEVICES']['Speakers']
    headphones = cfg['DEVICES']['Headphones']
    trig_codes = {'sender_1': 22, 'receiver_1': 24,
                  'sender_2': 32, 'receiver_2': 34}
    
    # Stimulator
    stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                            trig_codes=trig_codes)
    stimulator.set_devices(speakers=speakers, headphones=headphones)
    stimulator.start()
    
    # Start testing
    high_precision_sleep(1.)
    print('Start testing...')
    t0 = time.perf_counter()
    t1 = t0 + (60. * 10.) # 5 minutes
    next_stim = t0 + stim_time
    while time.perf_counter() < t1:
        acquisition_time_start = time.perf_counter()
        
        now = time.perf_counter()
        if next_stim - now <= 0:
            if prev_stim == 'sender_1':
                prev_stim = 'sender_2'
                stimulator.send_stim(stimulations[prev_stim])
            elif prev_stim == 'sender_2':
                prev_stim = 'sender_1'
                stimulator.send_stim(stimulations[prev_stim])
            stim_time = np.random.uniform(4.5, 6.5)
            next_stim = now + stim_time
            high_precision_sleep(.005)
            stimulator.stop_stimulation()

        data = task.get_data()
        detection = trig_detect(data, trig_codes, stimulations)
        if detection is not None:
            print('Detected:', detection)
            stimulator.send_stim(detection)
            high_precision_sleep(.015)
            stimulator.stop_stimulation()
            high_precision_sleep(2)
            
        acquisition_time_end = time.perf_counter()
        print('Acquisition time:', acquisition_time_end - acquisition_time_start)
       
    stimulator.stop()
    task.stop_acquisition()
    task.disconnect_streams()