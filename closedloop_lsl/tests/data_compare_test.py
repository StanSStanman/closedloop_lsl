import os
import os.path as op
import time
import numpy as np
import xarray as xr

from closedloop_lsl.core.manager_lsl import ClosedLoopLSL
from closedloop_lsl.core.stimulation import Stimulator
from closedloop_lsl.config.config import read_config
from closedloop_lsl.utils.utils import high_precision_sleep

if __name__ == '__main__':
    
    # Initialize configuration
    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    cfg = read_config()
    
    # Build fake stimulations:
    stimulations = {'start': ['start', 0, 0, 0],
                    'trigger': ['trigger', 0, 0, 0],
                    'stop': ['stop', 0, 0, 0]}
    
    stim_order = ['start', 'trigger', 'trigger', 'stop']
    stim_time = np.random.uniform(2.5, 3.5, len(stim_order))
    
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
    trig_codes = {'start': 20, 'trigger': 30, 'stop': 40}
    
    # Stimulator
    stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                            trig_codes=trig_codes)
    stimulator.set_devices(speakers=speakers, headphones=headphones)
    stimulator.start()
    
    # Start testing
    high_precision_sleep(5.)
    print('Start testing...')
    all_data = []
    t0 = time.perf_counter()
    t1 = t0 + 20. # 20 seconds
    stim_n = 0
    next_stim = t0 + stim_time[stim_n] # recording start time
    while time.perf_counter() < t1:
        # acquisition_time_start = time.perf_counter()
        
        now = time.perf_counter()
        if next_stim - now <= 0:
            stimulator.send_stim(stimulations[stim_order[stim_n]])
            stim_n += 1
            next_stim = now + stim_time[stim_n]
            high_precision_sleep(.005)
            stimulator.stop_stimulation()

        data = task.get_data()
        all_data.append(data)
            
        # acquisition_time_end = time.perf_counter()
        # print('Acquisition time:', acquisition_time_end - acquisition_time_start)
        
    # Save data
    xr.concat(all_data, dim='times').to_netcdf('test_data_1.nc')
       
    stimulator.stop()
    task.stop_acquisition()
    task.disconnect_streams()