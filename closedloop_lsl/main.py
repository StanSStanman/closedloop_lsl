import threading
import time
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt

from closedloop_lsl.eego_lsl import ClosedLoopLSL
from closedloop_lsl.topo_detection import SWCatcher
from closedloop_lsl.utils import high_precision_sleep

streams_name = ['EE225-000000-000625']
streams_type = ['eeg']

# Initialize the streamer
task = ClosedLoopLSL(sfreq=500.)
task.search_streams(snames=streams_name, stypes=streams_type)
task.open_streams(bufsize=5.)
task.connect_streams()
task.apply_filter(low_freq=.5, high_freq=4)
task.start_acquisition(interval=0.011)

# Create random templates
# templates = [[np.random.uniform(0, 1, (64)), 'roi1', 'neg'],
#              [np.random.uniform(0, 1, (64)), 'roi1', 'neg']]
# Load templates
tp_fname = '/media/jerry/ruggero/results/closedloop/topographies/subjects/nights/epo_topo_fronto-occipital_geodesic_64ch.nc'
templates = xr.open_dataarray(tp_fname)
cin_lh = templates.sel(rois=['cingulate-lh'], times=slice(-.015, .015)).mean('times').values.squeeze()
cin_rh = templates.sel(rois=['cingulate-rh'], times=slice(-.015, .015)).mean('times').values.squeeze()
templates = [[cin_lh, 'cingulate-lh', 'neg'], [cin_rh, 'cingulate-rh', 'neg']]
# templates = [[cin_lh, 'cingulate-lh', 'neg']]

# Initialize the detector
sw_catcher = SWCatcher(sfreq=500, 
                       stable_decrease_time=0.02, 
                       stable_increase_time=0.02,
                       neg_peaks_range=(-150e-6, -10e-6),
                       pos_peaks_range=(45e-6, 150e-6),
                       correlation_threshold=0.9,
                       distance_threshold=0.2)
# Set the templates
sw_catcher.set_templates(templates)

# Start the slow wave detection
# sw_catcher.start_sw_detection()


# task.new_protocol(interval=0.011, filter=[0.5, 15.])
# time.sleep(5)

total_time = 60.
catching_time = (5., 55.)

# print('Acquiring data...')
t0 = time.time()
t1 = t0 + total_time
t_catch = [t0 + catching_time[0], t0 + catching_time[1]] 

datas = []
results = []
results_times = []

# limted cycles for testing
# while time.time() < t1:
    
#     cycle_time_start = time.time()
    
#     data = task.data
#     # print(data.shape)
    
#     if t_catch[0] < time.time() < t_catch[1]:
#         if not sw_catcher.is_active:
#             sw_catcher.start_sw_detection()
#         sw_catcher.set_data(data.values)
#         results.append(sw_catcher.get_results())
#         results_times.append(data.times.values[-1])
#     else:
#         if sw_catcher.is_active:
#             sw_catcher.stop_sw_detection()
        
        
#     # print(task.data)
#     high_precision_sleep(0.018)
#     datas.append(data)
#     # print(task.data.get())
#     # print(task.timestamps.get()[0][-1], time.perf_counter())
    
#     cycle_time_end = time.time()
#     # print('Cycle time:', cycle_time_end - cycle_time_start)
#     pass
# print('time passed')

# Non-stop acquisition and detection


running = True  # Control flag

def listen_for_exit():
    global running
    while True:
        user_input = input()  # Wait for user input
        if user_input.lower() == "q":  # User types "q" to exit
            print("\n'q' detected! Stopping...")
            running = False
            break  # Exit the input thread

# Start the input listener in a separate thread
listener_thread = threading.Thread(target=listen_for_exit, daemon=True)
listener_thread.start()

running_mess_time = 60.
message_time_start = time.time()

sw_catcher.start_sw_detection()
while running:
    
    # cycle_time_start = time.time()
    
    data = task.data
    # print(data.shape)
    
    sw_catcher.set_data(data.values)
    res = sw_catcher.get_results()
    # print(res)
    if res[0][1] is True or res[-1][1] is True:
        print('SW detected', res)
        results.append(res)
        results_times.append(data.times.values[-1]) 
        datas.append(data)       
        
    # print(task.data)
    # high_precision_sleep(0.018)
    
    if time.time() - message_time_start > running_mess_time:
        print('Still detecting...')
        message_time_start = time.time()
        
    # cycle_time_end = time.time()
    # print('Cycle time:', cycle_time_end - cycle_time_start)
    
    # print(task.data.get())
    # print(task.timestamps.get()[0][-1], time.perf_counter())
    pass
print('time passed')
sw_catcher.stop_sw_detection()
    
task.stop_acquisition()
# print('closing threads...')
task.disconnect_streams()

correlations = []
for r in results:
    correlations.append([r[0][-1], r[1][-1]])
correlations = np.array(correlations).T

results_times = np.array(results_times)

for d in datas:
    plt.plot(d.times, d.values[0,:])
    
for c in correlations:
    plt.plot(results_times, c*1e-4)
    
plt.show()
# plt.close()

print('Done')