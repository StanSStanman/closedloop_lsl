# Base imports
import os
import os.path as op
import time
import datetime

import signal
import subprocess
import pyglet
import warnings

# Streaming, detecting ad stimulating
from closedloop_lsl.config.config import read_config
from closedloop_lsl.core.templates_topo import TopoTemplates
from closedloop_lsl.core.manager_lsl import ClosedLoopLSL
from closedloop_lsl.core.detection import SWCatcher
from closedloop_lsl.core.stimulation import Stimulator
from closedloop_lsl.report.questionnaire import dreamquestrc
from closedloop_lsl.utils.utils import high_precision_sleep, get_participant_info, collect_data

# Visualisation and interaction
from psychopy import monitors, visual, event, core, gui

# Set environmental variable for driver selection
os.environ['SDL_AUDIODRIVER'] = 'alsa'

# Set the configuration
cfg = read_config()

# Add custom fonts
fontsDir = cfg['DEFAULT']['FontsPath']
pyglet.font.add_directory(fontsDir)

all_monitors = monitors.getAllMonitors()
my_monitor = monitors.Monitor('Generic', width=53.1, distance=60)

# Get participant information
participant_info = get_participant_info()
print(participant_info)

# Create folder for the participant
pc_id, sesison, gender = participant_info
participant_folder = op.join(cfg['PATHS']['ResultsPath'], pc_id, sesison)
if not os.path.exists(participant_folder):
    os.makedirs(participant_folder)
else:
    # Raise warning in terminal!
    warnings.warn(f'Participant {pc_id} already exists in the database. Check the data.', UserWarning)

# Set sounds and triggers
stim_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'PN_44100Hz_50ms.wav')
alarm_sound = op.join(cfg['DEFAULT']['SoundsPath'], 'alarm.wav')
trig_codes = {'cingulate-lh': 22, 'cingulate-rh': 24,
              'occipital-lh': 32, 'occipital-rh': 34}

eeg_channels = ['0Z', '1Z', '2Z', '3Z', '4Z', '1L', '1R', 
                '1LB', '1RB', '2L', '2R', '3L', '3R', 
                '4L', '4R', '1LC', '1RC', '2LB', '2RB', 
                '1LA', '1RA', '1LD', '1RD', '2LC', '2RC', 
                '3LB', '3RB', '3LC', '3RC', '2LD', '2RD', 
                '3RD', '3LD', '9Z', '8Z', '7Z', '6Z', 'EOG',
                '10L', '10R', '9L', '9R', '8L', '8R', 
                '7L', '7R', '6L', '6R', '5L', '5R', 
                '4LD', '4RD', '5LC', '5RC', '5LB', '5RB', 
                '3LA', '3RA', '2LA', '2RA', '4LC', '4RC', 
                '4LB', '4RB', 'BIP1', 'BIP2', 'BIP3',
                'TRIG1']
