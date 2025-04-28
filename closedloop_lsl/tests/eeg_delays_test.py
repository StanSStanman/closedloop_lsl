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
        if  21 < channel_data.max() < 23:
            print('sender_1 found in', _ch.values)
            snd = 'sender_1'
        # elif triggers['sender_2'] in channel_data:
        elif 31 < channel_data.max() < 33:
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
    # streams_name = 'EE225-000000-000625'
    streams_name = 'EE225-020034-000625_on_MININT-A894NL4'
    streams_type = 'EEG'
    
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
    #                 '4LB', '4RB', 'BIP1', 'BIP2', 'BIP3',
    #                 'TRIG1', 'TRIG2']
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
    #                 '4LB', '4RB', 'BIP1', 'BIP2', 'BIP3', 'TRIG1']
    eeg_channels = ['Z1L', 'Z2L', 'Z3L', 'Z4L', 'Z5L', 'Z6L', 'Z7L', 'Z8L', 
                    'Z9L', 'Z10L', 'Z11L', 'Z12L', 'Z13L', 'Z14L', 'Z15L', 
                    'Z16L', 'Z17L', 'Z18L', 'Z19L', 'L1Z', 'L2Z', 'L3Z', 
                    'L4Z', 'L5Z', 'L6Z', 'L7Z', 'L8Z', 'L9Z', 'L10Z', 'L11Z', 
                    'L12Z', 'L13Z', 'L14Z', 'L15Z', 'L16Z', 'L17Z', 'L18Z', 
                    'L19Z', 'L20Z', 'L1L', 'L2L', 'L3L', 'L4L', 'L5L', 'L6L', 
                    'L7L', 'L8L', 'L9L', 'L10L', 'L11L', 'L12L', 'L13L', 
                    'L14L', 'L15L', 'L16L', 'L17L', 'L18L', 'L19L', 'L1A', 
                    'L2A', 'L3A', 'L4A', 'L5A', 'L6A', 'L1B', 'L2B', 'L3B', 
                    'L4B', 'L5B', 'L6B', 'L7B', 'L1C', 'L2C', 'L3C', 'L4C', 
                    'L5C', 'L6C', 'L7C', 'L8C', 'L1D', 'L2D', 'L3D', 'L4D', 
                    'L5D', 'L6D', 'L7D', 'L8D', 'L9D', 'L1E', 'L2E', 'L3E', 
                    'L4E', 'L5E', 'L6E', 'L7E', 'L8E', 'L9E', 'L10E', 'L1F', 
                    'L2F', 'L3F', 'L4F', 'L5F', 'L6F', 'L7F', 'L8F', 'L1G', 
                    'L2G', 'L3G', 'L4G', 'L5G', 'L6G', 'L7G', 'L1H', 'L2H', 
                    'L3H', 'L4H', 'L5H', 'Z1Z', 'Z2Z', 'Z3Z', 'Z4Z', 'Z5Z', 
                    'Z6Z', 'Z7Z', 'Z8Z', 'Z9Z', 'Z10Z', 'Z1R', 'Z2R', 'Z3R', 
                    'Z4R', 'Z5R', 'Z6R', 'Z7R', 'Z8R', 'Z9R', 'Z10R', 'Z11R', 
                    'Z12R', 'Z13R', 'Z14R', 'Z15R', 'Z16R', 'Z17R', 'Z18R', 
                    'Z19R', 'R1Z', 'R2Z', 'R3Z', 'R4Z', 'R5Z', 'R6Z', 'R7Z', 
                    'R8Z', 'R9Z', 'R10Z', 'R11Z', 'R12Z', 'R13Z', 'R14Z', 
                    'R15Z', 'R16Z', 'R17Z', 'R18Z', 'R19Z', 'R20Z', 'R1R', 
                    'R2R', 'R3R', 'R4R', 'R5R', 'R6R', 'R7R', 'R8R', 'R9R', 
                    'R10R', 'R11R', 'R12R', 'R13R', 'R14R', 'R15R', 'R16R', 
                    'R17R', 'R18R', 'R19R', 'R1A', 'R2A', 'R3A', 'R4A', 'R5A', 
                    'R6A', 'R1B', 'R2B', 'R3B', 'R4B', 'R5B', 'R6B', 'R7B', 
                    'R1C', 'R2C', 'R3C', 'R4C', 'R5C', 'R6C', 'R7C', 'R8C', 
                    'R1D', 'R2D', 'R3D', 'R4D', 'R5D', 'R6D', 'R7D', 'R8D', 
                    'R9D', 'R1E', 'R2E', 'R3E', 'R4E', 'R5E', 'R6E', 'R7E', 
                    'R8E', 'R9E', 'R10E', 'R1F', 'R2F', 'R3F', 'R4F', 'R5F', 
                    'R6F', 'R7F', 'R8F', 'R1G', 'R2G', 'R3G', 'R4G', 'R5G', 
                    'R6G', 'R7G', 'R1H', 'R2H', 'R3H', 'R4H', 'R5H', 'Z11Z', 
                    'VEOGR', 'Z13Z', 'Z14Z', 'Z15Z', 'Z16Z', 'Z17Z', 'Z18Z', 
                    'Z19Z', 'Z20Z', 'BIP1', 'BIP2', 'BIP3', 'TRIG1']
    
    task = ClosedLoopLSL(sfreq=500., ch_names=eeg_channels)
    task.search_stream(sname=streams_name, stype=streams_type)
    task.open_stream(bufsize=7.)
    task.connect_stream()
    # Add channels' names here
    # task.apply_filter(low_freq=.5, high_freq=4.,
    #                   filter_length='auto',
    #                   picks=slice(0, 64),
    #                   method='fir',
    #                   iir_params=None,
    #                   pad='reflect')
    task.apply_filter(low_freq=.5, high_freq=4.,
                      filter_length='auto',
                      picks=slice(0, 256),
                      method='fir',
                      iir_params=None,
                      pad='reflect')
    # task.set_reference_channels(['3LD', '3RD']) # Reference channels' names
    task.start_acquisition(interval=0.001)
    
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
    high_precision_sleep(7.)
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