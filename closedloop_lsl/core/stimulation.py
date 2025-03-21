import multiprocessing
import threading
import pygame
import pygame._sdl2.audio as sdl2_audio
import time
# from parallel import Parallel
from psychopy import parallel

from typing import Tuple, Optional

from closedloop_lsl.utils.utils import high_precision_sleep


class Stimulator:
    
    
    def __init__(self, stim_file: str, alarm_file: str, trig_codes: dict):
        # Set sounds file
        self.stim_file = stim_file
        self.alarm_file = alarm_file
        # Set triggers codes
        self.trig_codes = trig_codes
        self.alarm_trig = 38
        # Set audio devices
        self.devices = None
        self.inuse_device = None
        # Set parallel port
        self.paraport = None
        
        self.stim_stopped_by_user = False
        
        self.is_active = False
        self.is_stimulating = False
        self.process = None
        self.queue = None
        
        print('Reading sound files...')
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=64)
        self.stim_sound = pygame.mixer.Sound(self.stim_file)
        self.alarm_sound = pygame.mixer.Sound(self.alarm_file)
        pygame.mixer.quit()
        
    
    def get_devices(self, capture_devices: bool = False) -> Tuple[str, ...]:
        init_by_me = not pygame.mixer.get_init()
        if init_by_me:
            pygame.mixer.init()
        devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
        if init_by_me:
            pygame.mixer.quit()
            
        return devices
    
    
    def set_devices(self, headphones: str, speakers: str):
        self.devices = {
            'headphones': headphones,
            'speakers': speakers
        }
        print("Devices set: ", self.devices)
        
        return
    
    
    def _init_mixer(self, device: str = None, verbose: bool = False):
        pygame.mixer.quit()
        
        # if device is None:
        #     devices = get_devices()
        #     if not devices:
        #         raise RuntimeError("No device!")
        #     device = devices[0]
            
        # self.inuse_device = device
        # print(f"Loaded: {self.stim_file}\r\nDevice: {device}")
        if self.devices is None:
            raise RuntimeError("No devices set!")
        
        self.inuse_device = self.devices[device]
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=64, 
                          devicename=self.inuse_device)
        if verbose:
            print("Mixer initialized with device: ", self.inuse_device)
        
        return
    
    
    def _stop_mixer(self):
        if pygame.mixer.get_init is not None:
            pygame.mixer.quit()
            print("Mixer stopped")
        return 
    
    
    # def _play_audio(self, audio_file: str, volume: Optional[float] = 1.0):
    #     if pygame.mixer.get_init is not None:
    #         sound = pygame.mixer.Sound(audio_file)
    #         # sound.set_volume(volume)
    #         sound.play()
    #     else:
    #         print("Mixer not initialized!")
        
    #     return
    
    
    def _play_audio(self, sound: pygame.mixer.Sound, volume: Optional[float] = 1.0):
        if pygame.mixer.get_init is not None:
            sound = pygame.mixer.Sound(sound)
            sound.set_volume(volume)
            sound.play()
        else:
            print("Mixer not initialized!")
        
        return
    
    
    def _init_parallel_port(self):
        if self.paraport is None:
            try:
                # self.paraport = Parallel(port=0)
                # self.paraport.setData(0)
                self.paraport = parallel.ParallelPort(address=0)
                self.paraport.setData(0)
                high_precision_sleep(0.005)
                print("Parallel port opened")
            except Exception as e:
                self.paraport = None
                print("Error opening parallel port")
            
        return
    
    
    def _close_parallel_port(self):
        if self.paraport is not None:
            try:
                self.paraport.setData(0)
                del self.paraport
                self.paraport = None
                print ('Parallel port closed')
            except Exception:
                print('Unable to close the parallel port')
    
    
    def _send_trigger(self, code: int):
        
        def _set_trigger(code):
            self.paraport.setData(code)
            high_precision_sleep(0.005)
            self.paraport.setData(0)
            high_precision_sleep(0.005)
            print(f"Trigger sent: {code}")
            return
        
        threading.Thread(target=_set_trigger, args=(code,)).start() #### Check how much time does it takes to execute this line
        return
    
    
    # def prepare_stimulator(self, device: Optional[str] = None):
    #     self._init_mixer(device)
    #     self._init_parallel_port()
        
    #     return


    def start(self):
        pygame.init()
        self._init_parallel_port()
        self._init_mixer('headphones', verbose=True)
        
        # screen = pygame.display.set_mode((400, 300))
        
        self.is_active = True
        
        self.queue = multiprocessing.Queue()
        
        # self.process = multiprocessing.Process(target=self.stimulation_pipeline)
        self.process = threading.Thread(target=self.stimulation_pipeline, daemon=True)
        self.process.start()
        
        print(f"Stimulator ready to stimulate!")
        
        return


    def stop(self):
        self.send_stim(None)
        self.process.join()
        self._stop_mixer()
        self._close_parallel_port()
        
        self.is_active = False
        
        pygame.quit()
        
        return
        
    
    def send_stim(self, detection):
        self.queue.put(detection)
        return
    
    
    def stop_stimulation(self):
        self.stim_stopped_by_user = True
        return
        
    
    def stimulation_pipeline(self):
        
        def _stimulate(detection):
            # To save usefull milliseconds, subtract the execution time to the
            # time the stimulus should be played
            start_sitm_time = time.time()
            if detection[3] == 0:
                if not self.stim_stopped_by_user:
                # threading.Thread(target=self._play_audio, args=(self.stim_file,), kwargs={'volume': .1}, daemon=True).start()
                    # self._play_audio(self.stim_file, volume=1.)
                    self._play_audio(self.stim_sound, volume=.15)
                    self._send_trigger(self.trig_codes[detection[0]])
                    return
            else:
                for _ in range(3):
                    if not self.stim_stopped_by_user:
                        # self._play_audio(self.stim_file, volume=1.)
                        self._play_audio(self.stim_sound, volume=1.)
                        self._send_trigger(self.trig_codes[detection[0]])
                        high_precision_sleep(detection[3] - 
                                            (time.time() - start_sitm_time))
                        if running_stim is False:
                            return
                        start_sitm_time = time.time()
                return
        
        while True:
            try:
                detection = self.queue.get(block=True)  # Wait for data
                self.is_stimulating = True
                self.stim_stopped_by_user = False
                # for i in range(self.num_listeners):
                    # data = self.queues[i].get(block=True)  # Wait for data
                    # print(data)
                if detection is None:  # Sentinel value to terminate
                    print(f"Stimulator shutting down.")
                    # break
                    return
                # print(f"Listener {proc_num} got data.")
                
                # pygame.display.set_caption('Close this window to stop the stimulation')
                print('Stimulation starts')
                threading.Thread(target=_stimulate, args=(detection,), daemon=True).start() #### Check how much time does it takes to execute this line
                stimulation_starts = time.perf_counter()
                running_stim = True
                # self.stim_stopped_by_user = False
                play_alarm = False
                while running_stim:
                    # for event in pygame.event.get():
                    #     if event.type == pygame.QUIT:
                    #         running_stim = False
                    #         break
                    if time.perf_counter() - stimulation_starts > 5.:
                        running_stim = False
                        # pygame.display.quit()
                        play_alarm = True
                        break
                    if self.stim_stopped_by_user:
                        running_stim = False
                        break
                    high_precision_sleep(0.001)
                print(f"Total stimulation time:", time.perf_counter() - stimulation_starts)
                a0 = time.perf_counter()
                if play_alarm:
                    self._init_mixer('speakers')
                    # self._play_audio(self.alarm_file, volume=1.0)
                    self._play_audio(self.alarm_sound, volume=1.0)
                    self._send_trigger(self.alarm_trig)
                    while pygame.mixer.get_busy():
                        pass
                    # questionnaire()
                    self._init_mixer('headphones')
                else:
                    self._send_trigger(0)
                print('Alarm time:', time.perf_counter() - a0)
                self.is_stimulating = False
                
            except Exception as e:
                print(f"Error: {e}")
        