# eeg_channels = ['Z1L', 'Z2L', 'Z3L', 'Z4L', 'Z5L', 'Z6L', 'Z7L', 'Z8L', 
#                 'Z9L', 'Z10L', 'Z11L', 'Z12L', 'Z13L', 'Z14L', 'Z15L', 
#                 'Z16L', 'Z17L', 'Z18L', 'Z19L', 'L1Z', 'L2Z', 'L3Z', 
#                 'L4Z', 'L5Z', 'L6Z', 'L7Z', 'L8Z', 'L9Z', 'L10Z', 'L11Z', 
#                 'L12Z', 'L13Z', 'L14Z', 'L15Z', 'L16Z', 'L17Z', 'L18Z', 
#                 'L19Z', 'L20Z', 'L1L', 'L2L', 'L3L', 'L4L', 'L5L', 'L6L', 
#                 'L7L', 'L8L', 'L9L', 'L10L', 'L11L', 'L12L', 'L13L', 
#                 'L14L', 'L15L', 'L16L', 'L17L', 'L18L', 'L19L', 'L1A', 
#                 'L2A', 'L3A', 'L4A', 'L5A', 'L6A', 'L1B', 'L2B', 'L3B', 
#                 'L4B', 'L5B', 'L6B', 'L7B', 'L1C', 'L2C', 'L3C', 'L4C', 
#                 'L5C', 'L6C', 'L7C', 'L8C', 'L1D', 'L2D', 'L3D', 'L4D', 
#                 'L5D', 'L6D', 'L7D', 'L8D', 'L9D', 'L1E', 'L2E', 'L3E', 
#                 'L4E', 'L5E', 'L6E', 'L7E', 'L8E', 'L9E', 'L10E', 'L1F', 
#                 'L2F', 'L3F', 'L4F', 'L5F', 'L6F', 'L7F', 'L8F', 'L1G', 
#                 'L2G', 'L3G', 'L4G', 'L5G', 'L6G', 'L7G', 'L1H', 'L2H', 
#                 'L3H', 'L4H', 'L5H', 'Z1Z', 'Z2Z', 'Z3Z', 'Z4Z', 'Z5Z', 
#                 'Z6Z', 'Z7Z', 'Z8Z', 'Z9Z', 'Z10Z', 'Z1R', 'Z2R', 'Z3R', 
#                 'Z4R', 'Z5R', 'Z6R', 'Z7R', 'Z8R', 'Z9R', 'Z10R', 'Z11R', 
#                 'Z12R', 'Z13R', 'Z14R', 'Z15R', 'Z16R', 'Z17R', 'Z18R', 
#                 'Z19R', 'R1Z', 'R2Z', 'R3Z', 'R4Z', 'R5Z', 'R6Z', 'R7Z', 
#                 'R8Z', 'R9Z', 'R10Z', 'R11Z', 'R12Z', 'R13Z', 'R14Z', 
#                 'R15Z', 'R16Z', 'R17Z', 'R18Z', 'R19Z', 'R20Z', 'R1R', 
#                 'R2R', 'R3R', 'R4R', 'R5R', 'R6R', 'R7R', 'R8R', 'R9R', 
#                 'R10R', 'R11R', 'R12R', 'R13R', 'R14R', 'R15R', 'R16R', 
#                 'R17R', 'R18R', 'R19R', 'R1A', 'R2A', 'R3A', 'R4A', 'R5A', 
#                 'R6A', 'R1B', 'R2B', 'R3B', 'R4B', 'R5B', 'R6B', 'R7B', 
#                 'R1C', 'R2C', 'R3C', 'R4C', 'R5C', 'R6C', 'R7C', 'R8C', 
#                 'R1D', 'R2D', 'R3D', 'R4D', 'R5D', 'R6D', 'R7D', 'R8D', 
#                 'R9D', 'R1E', 'R2E', 'R3E', 'R4E', 'R5E', 'R6E', 'R7E', 
#                 'R8E', 'R9E', 'R10E', 'R1F', 'R2F', 'R3F', 'R4F', 'R5F', 
#                 'R6F', 'R7F', 'R8F', 'R1G', 'R2G', 'R3G', 'R4G', 'R5G', 
#                 'R6G', 'R7G', 'R1H', 'R2H', 'R3H', 'R4H', 'R5H', 'Z11Z', 
#                 'VEOGR', 'Z13Z', 'Z14Z', 'Z15Z', 'Z16Z', 'Z17Z', 'Z18Z', 
#                 'Z19Z', 'Z20Z', 'BIP1', 'BIP2', 'BIP3', 'TRIG1']

deleted_channels = ['EOG', 'BIP1', 'BIP2', 'BIP3']
# deleted_channels = ['VEOGR', 'BIP1', 'BIP2', 'BIP3']

# Load topographies

