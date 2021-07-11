"""
Data manager handling access to Arduino and Surface specific values.
"""
from .enums import Device
from .constants import DEFAULTS, RAMP_KEYS, RAMP_RATE
from .utils import logger


class DataManager:
    """
    Data manager with access to the internal per-device-dictionaries.

    Provides getter and setter methods to each dictionary.

    To use it, you should import the module and create the data manager:

        from .data_manager import DataManager
        dm = DataManager()

    You must then pass a reference to the manager to other parts of the code:

        def func(dm: DataManager):
            dm.set(Device.SURFACE, test=5)
            print(dm.get(Device.ARDUINO_O))
    """

    def __init__(self):
        """
        Create a data dictionary for each device connected to the server.

        The data represents values to send to the device it is registered under.
        """
        self._data = {
            Device.SURFACE: DEFAULTS[Device.SURFACE].copy(),
            Device.ARDUINO_A: DEFAULTS[Device.ARDUINO_A].copy(),
            Device.ARDUINO_B: DEFAULTS[Device.ARDUINO_B].copy()
        }

    def get(self, device: Device, *args) -> dict:
        """
        Access stored values.

        Returns selected data or full dictionary if no args passed.
        """
        if not args:
            return self._data[device].copy()

        # Raise error early if any of the keys are not registered
        if not set(args).issubset(set(self._data[device].keys())):
            raise KeyError(f"{set(args)} is not a subset of {set(self._data[device].keys())}")

        return {key: self._data[device][key] for key in args}

    def set(self, from_device: Device, set_default: bool = False, **kwargs):
        """
        Modify stored values.

        If the values are coming from surface, they are dispatched into separated dictionaries, specific to each
        Arduino. Otherwise, the values from the Arduino override specific values in the surface transmission data.

        Keep in mind that if the keys received are within the RAMP_KEYS constant, the values will not be changed to the
        target values, but will instead be modified by a small value (every time).

        `set_default` argument is treated with a priority, and if set to True the data is replaced with default values
        immediately, ignoring kwargs and simply setting all values possible to default (surface only).
        """
        if set_default:
            logger.info(f"Setting the values for device {from_device.name} to default")

        # Surface will dispatch the values to different dictionaries
        if from_device == Device.SURFACE:

            # Override each Arduino dictionary with the defaults if the `set_default` flag is set
            if set_default:
                self._data[Device.ARDUINO_A] = DEFAULTS[Device.ARDUINO_A]
                self._data[Device.ARDUINO_B] = DEFAULTS[Device.ARDUINO_B]
            else:
                for key, value in kwargs.items():
                    if key in self._data[Device.ARDUINO_A]:
                        self._handle_data_from_surface(Device.ARDUINO_A, key, value)
                    elif key in self._data[Device.ARDUINO_B]:
                        self._handle_data_from_surface(Device.ARDUINO_B, key, value)
                    else:
                        raise KeyError(f"Couldn't find key {key} in any of the Arduino dictionaries")

        # Arduino-s will simply override relevant values in the surface dictionary
        else:
            if set_default:
                raise KeyError(f"Setting the default values is only supported for surface, not {from_device.name}")

            if not set(kwargs.keys()).issubset(set(self._data[Device.SURFACE].keys())):
                raise KeyError(f"{set(kwargs.keys())} is not a subset of {set(self._data[Device.SURFACE].keys())}")

            for key, value in kwargs.items():
                self._data[Device.SURFACE][key] = value

    def _handle_data_from_surface(self, device: Device, key: str, value: int):
        """
        Ramp up/down a specific value within an Arduino dictionary, or set it to a specific value.
        """
        if key in RAMP_KEYS:
            difference = self._data[device][key] - value

            if difference > 0:
                self._data[device][key] -= RAMP_RATE
            elif difference < 0:
                self._data[device][key] += RAMP_RATE

        else:
            self._data[device][key] = value
