# Base imports
import os
import time
import datetime
import xarray as xr
import signal
import subprocess
import pyglet

# Streaming, detecting ad stimulating
from closedloop_lsl.core.manager_lsl import ClosedLoopLSL
from closedloop_lsl.core.detection import SWCatcher
from closedloop_lsl.core.stimulation import Stimulator
from closedloop_lsl.report.questionnaire import dreamquestrc
from closedloop_lsl.utils.utils import high_precision_sleep, get_participant_info, iter_draw

# Visualisation and interaction
from psychopy import monitors, visual, event, core, gui


fontFiles = ['/home/phantasos/python_projects/space/closedloop_lsl/fonts/nightsky.ttf',
             '/home/phantasos/python_projects/space/closedloop_lsl/fonts/Retro Gaming.ttf',
             '/home/phantasos/python_projects/space/closedloop_lsl/fonts/NimbusSanL-Reg.otf']
for font in fontFiles:
    pyglet.font.add_file(font)

all_monitors = monitors.getAllMonitors()
my_monitor = monitors.Monitor('Generic', width=53.1, distance=60)

# Get participant information
participant_info = get_participant_info()
print(participant_info)

# Set sounds and triggers
stim_sound = '/home/phantasos/python_projects/space/closedloop_lsl/data/sounds/beep.wav'
alarm_sound = '/home/phantasos/python_projects/space/closedloop_lsl/data/sounds/alarm.wav'
trig_codes = {'cingulate-lh': 20, 'cingulate-rh': 22,
              'occipital-lh': 30, 'occipital-rh': 32}

# Load topographies

# MAYBE IT IS BETTER TO REPLACE ALL OF THAT WITH DICTONARY
tp_fname = '/home/phantasos/python_projects/space/closedloop_lsl/data/topographies/epo_topo_fronto-occipital_geodesic_64ch.nc'
templates = xr.open_dataarray(tp_fname)
cin_lh = templates.sel(rois=['cingulate-lh'], times=slice(-.015, .015)).mean('times').values.squeeze()
cin_rh = templates.sel(rois=['cingulate-rh'], times=slice(-.015, .015)).mean('times').values.squeeze()
occ_lh = templates.sel(rois=['occipital-lh'], times=slice(-.015, .015)).mean('times').values.squeeze()
occ_rh = templates.sel(rois=['occipital-rh'], times=slice(-.015, .015)).mean('times').values.squeeze()

# Create a window
mainWin = visual.Window(size=[800, 600], pos=[0, 0], fullscr=False, color='black', allowGUI=True, title='Closed-Loop LSL v0.1')

# Introduction text
introText = visual.TextStim(mainWin, text='Welcome to\nClosed-Loop LSL!', pos=(0, .8), height=0.1, color='cyan', font='Night Sky')
subintroText = visual.TextStim(mainWin, text=' Click on \'Start stream\' when the system is ready.', pos=(0, .6), height=0.055, color='white', font='Nimbus Sans')

# Stream textbox
streamTextbox = visual.TextBox2(mainWin, text='EE225-000000-000625', pos=(.2, .3), size=(.8, .16), fillColor="white", color="black", editable=True, font='Nimbus Sans')

# Stream textbox label
streamTlabel = visual.TextStim(mainWin, text='Stream name:', pos=(-.4, .3), height=0.07)

# Stream type textbox
strtypeTextbox = visual.TextBox2(mainWin, text='eeg', pos=(.2, .1), size=(.8, .16), fillColor="white", color="black", editable=True, font='Nimbus Sans')

# Stream type textbox label
strtypeLabel = visual.TextStim(mainWin, text='Stream type:', pos=(-.4, .1), height=0.07, font='Nimbus Sans')

# Start button with a label
startButton = visual.Rect(mainWin, width=.4, height=.2, pos=(-.5, -.3), fillColor='green')
startButtonLabel = visual.TextStim(mainWin, text='Start stream', pos=(-.5, -.3), height=0.08, font='Nimbus Sans')

# Stop button with a label
stopButton = visual.Rect(mainWin, width=.4, height=.2, pos=(.5, -.3), fillColor='red')
stopButtonLabel = visual.TextStim(mainWin, text='Exit', pos=(.5, -.3), height=0.08, font='Nimbus Sans')

streamInfoText = visual.TextStim(mainWin, text='Starting the stream...', pos=(0, -.6), height=0.08, color='white', font='Nimbus Sans')

# Draw the buttons
mainWin.flip()

groupObjMain = [introText, subintroText, streamTextbox, strtypeTextbox, streamTlabel, strtypeLabel, startButton, startButtonLabel, stopButton, stopButtonLabel]

