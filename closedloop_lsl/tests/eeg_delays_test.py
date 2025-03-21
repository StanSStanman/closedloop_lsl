import os
import os.path as op
import time
import numpy as np

from closedloop_lsl.config.config import read_config
from closedloop_lsl.utils.utils import high_precision_sleep
from closedloop_lsl.core.manager_lsl import ClosedLoopLSL
from closedloop_lsl.core.stimulation import Stimulator


def trig_detect(data, triggers, stimulations):
    _data = data.sel({'times': data.times.values[-66:], 
                      'channels': ['TRIG1', 'TRIG2']})
    for _ch in _data.channels:
        channel_data = _data.sel({'channels': _ch}).values
        if triggers['sender_1'] in channel_data:
            print('sender_1 found in', _ch.values)
            snd = 'sender_1'
        elif triggers['sender_2'] in channel_data:
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
    
    # Initialize configuration
    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    cfg = read_config()
    
    # Build fake stimulations:
    stimulations = {'sender_1': ['sender_1', 0, 0, 0],
                    'sender_2': ['sender_2', 0, 0, 0],
                    'receiver_1': ['receiver_1', 0, 0, 0],
                    'receiver_2': ['receiver_2', 0, 0, 0]}
    
    # Initialize EEG stream
    streams_name = 'EE225-000000-000625'
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
    
    task = ClosedLoopLSL(sfreq=500., ch_names=eeg_channels,)
    task.search_stream(sname=streams_name, stype=streams_type)
    task.open_stream(bufsize=5.)
    task.connect_stream()
    # Add channels' names here
    task.apply_filter(low_freq=.5, high_freq=4.)
    task.set_reference_channels(['3LD', '3RD']) # Reference channels' names
    task.start_acquisition(interval=0.001)
    
    # Initialize stimulator
    stim_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'PN_44100Hz_50ms.wav')
    alarm_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'alarm.wav')
    speakers = cfg['DEVICES']['Speakers']
    headphones = cfg['DEVICES']['Headphones']
    trig_codes = {'sender_1': 22, 'receiver_1': 24,
                  'sender_2': 32, 'receiver_2': 34}
    stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                            trig_codes=trig_codes)
    stimulator.set_devices(speakers=speakers, headphones=headphones)
    stimulator.start()
    
    # Start testing
    high_precision_sleep(1.)
    print('Start testing...')
    t0 = time.perf_counter()
    t1 = t0 + (60. * 5.) # 5 minutes
    while time.perf_counter() < t1:
        acquisition_time_start = time.perf_counter()

        data = task.get_data()
        detection = trig_detect(data, trig_codes, stimulations)
        if detection is not None:
            print('Detected:', detection)
            stimulator.send_stim(detection)
            
        acquisition_time_end = time.perf_counter()
        print('Acquisition time:', acquisition_time_end - acquisition_time_start)
       
    stimulator.stop()
    task.stop_acquisition()
    task.disconnect_streams()