import configparser
import os
from pathlib import Path
import closedloop_lsl

# Define the path to the configuration file
CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.cfg')
PARENT_PKG_DIR = Path(closedloop_lsl.PACKAGE_DIR).parent.absolute()

def write_config(paths={}, devices={}, others={}):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'LogLevel': 'INFO',
                        'FontsPath': f'{PARENT_PKG_DIR}/fonts',
                        'DataPath': f'{PARENT_PKG_DIR}/data',
                        'SoundsPath': f'{PARENT_PKG_DIR}/data/sounds',
                        'TemplatesPath': f'{PARENT_PKG_DIR}/data/topographies',
                        }
    config['PATHS'] = paths
    config['DEVICES'] = devices
    config['OTHERS'] = others
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def read_config():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)
    return config


if __name__ == '__main__':
    paths = {'ResultsPath': '/home/jerry/closedloop_results'}
    devices = {'Headphones': 'Family 17h (Models 10h-1fh) HD Audio Controller Stereo analogico',
               'Speakers': 'Family 17h (Models 10h-1fh) HD Audio Controller Stereo analogico',
               'PlayRecDev': 'HD-Audio Generic: ALC285 Analog (hw:2,0)',
               'SerialPort': '/dev/ttyUSB0'}
    write_config(paths=paths, devices=devices)
    config = read_config()
    print(config)
