"""
Constants and other static values.
"""
import os
import dotenv
from .enums import Device

# Declare paths to relevant folders - tests folder shouldn't be known here
ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
RASPBERRY_PI_DIR = os.path.join(ROOT_DIR, "raspberry_pi")
RES_DIR = os.path.join(RASPBERRY_PI_DIR, "res")
LOG_DIR = os.path.join(RASPBERRY_PI_DIR, "log")

# Load the environment variables from the root folder and/or the resources folder
dotenv.load_dotenv(dotenv_path=os.path.join(ROOT_DIR, ".env"))
dotenv.load_dotenv(dotenv_path=os.path.join(RES_DIR, ".env"))

# Declare logging config
LOG_CONFIG_PATH = os.getenv("LOG_CONFIG_PATH", os.path.join(RES_DIR, "log-config.json"))
LOGGER_NAME = os.getenv("LOGGER_NAME", "raspberry-pi")

# Declare surface connection information
CONNECTION_IP = os.getenv("CONNECTION_IP", "0.0.0.0")
CONNECTION_PORT = int(os.getenv("CONNECTION_PORT", "50000"))
CONNECTION_DATA_SIZE = int(os.getenv("CONNECTION_DATA_SIZE", "4096"))

# Declare Arduino-related constants (timeouts in seconds)
ARDUINO_PORTS = tuple(port for port in os.getenv("ARDUINO_PORTS", "").split(",") if port)
SERIAL_WRITE_TIMEOUT = int(os.getenv("SERIAL_WRITE_TIMEOUT", "1"))
SERIAL_READ_TIMEOUT = int(os.getenv("SERIAL_READ_TIMEOUT", "1"))
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", "115200"))

# Declare the constant to determine how often should the connection statuses be checked (in seconds)
CONNECTION_CHECK_DELAY = int(os.getenv("CONNECTION_CHECK_DELAY", "1"))

# Declare constant for slowly changing up all values and keys affected
RAMP_RATE = 2
RAMP_KEYS = {
    "T_HFP",
    "T_HFS",
    "T_HAP",
    "T_HAS",
    "T_VFP",
    "T_VFS",
    "T_VAP",
    "T_VAS",
    "T_M"
}


# Declare the transmission sets with the default values as initial values
THRUSTER_IDLE = 1500
GRIPPER_IDLE = 1500
CORD_IDLE = 1500
DEFAULTS = {
    Device.SURFACE: {
        "A_A": False,
        "A_B": False,
        "S_A": 0,
        "S_B": 0
    },
    Device.ARDUINO_A: {
        "T_HFP": THRUSTER_IDLE,
        "T_HFS": THRUSTER_IDLE,
        "T_HAP": THRUSTER_IDLE,
        "T_HAS": THRUSTER_IDLE,
        "T_VFP": THRUSTER_IDLE,
        "T_VFS": THRUSTER_IDLE,
        "T_VAP": THRUSTER_IDLE,
        "T_VAS": THRUSTER_IDLE,
    },
    Device.ARDUINO_B: {
        "T_M": THRUSTER_IDLE,
        "M_G": GRIPPER_IDLE,
        "M_C": CORD_IDLE
    }
}
