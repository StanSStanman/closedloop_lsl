import mne_lsl
from mne_lsl.lsl import resolve_streams
import mne

import xarray as xr
import time
import warnings
from typing import Optional, List

import threading
import queue

from closedloop_lsl.utils.utils import high_precision_sleep


class ClosedLoopLSL:
    
    def __init__(self, sfreq, ch_names=None, del_chans=None) -> None:
        self.sfreq = sfreq
        self.device = None
        self.stream = None
        
        self.connected = False
        self.aquiring_data = False
        self._aquire = False
        self.new_samples = 0
        
        self.ch_names = ch_names
        self.filt_params = None
        self.del_chans = del_chans
        self.ref_ch = None
        
        self.process = None
        self.queue = None
        self.event = None
        
        return
    
    def search_stream(self, sname: list, stype: list)->bool:
        timeout = 10.
        print('Looking for available devices...')
        
        tstart = time.time()
        
        while self.device is None:
            avail_devices = resolve_streams()
            for ad in avail_devices:
                if ad.name == sname and ad.stype == stype:
                    self.device = (ad.name, ad.stype, ad.uid)
                else:
                    print('Device not found, trying again...')
                    time.sleep(1.)
                if time.time() - tstart >= timeout:
                    warnings.warn('Unable to find the device, timeout passed')
                    return False
        time.sleep(1.)
        return True
    
        
    def open_stream(self, bufsize: float = 5.) -> None:
        
        timeout = 10.
        print('Opening stream...')
        
        if self.device is None:
            print('\tNo device to open stream from.\n')
            return False
        
        self.bufsize = bufsize
        self.buflen = int(self.sfreq * bufsize)
        
        tstart = time.time()
        while self.stream is None:
            sname, stype, suid = self.device
            try:
                self.stream = mne_lsl.stream.StreamLSL(bufsize, 
                                                       name=sname, 
                                                       stype=stype)
            except Exception:
                print('Unable to open stream', sname)
                    
            if self.stream is None:
                print('Unable to open stream, trying again...')
                time.sleep(1.)
            else:
                print('\tOpened correspondig streams.\n')
                
            if time.time() - tstart >= timeout:
                warnings.warn('Unable to open stream, timeout passed')
                return
        
        time.sleep(1.) 
        return False
    
    def connect_stream(self) -> bool:
        
        timeout = 20.
        print('Connecting to the stream...')
        
        if self.stream is None:
            print('\tNo available stream to connect to.\n')
            return False
        
        tstart = time.time()
        while not self.stream.connected:
            try:
                self.stream.connect(acquisition_delay=0, 
                                    processing_flags='all', 
                                    timeout=10.)
            except Exception:
                    print('Unable to connect to stream', self.stream._name)
            
            if not self.stream.connected:
                print('Unable to connect to the stream, trying again...')
                time.sleep(1.)
            else:
                time.sleep(1.)
                self.connected = True
                print('\tStream connected.\n')
                
            if time.time() - tstart >= timeout:
                warnings.warn('Unable to open the stream, timeout passed')
                return False

        time.sleep(1.)
        return True
    
    
    def disconnect_streams(self) -> None:
        print('Disconnecting from the stream...')
        if self.stream.connected:
            self.stream.disconnect()
        self.connected = False
        print('\tStream disconnected.\n')
        return True
    
    def set_ch_types(self, ch_types: dict) -> None:
        if self.stream is None:
            print('No stream available to set channel types.')
            return
        else:
            orig_ch_types = self.stream.get_channel_types()
            orig_ch_types = {ch: t for ch, t in zip(self.stream.ch_names,
                                                    orig_ch_types)}
            for ch, t in ch_types.items():
                orig_ch_types[ch] = t
            self.stream.set_channel_types(orig_ch_types)
            self.ch_types = orig_ch_types
            print('Channel types set:', ch_types)
        return
    
    # If only mne_lsl filters worked...
    # def apply_filter(self, low_freq: float = .5, 
    #                  high_freq: float = 4.,
    #                  picks=None,
    #                  iir_params=None) -> None:
        
    #     # params = {'ftype': 'cheby2', 'gpass': 3, 'gstop': 10, 'output': 'ba'}
    #     # params = dict(order=4, ftype='butter', output='sos')
    #     # iir_params = mne.filter.construct_iir_filter(params, 
    #     #                                              f_pass=[.5, 4.], 
    #     #                                              f_stop=[.1, 10.], 
    #     #                                              sfreq=500., 
    #     #                                              btype='bandpass')
    #     self.stream.filter(low_freq, high_freq, 
    #                        picks=picks, iir_params=iir_params)        
    #     # self.stream.filter(low_freq, high_freq, iir_params=None)
    #     print('Filter applied, range:', low_freq, '-', high_freq, 'Hz')            
    #     return
    
    def apply_filter(self, low_freq: float = .5, 
                     high_freq: float = 4.,
                     filter_length: str = 'auto',
                     picks=None,
                     method='fir',
                     iir_params=None,
                     pad='reflect_limited') -> None:
        filt_params = {}
        filt_params['sfreq'] = self.sfreq
        filt_params['l_freq'] = low_freq
        filt_params['h_freq'] = high_freq
        filt_params['filter_length'] = filter_length
        if isinstance(picks, list):
            # Check if channel names are set
            if self.ch_names is not None:
                filt_params['picks'] = [self.ch_names.index(ch) for ch in picks]
            else:
                filt_params['picks'] = picks
        elif isinstance(picks, slice):
            filt_params['picks'] = picks
        else:
            filt_params['picks'] = None
        if iir_params is None:
            filt_params['method'] = method
        else:
            filt_params['method'] = 'iir'
        filt_params['iir_params'] = iir_params
        filt_params['pad'] = pad
        
        self.filt_params = filt_params

        print ('Applying filter with params:\n', filt_params)
        # print('Filter applied, range:', low_freq, '-', high_freq, 'Hz')            
        return
    
    def _set_filt(self, data):
        # start = time.perf_counter()
        if self.filt_params is not None:
            _data = mne.filter.filter_data(data, 
                            sfreq=self.filt_params['sfreq'],
                            l_freq=self.filt_params['l_freq'],
                            h_freq=self.filt_params['h_freq'],
                            filter_length=self.filt_params['filter_length'],
                            picks=self.filt_params['picks'],
                            method=self.filt_params['method'],
                            iir_params=self.filt_params['iir_params'],
                            pad=self.filt_params['pad'],
                            phase='zero',
                            copy=False, n_jobs=8, verbose=False)
        else:
            _data = data
        # end = time.perf_counter()
        # print('Filter time:', end - start)
        return _data
    
    
    def set_reference_channels(self, ref_ch: Optional[List[int]] = None) -> None:
        if ref_ch is None:
            print('No reference channels set.')
            return
        else:
            self.ref_ch = ref_ch
            print('Reference channels set:', ref_ch)
        return
    
    
    def _set_ref(self, data: xr.DataArray) -> xr.DataArray:
        if self.ref_ch is not None:
            data = data - data.sel(channels=self.ref_ch).mean(dim='channels')
        return data
    
    def start_acquisition(self, interval: float=.001, 
                          channels: list=list(range(64))) -> None:
        
        if not self.stream.connected:
            print('No streams are connected for aquisition.')
            return
        
        print('Starting acquisition...')
        self.aquiring_data = True
        
        def _acquire_data(interval: float, channels: list) -> None:                
            
            self._aquire = True
            
            while self.aquiring_data:
                # function timer
                # start_time = time.perf_counter()
                
                self.stream.acquire()
                # print(self.stream.n_new_samples)
                if self.stream.n_new_samples >= 10:  # Avoid taking chunks shorter than 10 points (20ms)
                    # print(self.stream.n_new_samples)
                    self.new_samples = self.stream.n_new_samples
                    
                    _dt, _ts = self.stream.get_data()
                        
                    if self.ch_names is None:
                        _chn = list(range(_dt.shape[0]))
                    else:
                        _chn = self.ch_names
                    
                    # filter timer
                    # start_filt = time.perf_counter()
                    _dt = self._set_filt(_dt)
                    # print('Filter time:', time.perf_counter() - start_filt)
                    
                    da = xr.DataArray(_dt, 
                                      coords={'channels': _chn, 
                                              'times': _ts}, 
                                      dims=('channels', 'times'))
                    # da = da.sel(channels=channels)
                    
                    if self.del_chans is not None:
                        da = da.drop_sel(channels=self.del_chans)
                    
                    da = self._set_ref(da)
                    
                    while not self.queue.empty():
                        self.queue.get()
                    self.queue.put(da)
                    self.event.set()
                    # print('Acquisition time:', time.perf_counter() - start_time)
                    
                high_precision_sleep(interval)
            
            self._aquire = False
            self.queue.put(None)
            self.event.set()
            return
        
        self.queue = queue.Queue()
        self.event = threading.Event()
        self.process = threading.Thread(target=_acquire_data, 
                                        args=(interval, channels), 
                                        daemon=True)
        self.process.start()
        
        print('\tAcquisition thread started.\n')
        high_precision_sleep(1.)
        
        return
    
    
    def get_data(self) -> xr.DataArray:
        self.event.wait()
        data = self.queue.get(block=True)
        self.event.clear()
        return data
                    
    def stop_acquisition(self):
        start = time.perf_counter()
        if not self.aquiring_data:
            print('Acquisition is not running.')
            return
        else:
            self.aquiring_data = False
            print('Stopping acquisition...')
            while self._aquire:
                pass
            self.process.join()
            print('\tAcquisition stopped.\n')
            print('Stop acquisition time:', time.perf_counter() - start)
            return
    
            
