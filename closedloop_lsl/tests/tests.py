from closedloop_lsl.core.stimulation import Stimulator
from closedloop_lsl.utils.utils import high_precision_sleep, envelope, gfp
import time
import pygame

stim_sound = '/home/jerry/python_projects/space/closedloop_lsl/data/sounds/beep.wav'
alarm_sound = '/home/jerry/python_projects/space/closedloop_lsl/data/sounds/alarm.wav'
trig_codes = {'cingulate-lh': 20, 'cingulate-rh': 22,
            'occipital-lh': 30, 'occipital-rh': 32}
stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                        trig_codes=trig_codes)
sound_dev = stimulator.get_devices()
print(sound_dev)
stimulator.set_devices(speakers=sound_dev[0], headphones=sound_dev[0])
stimulator.start()

high_precision_sleep(5)
print('waited 5 seconds')

start_single_stim = time.time()
stimulus = ['cingulate-rh', True, 0.746268656716418, 0, 0.9239749460737329]
stimulator.send_stim(stimulus)
end_single_stim = time.time()
# time.sleep(2)
# stimulator.stop_stimulation()
print('Single stim time:', end_single_stim - start_single_stim)

high_precision_sleep(10)
print('waited 10 seconds')

start_triple_stim = time.time()
stimulus = ['cingulate-lh', True, 0.746268656716418, 1., 0.9239749460737329]
stimulator.send_stim(stimulus)
end_triple_stim = time.time()
# time.sleep(2)
# stimulator.stop_stimulation()
print('Triple stim time:', end_triple_stim - start_triple_stim)

high_precision_sleep(10)

stimulator.stop()

# import os
# import inspect
# import closedloop_lsl
# print(inspect.getfile(closedloop_lsl))
# print(closedloop_lsl.__file__)
# print(os.getcwd())