# MAYBE IT IS BETTER TO REPLACE ALL OF THAT WITH DICTONARY
tp_dir = cfg['DEFAULT']['TemplatesPath']
tp_fname = op.join(tp_dir, 'epo_topo_geodesic_mastoid-ref_64ch.nc')
# tp_fname = op.join(tp_dir, 'epo_topo_geodesic_mastoid-ref_256ch.nc')
all_templates = TopoTemplates()
all_templates.load_templates(tp_fname)
all_templates.reorder_channels(['0Z', '1Z', '2Z', '3Z', '4Z', '1L', '1R', 
                                '1LB', '1RB', '2L', '2R', '3L', '3R', 
                                '4L', '4R', '1LC', '1RC', '2LB', '2RB', 
                                '1LA', '1RA', '1LD', '1RD', '2LC', '2RC', 
                                '3LB', '3RB', '3LC', '3RC', '2LD', '2RD', 
                                '3RD', '3LD', '9Z', '8Z', '7Z', '6Z',
                                '10L', '10R', '9L', '9R', '8L', '8R', 
                                '7L', '7R', '6L', '6R', '5L', '5R', 
                                '4LD', '4RD', '5LC', '5RC', '5LB', '5RB', 
                                '3LA', '3RA', '2LA', '2RA', '4LC', '4RC', 
                                '4LB', '4RB', '5Z'])
# all_templates.reorder_channels(['Z1L', 'Z2L', 'Z3L', 'Z4L', 'Z5L', 'Z6L', 'Z7L', 'Z8L', 
#                                 'Z9L', 'Z10L', 'Z11L', 'Z12L', 'Z13L', 'Z14L', 'Z15L', 
#                                 'Z16L', 'Z17L', 'Z18L', 'Z19L', 'L1Z', 'L2Z', 'L3Z', 
#                                 'L4Z', 'L5Z', 'L6Z', 'L7Z', 'L8Z', 'L9Z', 'L10Z', 'L11Z', 
#                                 'L12Z', 'L13Z', 'L14Z', 'L15Z', 'L16Z', 'L17Z', 'L18Z', 
#                                 'L19Z', 'L20Z', 'L1L', 'L2L', 'L3L', 'L4L', 'L5L', 'L6L', 
#                                 'L7L', 'L8L', 'L9L', 'L10L', 'L11L', 'L12L', 'L13L', 
#                                 'L14L', 'L15L', 'L16L', 'L17L', 'L18L', 'L19L', 'L1A', 
#                                 'L2A', 'L3A', 'L4A', 'L5A', 'L6A', 'L1B', 'L2B', 'L3B', 
#                                 'L4B', 'L5B', 'L6B', 'L7B', 'L1C', 'L2C', 'L3C', 'L4C', 
#                                 'L5C', 'L6C', 'L7C', 'L8C', 'L1D', 'L2D', 'L3D', 'L4D', 
#                                 'L5D', 'L6D', 'L7D', 'L8D', 'L9D', 'L1E', 'L2E', 'L3E', 
#                                 'L4E', 'L5E', 'L6E', 'L7E', 'L8E', 'L9E', 'L10E', 'L1F', 
#                                 'L2F', 'L3F', 'L4F', 'L5F', 'L6F', 'L7F', 'L8F', 'L1G', 
#                                 'L2G', 'L3G', 'L4G', 'L5G', 'L6G', 'L7G', 'L1H', 'L2H', 
#                                 'L3H', 'L4H', 'L5H', 'Z1Z', 'Z2Z', 'Z3Z', 'Z4Z', 'Z5Z', 
#                                 'Z6Z', 'Z7Z', 'Z8Z', 'Z9Z', 'Z10Z', 'Z1R', 'Z2R', 'Z3R', 
#                                 'Z4R', 'Z5R', 'Z6R', 'Z7R', 'Z8R', 'Z9R', 'Z10R', 'Z11R', 
#                                 'Z12R', 'Z13R', 'Z14R', 'Z15R', 'Z16R', 'Z17R', 'Z18R', 
#                                 'Z19R', 'R1Z', 'R2Z', 'R3Z', 'R4Z', 'R5Z', 'R6Z', 'R7Z', 
#                                 'R8Z', 'R9Z', 'R10Z', 'R11Z', 'R12Z', 'R13Z', 'R14Z', 
#                                 'R15Z', 'R16Z', 'R17Z', 'R18Z', 'R19Z', 'R20Z', 'R1R', 
#                                 'R2R', 'R3R', 'R4R', 'R5R', 'R6R', 'R7R', 'R8R', 'R9R', 
#                                 'R10R', 'R11R', 'R12R', 'R13R', 'R14R', 'R15R', 'R16R', 
#                                 'R17R', 'R18R', 'R19R', 'R1A', 'R2A', 'R3A', 'R4A', 'R5A', 
#                                 'R6A', 'R1B', 'R2B', 'R3B', 'R4B', 'R5B', 'R6B', 'R7B', 
#                                 'R1C', 'R2C', 'R3C', 'R4C', 'R5C', 'R6C', 'R7C', 'R8C', 
#                                 'R1D', 'R2D', 'R3D', 'R4D', 'R5D', 'R6D', 'R7D', 'R8D', 
#                                 'R9D', 'R1E', 'R2E', 'R3E', 'R4E', 'R5E', 'R6E', 'R7E', 
#                                 'R8E', 'R9E', 'R10E', 'R1F', 'R2F', 'R3F', 'R4F', 'R5F', 
#                                 'R6F', 'R7F', 'R8F', 'R1G', 'R2G', 'R3G', 'R4G', 'R5G', 
#                                 'R6G', 'R7G', 'R1H', 'R2H', 'R3H', 'R4H', 'R5H', 'Z11Z', 
#                                 'Z13Z', 'Z14Z', 'Z15Z', 'Z16Z', 'Z17Z', 'Z18Z', 
#                                 'Z19Z', 'Z20Z', 'Z12Z'])

