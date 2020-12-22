"""
Representation of an Arduino, including relevant networking functionalities.
"""
from threading import Thread
import msgpack
from msgpack import UnpackException
from serial import Serial, SerialException
from .data_manager import DataManager
from .constants import SERIAL_BAUDRATE, SERIAL_READ_TIMEOUT, SERIAL_WRITE_TIMEOUT
from .enums import Device
from .utils import logger


class Arduino:
    """
    Handle serial communication between the ROV and an Arduino.

    The Arduino-s are created via server, and can be accessed in the following way:

        arduinos = server.arduinos

    While working, the code should check if the communication is happening, to detect when it stops:

        if not arduino.connected():
            arduino.reconnect()

    You can check __main__.py to see how the surface-rov and rov-arduino(s) connections are kept alive.
    """

    def __init__(self, dm: DataManager, port: str):
        """
        Initialise the serial object and the thread.

        At first, the device is not identified (it's unassigned), and will be known after the pre-communication process.
        """
        self._dm = dm
        self._port = port
        self._device = Device.UNASSIGNED
        self._communication_thread = self._new_thread()
        self._serial = Serial(baudrate=SERIAL_BAUDRATE)
        self._serial.port = self._port
        self._serial.write_timeout = SERIAL_WRITE_TIMEOUT
        self._serial.timeout = SERIAL_READ_TIMEOUT

    def __str__(self):
        return self._port

    @property
    def connected(self) -> bool:
        """
        Check if the communication is happening.
        """
        return self._communication_thread.is_alive()

    def _new_thread(self) -> Thread:
        """
        Create the communication thread.
        """
        return Thread(target=self._communicate)

    def connect(self):
        """
        Connect to the Arduino and start exchanging the data.

        Opens a serial connection and starts the communication thread.
        """
        if self.connected:
            logger.error(f"Can't connect - already connected to {self._port}")
            return

        logger.info(f"Connecting to {self._port}")
        while True:
            try:
                if not self._serial.is_open:
                    self._serial.open()
                    break
            except SerialException as ex:
                logger.debug(f"Failed to connect to {self._port} - {ex}")

        logger.info(f"Connected to {self._port}")
        self._communication_thread.start()

    def _communicate(self):
        """
        Exchange the data with the Arduino.

        Pre-communicates at first, to identify the device and set relevant ID, while ignoring empty data. Starts
        exchanging information properly immediately after.
        """
        while True:
            try:
                data = self._serial.read_until().strip()
                if not data:
                    continue

                try:
                    self._device = Device(msgpack.unpackb(data.decode("utf-8"))["ID"])
                except (UnicodeError, UnpackException):
                    logger.exception(f"Failed to decode the following data in pre-communication: {data}")
                    return

                # Knowing the id, set the connection status to connected (True) and exit the pre-communication step
                logger.info(f"Detected a valid device at {self._port} - {self._device.name}")
                self._dm.set(self._device, **{self._device.value: True})
                break

            except SerialException:
                logger.exception(f"Lost connection to {self._port}")
                return

            except (KeyError, ValueError):
                logger.error(f"Invalid device ID received from {self._port}")
                return

        while True:
            try:
                if data:
                    logger.debug(f"Received data from {self._port} - {data}")

                    try:
                        data = msgpack.unpackb(data.decode("utf-8").strip())
                    except (UnicodeError, UnpackException):
                        logger.exception(f"Failed to decode following data: {data}")

                    # Remove ID from the data to avoid setting it upstream, disconnect in case of errors
                    if "ID" not in data or data["ID"] != self._device.value:
                        logger.error(f"ID key not in {data} or key doesn't match {self._device.value}")
                        break

                    del data["ID"]
                    self._dm.set(self._device, **data)

                else:
                    logger.debug(f"Timed out reading from {self._port}, clearing the buffer")
                    self._serial.reset_output_buffer()

                # Send data and wait for a response from Arduino (next set of data to process)
                self._serial.write(bytes(msgpack.packb(self._dm.get(self._device)) + "\n"))
                data = self._serial.read_until().strip()

            except SerialException:
                logger.error(f"Lost connection to {self._port}")
                break

    def disconnect(self):
        """
        Disconnect from the Arduino and stop exchanging the data.
        """
        try:
            if self._serial.is_open:
                self._serial.close()
        except SerialException:
            logger.exception(f"Failed to safely disconnect from {self._port}")

        # Clean up the communication thread
        self._communication_thread = self._new_thread()

        # Set the connection status to disconnected, if the id was known
        if self._device != Device.UNASSIGNED:
            self._dm.set(self._device, **{self._device.value: False})

        # Forget the device id
        self._device = Device.UNASSIGNED

    def reconnect(self):
        """
        Reconnect to the Arduino.
        """
        self.disconnect()
        self.connect()
