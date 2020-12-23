"""
Raspberry Pi execution file.
"""
import os
import sys

# Make sure a local raspberry-pi package can be found and overrides any installed versions
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from raspberry_pi.data_manager import DataManager  # pylint: disable = wrong-import-position
from raspberry_pi.server import Server  # pylint: disable = wrong-import-position

if __name__ == '__main__':
    dm = DataManager()
    server = Server(dm)
    server.start()
