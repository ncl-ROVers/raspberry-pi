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
    ARDUINO_A = "A_A"
    ARDUINO_B = "A_B"