if __name__ == '__main__':
    
    import matplotlib
    matplotlib.use('Qt5Agg')
    import matplotlib.pyplot as plt
    
    streams_name = 'EE225-000000-000625'
    streams_type = 'eeg'
    
    # streams_name = 'EE225-020034-000627_on_MININT-A894NL4'
    # streams_type = 'EEG'
    
    task = ClosedLoopLSL(sfreq=500.)
    
    task.search_stream(sname=streams_name, stype=streams_type)
    
    task.open_stream(bufsize=5.)
    
    task.connect_stream()
    
    task.apply_filter()
    
    task.start_acquisition(interval=0.0001)

 
    time.sleep(1.)
    print('Acquiring data...')
    t0 = time.time()
    t1 = t0 + 10.
    data = []
    while time.time() < t1:
        cycle_time_start = time.time()
        # print(task.data)
        # high_precision_sleep(0.01)
        data.append(task.get_data())
        # print(task.data.get())
        # print(task.timestamps.get()[0][-1], time.perf_counter())
        cycle_time_end = time.time()
        print('Cycle time:', cycle_time_end - cycle_time_start)
        pass
    print('Time passed')
       
    task.stop_acquisition()
    # print('closing threads...')
    task.disconnect_streams()
    
    for d in data:
        plt.plot(d.times, d.values[0,:])
    plt.show(block=True)
    # plt.close()

    # task.protocol_thread.join()
    print('Done')
    