if __name__ == '__main__':
    import os
    import os.path as op
    from closedloop_lsl.config.config import read_config
    
    os.environ['SDL_AUDIODRIVER'] = 'alsa'
    
    cfg = read_config()
    stim_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'PN_44100Hz_50ms.wav')
    alarm_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'alarm.wav')
    trig_codes = {'cingulate-lh': 20, 'cingulate-rh': 22,
                'occipital-lh': 30, 'occipital-rh': 32}
    stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                            trig_codes=trig_codes)
    sound_dev = stimulator.get_devices()
    print(sound_dev)
    stimulator.set_devices(speakers=sound_dev[4], headphones=sound_dev[7])
    # stimulator.set_devices(speakers=sound_dev[1], headphones=sound_dev[-1])
    stimulator.start()
    
    high_precision_sleep(5)
    print('waited 5 seconds')
    
    for i in range(100):
        start_single_stim = time.time()
        stimulus = ['cingulate-rh', True, 0.746268656716418, 0, 0.9239749460737329]
        stimulator.send_stim(stimulus)
        end_single_stim = time.time()
        high_precision_sleep(0.25)
        stimulator.stop_stimulation()
        print('Single stim time:', end_single_stim - start_single_stim)
        high_precision_sleep(.25)
    stimulator.send_stim(stimulus)
    
    # high_precision_sleep(10)
    # print('waited 10 seconds')
    
    # start_triple_stim = time.time()
    # stimulus = ['cingulate-lh', True, 0.746268656716418, 1., 0.9239749460737329]
    # stimulator.send_stim(stimulus)
    # end_triple_stim = time.time()
    # print('Triple stim time:', end_triple_stim - start_triple_stim)
    
    high_precision_sleep(6)
    
    stimulator.stop()