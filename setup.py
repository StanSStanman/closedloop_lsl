DESCRIPTION = "ClosedLoop system for automatic slow-waves targeting"
LONG_DESCRIPTION = """"""

DISTNAME = "closedloop_lsl"
MAINTAINER = "Ruggero Basanisi"
MAINTAINER_EMAIL = "ruggero.basanisi@imtlucca.it"
URL = "https://github.com/StanSStanman/closedloop_lsl"
LICENSE = "The Unlicense"
DOWNLOAD_URL = "https://github.com/StanSStanman/closedloop_lsl"
VERSION = "0.0.2"
PACKAGE_DATA = {}

INSTALL_REQUIRES = [
    "numpy",
    "scipy",
    "matplotlib",
    "numba",
    "pyserial==3.5",
    "xarray==2025.1.2",
    "mne_lsl==1.8.0",
    "pandas==2.2.3",
    "h5py==3.12.1",
    "netCDF4==1.7.2",
    "pygame==2.6.1",
    "sounddevice==0.5.1"
]

PACKAGES = []

CLASSIFIERS = []

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if __name__ == "__main__":
    setup(
        name=DISTNAME,
        author=MAINTAINER,
        author_email=MAINTAINER_EMAIL,
        maintainer=MAINTAINER,
        maintainer_email=MAINTAINER_EMAIL,
        description=DESCRIPTION,
        long_description=LONG_DESCRIPTION,
        license=LICENSE,
        url=URL,
        version=VERSION,
        download_url=DOWNLOAD_URL,
        install_requires=INSTALL_REQUIRES,
        include_package_data=True,
        packages=PACKAGES,
        package_data=PACKAGE_DATA,
        classifiers=CLASSIFIERS,
    )
