import time
import numpy as np
import scipy.signal as ss
from psychopy import gui
import os
import shutil
import platform
import threading


def high_precision_sleep(duration: float) -> None:
    """High precision sleep function.

    duration : float
        Duration to sleep in seconds.
    """
    if duration <= 0:
        return
    start_time = time.perf_counter()
    while True:
        elapsed_time = time.perf_counter() - start_time
        remaining_time = duration - elapsed_time
        if remaining_time <= 0:
            break
        if remaining_time >= 0.0002:
            time.sleep(0.8 * remaining_time)


def envelope(data: np.ndarray, n_excl: int=1, n_kept: int=3, center: bool=True)-> np.ndarray:
    """
    Calculate the envelope of the data.
    
    Parameters
    ----------
    data : np.ndarray
        The data to calculate the envelope.
    n_excl : int
        Number of channels to exclude from the envelope calculation.
    n_kept : int
        Number of channels to keep for the envelope calculation.
        
    Returns
    -------
    envp : np.ndarray
        The envelope of the data.
    """
    dt = np.sort(data, axis=0, kind='quicksort')
    # data = np.sort(data, axis=0, kind='stable')
    envp = np.mean(dt[n_excl:n_excl+n_kept, :], axis=0, keepdims=True)
    
    # Center envelope around 0
    if center:
        # envp -= np.mean(data)
        envp -= np.mean(envp)
    
    return envp


def moving_envp(data: np.ndarray, n_excl: int=1, n_kept: int=3, 
                ntp: int=1000, center: bool=True, idx: list=[])-> np.ndarray:
    if len(idx) == 0:
        idx = np.argsort(np.min(data[:, -ntp:], axis=1))[n_excl:n_excl+n_kept]
    # # compute minima across channels
    # mins = np.min(data[:, -ntp:], axis=1)
    # # check which are the channels with the lowest minima
    # idx = np.argsort(mins)
    # # get the indices of the channels to keep
    # idx = idx[n_excl:n_excl+n_kept]
    # average the corresponding channels
    envp = np.mean(data[idx], axis=0, keepdims=True)
    
    if center:
        envp = ss.detrend(envp, axis=1)
        
    return envp, idx
        

def gfp(data):
    """
    Calculate the global field power of the data.
    
    Parameters
    ----------
    data : np.ndarray
        The data to calculate the global field power.
        
    Returns
    -------
    gfp : np.ndarray
        The global field power of the data.
    """
    return np.std(data, axis=0)


def get_participant_info():
    dlg = gui.Dlg(title='Welcome to Closed-Loop LSL')
    dlg.addField("Participant ID:", initial='CL0')
    dlg.addField("Session:", choices=['N1', 'N2', 'N3'])
    dlg.addField("Gender", choices=['Male', 'Female'])

    params = dlg.show()

    if dlg.OK:
        id, session, gnd = params.values()
        return id, session, gnd
    else:
        print("Action cancelled by user.")
        raise SystemExit
    
    
def iter_draw(objs):
    for obj in objs:
        obj.draw()


def install_font(font_path):
    system = platform.system()
    if system == 'Linux':
        font_dir = os.path.expanduser('~/.fonts/')
    elif system == 'Windows':
        font_dir = os.path.join(os.environ['WINDIR'], 'Fonts')
    elif system == 'Darwin':  # macOS
        font_dir = os.path.expanduser('~/Library/Fonts/')
    else:
        raise RuntimeError(f'Unsupported operating system: {system}')

    if not os.path.exists(font_dir):
        os.makedirs(font_dir)

    shutil.copy(font_path, font_dir)
    print(f'Font installed to {font_dir}')

    if system == 'Linux':
        os.system('fc-cache -fv')
    elif system == 'Windows':
        print('Please restart your computer to complete the font installation.')
    elif system == 'Darwin':
        print('Please restart your computer to complete the font installation.')
        
    return


def collect_data(data, streamer, results, timestamp, fname):
    
    def _collect_data(data, streamer, results, timestamp, fname):
        det_time = data.times[-1]
        data_next = streamer.get_data()
        data = data.combine_first(data_next)
        attributes = {'roi': results[0][0],
                      'detection_time': det_time,
                      'sw_freq': results[0][2],
                      'next_sw': results[0][3],
                      'sw_corr': results[0][4],
                      'timestamp': timestamp}
        data.assign_attrs(attributes)
        data.to_netcdf(fname) # save data
    
    t = threading.Thread(target=_collect_data, 
                         args=(data, streamer, results, timestamp, fname))
    t.start()
    
    return


def generate_pink_noise(duration, volume=1, sample_rate=44100):
    # Compute n. of samples
    samples = int(duration * sample_rate)
    # Generate white noise
    white_noise = np.random.normal(0, 1, samples)
    # Make filter for pink noise
    b, a = ss.butter(1, 1.0, btype='lowpass', fs=sample_rate)
    # Apply filter to obtain pink noise
    pink_noise = ss.lfilter(b, a, white_noise)
    # Normalize
    pink_noise = pink_noise / np.max(np.abs(pink_noise))
    # Adjust volume
    pink_noise = pink_noise * volume
    
    return pink_noise
