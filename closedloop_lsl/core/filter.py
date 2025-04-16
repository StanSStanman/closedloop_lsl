import numpy as np
from scipy.signal import firwin, lfilter, lfilter_zi
import mne

# class SlidingFilter:
#     def __init__(self, sfreq, low_freq = .5, high_freq = 4.,
#                 filter_length = 'auto', picks=None, method='fir',
#                 iir_params=None, pad='reflect_limited'):
        
#         self.fs = sfreq
#         self.fir_coeff = mne.filter.create_filter(data=None, sfreq=sfreq, 
#                                                   l_freq=low_freq, 
#                                                   h_freq=high_freq, 
#                                                   method=method, 
#                                                   filter_length=filter_length, 
#                                                   iir_params=iir_params)
#         if isinstance(picks, slice):
#             picks = list(range(picks.stop))
#         self.picks = picks
            
#         self.numtaps = self.fir_coeff.shape[0]
#         self.is_active = False
        

#     def update(self, buffer, new_data_len):
#         """
#         Efficiently filter overlapping EEG buffer by only recomputing the changed tail.

#         buffer        : (n_channels, n_samples), full new buffer
#         new_data_len  : int, number of new data points added to buffer since last call
        
#         Returns:
#             filtered : (n_channels, n_samples), filtered version of buffer
#         """
        
#         _buff = buffer.copy().astype(np.float32)
#         _buff = _buff[self.picks, :] if self.picks is not None else _buff   
        
#         n_channels, n_samples = _buff.shape
#         assert n_channels == self.n_channels

#         # Get just the new part (+ tail context)
#         tail_start = n_samples - (new_data_len + self.numtaps - 1)
#         extended_chunk = _buff[:, tail_start:]

#         # Prepend previous filter tail
#         to_filter = np.concatenate((self.last_tail, extended_chunk), axis=-1)

#         # Filter the chunk
#         filtered_tail = lfilter(self.fir_coeff, [1.0], to_filter, axis=-1)

#         # Update tail state for next run
#         self.last_tail = _buff[:, -(self.numtaps - 1):].copy()

#         # Merge filtered output
#         filtered_full = np.empty_like(_buff, dtype=np.float32)
#         filtered_full[:, :-new_data_len] = self.prev_filtered[:, :-new_data_len]
#         filtered_full[:, -new_data_len:] = filtered_tail[:, -new_data_len:]

#         # Store for next merge
#         self.prev_filtered = filtered_full.copy()

#         return filtered_full

#     def initialize(self, buffer):
#         """
#         First-time call to initialize filter state with full buffer.
#         """
#         _buff = buffer.copy().astype(np.float32)
#         _buff = _buff[self.picks, :] if self.picks is not None else _buff
        
#         # Initialize filter state
#         self.n_channels, self.n_samples = _buff.shape
#         self.last_tail = np.zeros((self.n_channels, self.numtaps - 1), dtype=np.float32)
#         self.prev_filtered = lfilter(self.fir_coeff, [1.0], _buff, axis=-1).astype(np.float32)
#         self.last_tail = _buff[:, -(self.numtaps - 1):].copy()
#         self.is_active = True
#         return self.prev_filtered


class SlidingFilter:
    def __init__(self, sfreq, low_freq=0.5, high_freq=4.0,
                 filter_length='auto', picks=None, method='fir',
                 iir_params=None, pad='reflect_limited'):
        
        self.fs = sfreq
        self.fir_coeff = mne.filter.create_filter(data=None, sfreq=sfreq, 
                                                  l_freq=low_freq, 
                                                  h_freq=high_freq, 
                                                  method=method, 
                                                  filter_length=filter_length, 
                                                  iir_params=iir_params)
        if isinstance(picks, slice):
            picks = list(range(picks.stop))
        self.picks = picks
            
        self.numtaps = self.fir_coeff.shape[0]
        self.is_active = False
        self.zi = None  # Initial filter state

    def initialize(self, buffer):
        """
        First-time call to initialize filter state with full buffer.
        """
        _buff = buffer.copy().astype(np.float32)
        _buff = _buff[self.picks, :] if self.picks is not None else _buff
        
        # Initialize filter state
        self.n_channels, self.n_samples = _buff.shape
        self.zi = lfilter_zi(self.fir_coeff, [1.0])  # Compute initial conditions
        self.zi = self.zi = np.tile(self.zi[:, np.newaxis], (1, self.n_channels))
        # self.filtered_full = np.empty_like(buffer, dtype=np.float32)  # Preallocate memory
        filtered_full = buffer.copy().astype(np.float32)
        filtered_full[self.picks, :], self.zi = lfilter(self.fir_coeff, [1.0], _buff, axis=-1, zi=self.zi)
        self.prev_filtered = filtered_full.copy()  # Store filtered output
        self.is_active = True
        return filtered_full

    def update(self, buffer, new_data_len):
        """
        Efficiently filter overlapping EEG buffer by recomputing the changed tail.

        buffer        : (n_channels, n_samples), full new buffer
        new_data_len  : int, number of new data points added to buffer since last call
        
        Returns:
            filtered : (n_channels, n_samples), filtered version of buffer
        """
        
        if not self.is_active:
            return self.initialize(buffer)
        
        _buff = buffer.copy().astype(np.float32)
        _buff = _buff[self.picks, :] if self.picks is not None else _buff   
        
        n_channels, n_samples = _buff.shape
        assert n_channels == self.n_channels

        # Get just the new part (+ tail context)
        tail_start = max(0, n_samples - (new_data_len + self.numtaps - 1))
        extended_chunk = _buff[:, tail_start:]

        # Filter the new data with the previous state
        filtered_tail, self.zi = lfilter(self.fir_coeff, [1.0], extended_chunk, axis=-1, zi=self.zi)

        # Merge filtered output
        # filtered_full = np.empty_like(_buff, dtype=np.float32)
        filtered_full = buffer.copy().astype(np.float32)
        filtered_full[:, :-new_data_len] = self.prev_filtered[:, :-new_data_len]
        filtered_full[self.picks, -new_data_len:] = filtered_tail[:, -new_data_len:]

        # Store for next merge
        self.prev_filtered = filtered_full.copy()

        return filtered_full
    
    def reset(self):
        """
        Reset the filter state.
        """
        self.is_active = False
        self.zi = None
        self.prev_filtered = None
        return