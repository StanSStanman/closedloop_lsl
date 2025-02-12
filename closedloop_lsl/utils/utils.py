import time
import numpy as np
from psychopy import gui
import os
import shutil
import platform


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


def envelope(data: np.ndarray, n_excl: int=1, n_kept: int=3)-> np.ndarray:
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
    data = np.sort(data, axis=0, kind='quicksort')
    # data = np.sort(data, axis=0, kind='stable')
    envp = np.mean(data[n_excl:n_excl+n_kept, :], axis=0, keepdims=True)
    
    return envp


def get_participant_info():
    dlg = gui.Dlg(title='Welcome to Closed-Loop LSL')
    dlg.addField("Participant ID:")
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