# Check if the mouse is clicked on the button
is_stream_active = False
streamMouse = event.Mouse(win=mainWin)
while True:
    iter_draw(groupObjMain)
    
    if streamMouse.isPressedIn(startButton):
        while streamMouse.getPressed()[0]:  # Wait until the mouse button is released
            core.wait(0.0001)
        startButton.fillColor = 'gray'
        stopButtonLabel.text = 'Stop stream'
        
        if not is_stream_active:
            # Starting the stream
            streamInfoText.draw()
            iter_draw(groupObjMain)
            mainWin.flip()
            # Define stream name and type
            streams_name = streamTextbox.text
            streams_type = strtypeTextbox.text
            # Activate the stream
            stream = ClosedLoopLSL(sfreq=500.)
            stream.search_stream(sname=streams_name, stype=streams_type)
            streamInfoText.text = 'Stream found.'
            streamInfoText.draw()
            iter_draw(groupObjMain)
            mainWin.flip()
            
            stream.open_stream(bufsize=5.)
            streamInfoText.text = 'Stream opened.'
            streamInfoText.draw()
            iter_draw(groupObjMain)
            mainWin.flip()
            
            stream.connect_stream()
            streamInfoText.text = 'Stream connected.'
            streamInfoText.draw()
            iter_draw(groupObjMain)
            mainWin.flip()
            
            stream.apply_filter(low_freq=.5, high_freq=4)
            stream.start_acquisition(interval=0.002)
            streamInfoText.text = 'Stream active.'
            streamInfoText.draw()
            iter_draw(groupObjMain)
            mainWin.flip()
            
            is_stream_active = True
            
        # Make the main window opaque
        
        # Open the viewer
        command = f'mne-lsl viewer -s {streams_name}'
        viewer = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                  shell=True, preexec_fn=os.setsid)
        
        # New window for the detection
        detectWin = visual.Window(size=[500, 500], pos=(300, 100), monitor=my_monitor, fullscr=False, color='black', allowGUI=True, title='SW selection')
        detectText = visual.TextStim(detectWin, text='Automatic SW Detection', pos=(0, .8), height=0.12, color='cyan', font='Night Sky')
        detectText.draw()
        detectSubText = visual.TextStim(detectWin, text='Click on \'Start detect\' to begin.', pos=(0, .55), height=0.065, color='white', font='Nimbus Sans')
        detectSubText.draw()
        startDetectText = visual.TextStim(detectWin, text='Starting the detection...', pos=(0, -.6), height=0.08, color='white', font='Nimbus Sans')
        
        # Topo selection buttons
        selected_topo = 'cingulate'
        topoText = visual.TextStim(detectWin, text='Select the topographies:', pos=(0, .35), height=0.08, color='white', font='Nimbus Sans')
        topo1Label = visual.TextStim(detectWin, text='Cingulate', pos=(-.5, .2), height=0.075, font='Nimbus Sans')
        topo2Label = visual.TextStim(detectWin, text='Occipital', pos=(.5, .2), height=0.075, font='Nimbus Sans')
        if selected_topo == 'cingulate':
            topo1Button = visual.Circle(detectWin, radius=.05, pos=(-.5, .05), fillColor='green')
            topo2Button = visual.Circle(detectWin, radius=.05, pos=(.5, .05), fillColor='white')
        else:
            topo1Button = visual.Circle(detectWin, radius=.05, pos=(-.5, .05), fillColor='white')
            topo2Button = visual.Circle(detectWin, radius=.05, pos=(.5, .05), fillColor='green')
            
        # Peak detection buttons
        selected_peak = 'negative'
        peakText = visual.TextStim(detectWin, text='Select the peak type:', pos=(0, -.2), height=0.08, color='white', font='Nimbus Sans')
        peak1Label = visual.TextStim(detectWin, text='Negative', pos=(-.5, -.35), height=0.08, font='Nimbus Sans')
        peak2Label = visual.TextStim(detectWin, text='Positive', pos=(.5, -.35), height=0.08, font='Nimbus Sans')
        if selected_peak == 'negative':
            peak1Button = visual.Circle(detectWin, radius=.05, pos=(-.5, -.5), fillColor='green')
            peak2Button = visual.Circle(detectWin, radius=.05, pos=(.5, -.5), fillColor='white')
        else:
            peak1Button = visual.Circle(detectWin, radius=.05, pos=(-.5, -.5), fillColor='white')
            peak2Button = visual.Circle(detectWin, radius=.05, pos=(.5, -.5), fillColor='green')
        
        # Start detection button
        detectButton = visual.Rect(detectWin, width=.5, height=.2, pos=(-.4, -.8), fillColor='green')
        detectButtonLabel = visual.TextStim(detectWin, text='Start detect', pos=(-.4, -.8), height=0.08, font='Nimbus Sans')
        
        # Stop detection button
        stopDetectButton = visual.Rect(detectWin, width=.5, height=.2, pos=(.4, -.8), fillColor='red')
        stopDetectButtonLabel = visual.TextStim(detectWin, text='Exit', pos=(.4, -.8), height=0.08, font='Nimbus Sans')
        
        detectWin.flip()
        
        groupObjDetect = [detectText, detectSubText, topoText, topo1Label, topo2Label, topo1Button, topo2Button, peakText, peak1Label, peak2Label, peak1Button, peak2Button, detectButton, detectButtonLabel, stopDetectButton, stopDetectButtonLabel]
        
        # Reinitializing the stream makes you unsure about the devices
        not_really_sure_about_the_devices = True
        
        # Mouse
        detectMouse = event.Mouse(win=detectWin)
        while True:
            iter_draw(groupObjDetect)
            # Choose the topography and peak type
            if detectMouse.isPressedIn(topo1Button):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                selected_topo = 'cingulate'
                topo1Button.fillColor = 'green'
                topo2Button.fillColor = 'white'
            elif detectMouse.isPressedIn(topo2Button):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                selected_topo = 'occipital'
                topo1Button.fillColor = 'white'
                topo2Button.fillColor = 'green'
                
            if detectMouse.isPressedIn(peak1Button):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                selected_peak = 'negative'
                peak1Button.fillColor = 'green'
                peak2Button.fillColor = 'white'
            elif detectMouse.isPressedIn(peak2Button):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                selected_peak = 'positive'
                peak1Button.fillColor = 'white'
                peak2Button.fillColor = 'green'
                
            if detectMouse.isPressedIn(detectButton):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                detectButton.fillColor = 'gray'
                startDetectText.draw()
                stopDetectButtonLabel.text = 'Stop detect'
                
                iter_draw(groupObjDetect)
                detectWin.flip()
                
                # Creating templates
                if selected_topo == 'cingulate':
                    templates = [[cin_lh, 'cingulate-lh', None], [cin_rh, 'cingulate-rh', None]]
                else:
                    templates = [[occ_lh, 'occipital-lh', None], [occ_rh, 'occipital-rh', None]]
                
                if selected_peak == 'negative':
                    for template in templates:
                        template[2] = 'neg'
                else:
                    for template in templates:
                        template[2] = 'pos'
                
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
                sw_catcher.start_sw_detection()
                
                # Initialize the stimulator
                stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                    trig_codes=trig_codes)
                sound_dev = stimulator.get_devices()
                record_dev = stimulator.get_devices(capture_devices=True)
                
                # maybe add an autoselector for the devices here 
                
                # Select devices
                while not_really_sure_about_the_devices:
                    devsel = gui.Dlg(title='Select audio devices')
                    devsel.addField("Speakers device:", choices=sound_dev)
                    devsel.addField("Headphones device", choices=sound_dev)
                    # devsel.addField("Microphone device", choices=record_dev)

                    params = devsel.show()

                    if devsel.OK:
                        # spk, hdp, mic = params.values()
                        spk, hdp = params.values()
                        not_really_sure_about_the_devices = False
                    else:
                        print("No way, you must select the devices. Make a wise choice.")
                
                stimulator.set_devices(speakers=spk, headphones=hdp)
                stimulator.start()
                
                startDetectText.text = 'Detection started'
                startDetectText.draw()
                iter_draw(groupObjDetect)
                detectWin.flip()
                
                check_detect = 60.
                checkpoint = time.time()
                
                # Timer for the interrupt
                interrupt_time = 5. # seconds
                timer_text = 'Alarm will play in:\n{0}'
                # Prepare interrupt stimulation window
                interruptWin = visual.Window(size=[300, 300], pos=(250, 250), monitor=my_monitor, fullscr=False, color='black', allowGUI=True, title='Be ready!')
                interruptText = visual.TextStim(interruptWin, text='Button will become green when a SW is detected.\nPress it within 5 seconds to stop stimulation.', pos=(0, .65), height=0.12, color='white', wrapWidth=1.5, font='Nimbus Sans')
                interruptText.draw()
                interruptButton = visual.Rect(interruptWin, width=1.85, height=1.2, pos=(0, -.35), fillColor='gray')
                interruptButton.draw()
                interruptButtonLabel = visual.TextStim(interruptWin, text='Click to stop stimulation', pos=(0, -.35), height=0.28, color='white', wrapWidth=1.5, font='Nimbus Sans')
                interruptButtonLabel.draw()
                interruptWin.flip()
                
                # Core of the closed loop
                stopstimMouse = event.Mouse(win=interruptWin)
                running = True
                while running:

                    # cycle_time_start = time.time()
                    data = stream.get_data()
                    sw_catcher.set_data(data.values)
                    res = sw_catcher.get_results()
                    # Check if one topography corresponds to a SW
                    if res[0][1] is True or res[-1][1] is True:
                        print('SW detected', res)  
                        
                        # Chose the most correlated topography
                        if not stimulator.is_stimulating:
                            if res[0][-1] > res[-1][-1]:
                                stimulator.send_stim(res[0])
                            else:
                                stimulator.send_stim(res[-1])
                                
                        start_stim_time = time.perf_counter()
                        interruptButton.fillColor = 'green'
                        interruptButton.draw()
                        interruptButtonLabel.draw()
                        interruptWin.flip()
                        stim_completed = True
                        # Interrupt the stimulation if the button is pressed
                        while time.perf_counter() - start_stim_time < interrupt_time:
                            # st = time.time()
                            # countdown = np.round(interrupt_time - (time.time() - start_stim_time), 3)
                            # interruptText.text = timer_text.format(countdown)
                            # interruptText.draw()
                            
                            if stopstimMouse.isPressedIn(interruptButton):
                                while stopstimMouse.getPressed()[0]:  # Wait until the mouse button is released
                                    core.wait(0.0001)
                                stimulator.stop_stimulation()
                                stim_completed = False
                                break
                            # et = time.time()
                            # print('Time to draw:', et - st)
                            # high_precision_sleep(0.0001)
                            
                            # ADD SET THE INTERRUPTION WINDW BACK TO THE ORIGINAL
                            # ADD THE QUESTIONNAIRE AND THE AUTOMATIC DETECTION STOP AFTER THE QUESTIONNAIRE
                        
                        running = False
                        # Stop stimulator
                        stimulator.stop()
                        interruptWin.close()
                        # Stop detection
                        sw_catcher.stop_sw_detection()
                        startDetectText.text = 'Detection stopped'
                        startDetectText.draw()
                        iter_draw(groupObjDetect)
                        detectButton.fillColor = 'green'
                        stopDetectButton.fillColor = 'red'
                        stopDetectButtonLabel.text = 'Exit'
                        detectWin.flip()
                        high_precision_sleep(1.)
                        if stim_completed:
                            # sart questionnatire
                            print('Questionnaire started')
                            dq = dreamquestrc(*(participant_info))
                        break
                            
                                                            
                    if time.time() - checkpoint > check_detect:
                        now = datetime.datetime.now().strftime("%H:%M:%S")
                        print('Still detecting...', now)
                        checkpoint = time.time()
                        
                    # Stopping detection after it has started
                    if detectMouse.isPressedIn(stopDetectButton):
                        while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                            core.wait(0.0001)
                        running = False
                        # Stop stimulator
                        stimulator.stop()
                        interruptWin.close()
                        # Stop detection
                        sw_catcher.stop_sw_detection()
                        startDetectText.text = 'Detection stopped'
                        startDetectText.draw()
                        iter_draw(groupObjDetect)
                        detectButton.fillColor = 'green'
                        stopDetectButton.fillColor = 'red'
                        stopDetectButtonLabel.text = 'Exit'
                        detectWin.flip()
                        high_precision_sleep(1.)
                        break
            
            # Stop detection and close detection window
            elif detectMouse.isPressedIn(stopDetectButton):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                stopDetectButton.fillColor = 'gray'
                startDetectText.text = 'Exit detection'
                startDetectText.draw()
                iter_draw(groupObjDetect)
                detectWin.flip()
                high_precision_sleep(2.)
                detectWin.close()
                startButtonLabel.text = 'Open detect' 
                startButton.fillColor = 'green'
                streamInfoText.text = 'Straming starting...'               
                break
                
            detectWin.flip()
            
        
        # print(streamTextbox.text)
        # print(strtypeTextbox.text)
        # # startButton.fillColor = 'green'
        # # stopButtonLabel.text = 'Exit'
        # mainWin.flip()
        
    
    if streamMouse.isPressedIn(stopButton):
        while streamMouse.getPressed()[0]:  # Wait until the mouse button is released
            core.wait(0.0001)
        if is_stream_active:
            stream.stop_acquisition()
            stream.disconnect_streams()
            startButton.fillColor = 'green'
            stopButtonLabel.text = 'Exit'
            is_stream_active = False
            viewer.terminate()
            try:
                os.killpg(os.getpgid(viewer.pid), signal.SIGTERM)
            except Exception as e:
                pass
        else:
            stopButton.fillColor = 'gray'
            streamInfoText.text = 'ClosedLoop stopping.'
            streamInfoText.draw()
            byesubText = visual.TextStim(mainWin, text='Turn your computer off and go to sleep!', pos=(0, -.75), height=0.07, color='violet', wrapWidth=1.5, font='Retro Gaming')
            byesubText.draw()
            mainWin.flip()
            core.wait(3.)
            break
    
    mainWin.flip()

mainWin.close()
core.quit()