all_templates.del_channels(['5Z'])
# all_templates.del_channels(['Z12Z'])

# Create a window
mainWin = visual.Window(size=[800, 600], pos=[0, 0], fullscr=False, color='black', allowGUI=True, title='Closed-Loop LSL v0.1')

# Introduction text
introText = visual.TextStim(mainWin, text='Welcome to\nClosed-Loop LSL!', pos=(0, .8), height=0.1, color='cyan', font='Night Sky', autoDraw=True)
subintroText = visual.TextStim(mainWin, text=' Click on \'Start stream\' when the system is ready.', pos=(0, .6), height=0.055, color='white', font='Nimbus Sans', autoDraw=True)

# Stream textbox
streamTextbox = visual.TextBox2(mainWin, text='EE225-020034-000625_on_MININT-A894NL4', pos=(.2, .3), size=(.8, .16), fillColor="white", color="black", editable=True, font='Nimbus Sans', autoDraw=True)
# streamTextbox = visual.TextBox2(mainWin, text='EE225-020034-000625_on_MININT-A894NL4', pos=(.2, .3), size=(.8, .16), fillColor="white", color="black", editable=True, font='Nimbus Sans', autoDraw=True)

# Stream textbox label
streamTlabel = visual.TextStim(mainWin, text='Stream name:', pos=(-.4, .3), height=0.07, font='Nimbus Sans', autoDraw=True)

# Stream type textbox
# strtypeTextbox = visual.TextBox2(mainWin, text='eeg', pos=(.2, .1), size=(.8, .16), fillColor="white", color="black", editable=True, font='Nimbus Sans', autoDraw=True)
strtypeTextbox = visual.TextBox2(mainWin, text='EEG', pos=(.2, .1), size=(.8, .16), fillColor="white", color="black", editable=True, font='Nimbus Sans', autoDraw=True)

# Stream type textbox label
strtypeLabel = visual.TextStim(mainWin, text='Stream type:', pos=(-.4, .1), height=0.07, font='Nimbus Sans', autoDraw=True)

# Start button with a label
startButton = visual.Rect(mainWin, width=.4, height=.2, pos=(-.5, -.3), fillColor='green', autoDraw=True)
startButtonLabel = visual.TextStim(mainWin, text='Start stream', pos=(-.5, -.3), height=0.08, font='Nimbus Sans', autoDraw=True)

