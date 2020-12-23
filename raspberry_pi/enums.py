"""
Enumerations.
"""
from enum import Enum


class Device(Enum):
    """
    Available devices.

    A device must be the surface control station or an Arduino, otherwise it's' unassigned (unknown) and must be
    identified first.
    """

    UNASSIGNED = "UNASSIGNED"
    SURFACE = "S"
    ARDUINO_O = "A_O"
    ARDUINO_I = "A_I"
