import sounddevice as sd
# import pygame
# import pygame._sdl2.audio as sdl2_audio
import scipy.io.wavfile as wav
import numpy as np


# pygame.mixer.init()
# devices = tuple(sdl2_audio.get_audio_device_names(False))
# print(devices)
# print(pygame.mixer.get_init())
# pygame.mixer.stop()
# pygame.mixer.quit()

# pygame.mixer.init(devicename=devices[1])

sd_dev = sd.query_devices()
sd.default.device = [5, 5]
sd.default.samplerate = 44100
sd.default.channels = 1
print(sd_dev)

# load a wav file
fs, data = wav.read('/home/jerry/python_projects/space/closedloop_lsl/data/sounds/questions/qst01.wav')

# Create a buffer for recorded data with the same length as the input data
recorded_data = np.empty_like(data, dtype='int16')
recorded_data = np.empty((len(data), 2), dtype='int16')

# Record and play the audio
sd.playrec(data, samplerate=fs, channels=[1, 1], blocking=True, dtype='int16', out=recorded_data)
sd.wait()

# Save the recorded audio to a file
wav.write('/home/jerry/python_projects/space/closedloop_lsl/data/sounds/recorded_audio.wav', fs, recorded_data)

# Play back the recorded audio
sd.play(recorded_data, samplerate=fs, blocking=True)