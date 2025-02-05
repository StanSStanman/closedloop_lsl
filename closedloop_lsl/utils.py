import time
import numpy as np


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
