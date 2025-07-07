from setuptools import setup
import sys

sys.setrecursionlimit(5000)

APP = ['pyqt_app.py']
DATA_FILES = []
OPTIONS = {
    # 'argv_emulation': True, <- ?trying to load old Carbon framework
    'packages': ['PyQt5', 'ebooklib', 'bs4', 'kokoro', 'soundfile', 'PyPDF2', 'jaraco.text'],
    'includes': ['merge_audio', 'timers'],
    # 'iconfile': 'youricon.icns',  # Optional: path to your app icon
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
) 