import multiprocessing
import threading
import pygame
import pygame._sdl2.audio as sdl2_audio
import time
from parallel import Parallel

from typing import Tuple, Optional

from closedloop_lsl.utils import high_precision_sleep


class Stimulator:
    
    
    def __init__(self, stim_file: str, alarm_file: str, trig_codes: dict):
        # Set sounds file
        self.stim_file = stim_file
        self.alarm_file = alarm_file
        # Set triggers codes
        self.trig_codes = trig_codes
        # Set audio devices
        self.devices = None
        self.inuse_device = None
        # Set parallel port
        self.paraport = None
        
        self.is_active = False
        self.process = None
        self.queue = None
        
    
    def get_devices(self, capture_devices: bool = False) -> Tuple[str, ...]:
        init_by_me = not pygame.mixer.get_init()
        if init_by_me:
            pygame.mixer.init()
        devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
        if init_by_me:
            pygame.mixer.quit()
            
        return devices
    
    
    def set_devise(self, headphones: str, speakers: str):
        self.devices = {
            'headphones': headphones,
            'speakers': speakers
        }
        print("Devices set: ", self.devices)
        
        return
    
    
    def _init_mixer(self, device: str = None):
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
        pygame.mixer.init(devicename=self.inuse_device)
        print("Mixer initialized with device: ", self.inuse_device)
        
        return
    
    
    def _stop_mixer(self):
        if pygame.mixer.get_init is not None:
            pygame.mixer.quit()
            print("Mixer stopped")
        return 
    
    
    def _play_audio(self, audio_file: str, volume: Optional[float] = 1.0):
        if self.mixer is not None:
            sound = pygame.mixer.Sound(audio_file)
            sound.set_volume(volume)
            sound.play()
        else:
            print("Mixer not initialized!")
        
        return
    
    
    def _init_parallel_port(self):
        try:
            self.paraport = Parallel()
            print("Parallel port opened")
        except Exception as e:
            self.paraport = None
            print("Error opening parallel port")
            
        return
    
    
    def _send_trigger(self, code: int):
        
        def _set_trigger(code):
            self.paraport.setData(code)
            high_precision_sleep(0.005)
            self.paraport.setData(0)
            return
        
        threading.Thread(target=_set_trigger, args=(code,)).start() #### Check how much time does it takes to execute this line
        return
    
    
    def prepare_stimulation(self, device: Optional[str] = None):
        self._init_mixer(device)
        self._init_parallel_port()
        
        return


    def start(self):
        pygame.init()
        self._init_parallel_port()
        self._init_mixer('headphones')
        
        screen = pygame.display.set_mode((400, 300))
        
        self.is_active = True
        
        self.queue = multiprocessing.Queue()
        
        self.process = multiprocessing.Process(target=self.stimulation_pipeline)
        self.process.start()
        
        print(f"Stimulator ready to stimulate!")
        
        return


    def stop(self):
        self.send_stim(None)
        self.process.terminate()
        self.process.join()
        self.process.close()
        
        self.is_active = False
        
        pygame.quit()
        
        return
        
    
    def send_stim(self, detection):
        self.queue.put(detection)
        return
        
    
    def stimulation_pipeline(self):
        
        def _stimulate(detection):
            # To save usefull milliseconds, subtract the execution time to the
            # time the stimulus should be played
            start_sitm_time = time.time()
            if detection[3] == 0:
                self._play_audio(self.stim_file, volume=1.0)
                self._send_trigger(self.trig_codes[detection[0]])
                return
            else:
                for _ in range(3):
                    self._play_audio(self.stim_file, volume=1.0)
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
                # for i in range(self.num_listeners):
                    # data = self.queues[i].get(block=True)  # Wait for data
                    # print(data)
                if detection is None:  # Sentinel value to terminate
                    print(f"Stimulator shutting down.")
                    # break
                    return
                # print(f"Listener {proc_num} got data.")
                
                pygame.display.set_caption('Close this window to stop the stimulation')
                
                running_stim = True
                play_alarm = False
                stimulation_starts = time.time()
                threading.Thread(target=_stimulate, args=(detection,)).start() #### Check how much time does it takes to execute this line
                while running_stim:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            running_stim = False
                            break
                        if time.time() - stimulation_starts > 5:
                            running_stim = False
                            pygame.display.quit()
                            play_alarm = True
                            break
                if play_alarm:
                    self._init_mixer('speakers')
                    self._play_audio(self.alarm_file, volume=1.0)
                    while pygame.mixer.get_busy():
                        pass
                    # questionnaire()
                    self._init_mixer('headphones')
                
            except Exception as e:
                print(f"Error: {e}")
        

if __name__ == '__main__':
    def get_devices(capture_devices: bool = False) -> Tuple[str, ...]:
        init_by_me = not pygame.mixer.get_init()
        if init_by_me:
            pygame.mixer.init()
        devices = tuple(sdl2_audio.get_audio_device_names(capture_devices))
        if init_by_me:
            pygame.mixer.quit()
        return devices
    
    print(get_devices(False))