# Stop button with a label
stopButton = visual.Rect(mainWin, width=.4, height=.2, pos=(.5, -.3), fillColor='red', autoDraw=True)
stopButtonLabel = visual.TextStim(mainWin, text='Exit', pos=(.5, -.3), height=0.08, font='Nimbus Sans', autoDraw=True)

streamInfoText = visual.TextStim(mainWin, text='Starting the stream...', pos=(0, -.6), height=0.08, color='white', font='Nimbus Sans')

# Draw the buttons
mainWin.flip()

# Check if the mouse is clicked on the button
is_stream_active = False
streamMouse = event.Mouse(win=mainWin)
while True:
    
    if streamMouse.isPressedIn(startButton):
        while streamMouse.getPressed()[0]:  # Wait until the mouse button is released
            core.wait(0.0001)
        startButton.fillColor = 'gray'
        stopButtonLabel.text = 'Stop stream'
        
        if not is_stream_active:
            # Starting the stream
            streamInfoText.setAutoDraw(True)
            mainWin.flip()
            # Define stream name and type
            streams_name = streamTextbox.text
            streams_type = strtypeTextbox.text
            # Activate the stream
            stream = ClosedLoopLSL(sfreq=500, 
                                   ch_names=eeg_channels, 
                                   del_chans=deleted_channels)
            stream.search_stream(sname=streams_name, stype=streams_type)
            streamInfoText.text = 'Stream found.'
            mainWin.flip()
            
            stream.open_stream(bufsize=7.)
            streamInfoText.text = 'Stream opened.'
            mainWin.flip()
            
            stream.connect_stream()
            streamInfoText.text = 'Stream connected.'
            mainWin.flip()
            
            stream.apply_filter(low_freq=.5, high_freq=4.,
                                filter_length='auto',
                                picks=slice(0, 64),
                                method='fir',
                                iir_params=None,
                                pad='reflect')
            # stream.apply_filter(low_freq=.5, high_freq=4.,
            #                     filter_length='auto',
            #                     picks=slice(0, 256),
            #                     method='fir',
            #                     iir_params=None,
            #                     pad='reflect')
            print('Filter applied')
            stream.set_reference_channels(['3LD', '3RD'])
            # stream.set_reference_channels(['R4H', 'L4H'])
            stream.start_acquisition(interval=0.001)
            streamInfoText.text = 'Stream active.'
            mainWin.flip()
            streamInfoText.setAutoDraw(False)
            
            is_stream_active = True
            
            # Open the viewer
            command = f'mne-lsl viewer -s {streams_name}'
            viewer = subprocess.Popen(command, stdout=subprocess.PIPE, 
                                    shell=True, preexec_fn=os.setsid)
            
        # Make the main window opaque
        
        # New window for the detection
        detectWin = visual.Window(size=[500, 500], pos=(150, 150), monitor=my_monitor, fullscr=False, color='black', allowGUI=True, title='SW selection')
        detectText = visual.TextStim(detectWin, text='Automatic SW Detection', pos=(0, .8), height=0.12, color='cyan', font='Night Sky', autoDraw=True)
        detectSubText = visual.TextStim(detectWin, text='Click on \'Start detect\' to begin.', pos=(0, .55), height=0.065, color='white', font='Nimbus Sans', autoDraw=True)
        startDetectText = visual.TextStim(detectWin, text='Starting the detection...', pos=(0, -.6), height=0.08, color='white', font='Nimbus Sans')
        
        selected_topo = 'cingulate'
        selected_peak = 'negative'
        
        # Topo selection buttons
        # selected_topo = 'cingulate'
        topoText = visual.TextStim(detectWin, text='Select the topographies:', pos=(0, .35), height=0.08, color='white', font='Nimbus Sans', autoDraw=True)
        topo1Label = visual.TextStim(detectWin, text='Cingulate', pos=(-.5, .2), height=0.075, font='Nimbus Sans', autoDraw=True)
        topo2Label = visual.TextStim(detectWin, text='Occipital', pos=(.5, .2), height=0.075, font='Nimbus Sans', autoDraw=True)
        topo1Button = visual.Circle(detectWin, radius=.05, pos=(-.5, .05), fillColor='green', autoDraw=True)
        topo2Button = visual.Circle(detectWin, radius=.05, pos=(.5, .05), fillColor='white', autoDraw=True)
            
        # Peak detection buttons
        peakText = visual.TextStim(detectWin, text='Select the peak type:', pos=(0, -.2), height=0.08, color='white', font='Nimbus Sans', autoDraw=True)
        peak1Label = visual.TextStim(detectWin, text='Negative', pos=(-.5, -.35), height=0.08, font='Nimbus Sans', autoDraw=True)
        peak2Label = visual.TextStim(detectWin, text='Positive', pos=(.5, -.35), height=0.08, font='Nimbus Sans', autoDraw=True)
        peak1Button = visual.Circle(detectWin, radius=.05, pos=(-.5, -.5), fillColor='green', autoDraw=True)
        peak2Button = visual.Circle(detectWin, radius=.05, pos=(.5, -.5), fillColor='white', autoDraw=True)
        
        # Start detection button
        detectButton = visual.Rect(detectWin, width=.5, height=.2, pos=(-.4, -.8), fillColor='green', autoDraw=True)
        detectButtonLabel = visual.TextStim(detectWin, text='Start detect', pos=(-.4, -.8), height=0.08, font='Nimbus Sans', autoDraw=True)
        
        # Stop detection button
        stopDetectButton = visual.Rect(detectWin, width=.5, height=.2, pos=(.4, -.8), fillColor='red', autoDraw=True)
        stopDetectButtonLabel = visual.TextStim(detectWin, text='Exit', pos=(.4, -.8), height=0.08, font='Nimbus Sans', autoDraw=True)
        
        detectWin.flip()
                
        # Reinitializing the stream makes you unsure about the devices
        not_really_sure_about_the_devices = True
        
        # Mouse
        detectMouse = event.Mouse(win=detectWin)
        while True:
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
                
                detectWin.flip()
                
                # Selcting templates
                if selected_peak == 'negative':
                    peak = 'neg'
                elif selected_peak == 'positive':
                    peak = 'pos'
                else:
                    raise ValueError('Peak type not recognized.')
                
                templates = all_templates.select_templates(roi=selected_topo, 
                                                           phase=peak, 
                                                           twin=(-.025, .0))
                
                # Initialize the detector
                sw_catcher = SWCatcher(sfreq=500, 
                                       stable_decrease_time=0.04, 
                                       stable_increase_time=0.02,
                                       neg_peaks_range=(-100e-6, -40e-6),
                                       pos_peaks_range=(5e-6, 40e-6),
                                       correlation_threshold=0.95,
                                       distance_threshold=0.05)
                # Set the templates
                sw_catcher.set_templates(templates)
                # Start the slow wave detection
                sw_catcher.start_sw_detection()
                
                # Initialize the stimulator
                stimulator = Stimulator(stim_file=stim_sound, alarm_file=alarm_sound, 
                    trig_codes=trig_codes)
                sound_dev = stimulator.get_devices()
                record_dev = stimulator.get_devices(capture_devices=True)
                
                # Select devices
                while not_really_sure_about_the_devices:
                    devsel = gui.Dlg(title='Select audio devices')
                    devsel.addField("Speakers device:", choices=sound_dev, 
                                    initial=cfg['DEVICES']['speakers'])
                    devsel.addField("Headphones device", choices=sound_dev, 
                                    initial=cfg['DEVICES']['headphones'])

                    params = devsel.show()

                    if devsel.OK:
                        spk, hdp = params.values()
                        not_really_sure_about_the_devices = False
                    else:
                        print("No way, you must select the devices. Make a wise choice.")
                
                stimulator.set_devices(speakers=spk, headphones=hdp)
                stimulator.start()
                
                startDetectText.text = 'Detection started'
                startDetectText.draw()
                detectWin.flip()
                
                # Timer for checking detection status
                check_detect = 60.
                checkpoint = time.time()
                
                # Timer for the interrupt
                interrupt_time = 5. # seconds
                timer_text = 'Alarm will play in:\n{0}'
                # Prepare interrupt stimulation window
                interruptWin = visual.Window(size=[300, 300], pos=(250, 250), monitor=my_monitor, fullscr=False, color='black', allowGUI=True, title='Be ready!')
                interruptText = visual.TextStim(interruptWin, text='Button will become green when a SW is detected.\nPress it within 5 seconds to stop stimulation.', pos=(0, .65), height=0.12, color='white', wrapWidth=1.5, font='Nimbus Sans', autoDraw=True)
                interruptButton = visual.Rect(interruptWin, width=1.85, height=1.2, pos=(0, -.35), fillColor='gray', autoDraw=True)
                interruptButtonLabel = visual.TextStim(interruptWin, text='Click to stop stimulation', pos=(0, -.35), height=0.28, color='white', wrapWidth=1.5, font='Nimbus Sans', autoDraw=True)
                interruptWin.flip()
                
                # Core of the closed loop
                stopstimMouse = event.Mouse(win=interruptWin)
                running = True
                while running:

                    cycle_time_start = time.perf_counter()
                    data = stream.get_data()
                    sw_catcher.set_data(data.copy().drop_sel({'channels': ['TRIG1']}).values)
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
                        interruptWin.flip()
                        stim_completed = True
                        stimtime = datetime.datetime.now().strftime("%H%M%S")
                        collect_data(data, stream, res, stimtime,
                                     op.join(participant_folder, 
                                             f'{pc_id}_{sesison}_{stimtime}.nc'))
                        # Interrupt the stimulation if the button is pressed
                        while time.perf_counter() - start_stim_time < interrupt_time:
                            # st = time.time()
                            # countdown = np.round(interrupt_time - (time.perf_counter() - start_stim_time), 3)
                            # interruptText.text = timer_text.format(countdown)
                            # interruptWin.flip()
                            # interruptText.draw()
                            
                            if stopstimMouse.isPressedIn(interruptButton):
                                while stopstimMouse.getPressed()[0]:  # Wait until the mouse button is released
                                    core.wait(0.0001)
                                stimulator.stop_stimulation()
                                stim_completed = False
                                break
                            # et = time.time()
                            # print('Time to draw:', et - st)
                            # high_precision_sleep(0.01)
                        interruptButton.fillColor = 'gray'
                        interruptText.text = 'Press the button within 5 seconds to stop stimulation.'
                        interruptWin.flip()
                        
                        # UCOMMENT ALL THIS BLOCK TO STOP THE DETECTION AFTER THE FIRST SW
                        # running = False
                        # # Stop stimulator
                        # stimulator.stop()
                        # interruptWin.close()
                        # # Stop detection
                        # sw_catcher.stop_sw_detection()
                        # startDetectText.text = 'Detection stopped'
                        # startDetectText.draw()
                        # # iter_draw(groupObjDetect)
                        # detectButton.fillColor = 'green'
                        # stopDetectButton.fillColor = 'red'
                        # stopDetectButtonLabel.text = 'Exit'
                        # detectWin.flip()
                        # high_precision_sleep(1.)
                        # if stim_completed:
                        #     # sart questionnatire
                        #     print('Questionnaire started')
                        #     dq = dreamquestrc(*(participant_info))
                        # break
                            
                                                            
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
                        detectButton.fillColor = 'green'
                        stopDetectButton.fillColor = 'red'
                        stopDetectButtonLabel.text = 'Exit'
                        detectWin.flip()
                        high_precision_sleep(1.)
                        break
                    
                    cycle_time_end = time.perf_counter()
                    print('Cycle time:', cycle_time_end - cycle_time_start)
            
            # Stop detection and close detection window
            elif detectMouse.isPressedIn(stopDetectButton):
                while detectMouse.getPressed()[0]:  # Wait until the mouse button is released
                    core.wait(0.0001)
                stopDetectButton.fillColor = 'gray'
                startDetectText.text = 'Exit detection'
                startDetectText.draw()
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
