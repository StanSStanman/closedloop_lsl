DESCRIPTION = "ClosedLoop system for automatic slow-waves targeting"
LONG_DESCRIPTION = """"""

DISTNAME = "closedloop_lsl"
MAINTAINER = "Ruggero Basanisi"
MAINTAINER_EMAIL = "ruggero.basanisi@imtlucca.it"
URL = "https://github.com/StanSStanman/closedloop_lsl"
LICENSE = "The Unlicense"
DOWNLOAD_URL = "https://github.com/StanSStanman/closedloop_lsl"
VERSION = "0.0.1"
PACKAGE_DATA = {}

INSTALL_REQUIRES = [
    "numpy",
    "scipy",
    "xarray",
    "matplotlib",
    "mne_lsl",
    "numba",
    "joblib",
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
