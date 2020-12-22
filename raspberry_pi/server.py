"""
Implementation of a socket-based and serial-based server, to exchange data with surface and the Arduino-s.
"""
import time
from typing import Tuple, Optional, Set
from socket import socket, SHUT_RDWR, error as socket_error
from threading import Thread
import msgpack
from msgpack import UnpackException
from .data_manager import DataManager
from .constants import CONNECTION_IP, CONNECTION_PORT, CONNECTION_DATA_SIZE, CONNECTION_CHECK_DELAY, ARDUINO_PORTS
from .arduino import Arduino
from .utils import logger
from .enums import Device


class Server:
    """
    Communicate with all components (hence heart of the ROV).

    Threaded networking functionality is exposed by the `start` function, and allows handling data in a relatively fast
    manner, while keeping a low level of code (and concurrency) complexity.
    """

    def __init__(self, dm: DataManager):
        self._dm = dm
        self._surface_connection = _SurfaceConnection(self._dm)
        self._arduino_connections = _ArduinoConnections(self._dm)

    def _surface_thread(self):
        """
        Communicate with surface.
        """
        while True:
            self._surface_connection.accept()
            while self._surface_connection.connected:
                time.sleep(CONNECTION_CHECK_DELAY)
            self._surface_connection.cleanup()

    @staticmethod
    def _arduino_thread(arduino: Arduino):
        """
        Communicate with an arduino.
        """
        arduino.connect()
        while True:
            while arduino.connected:
                time.sleep(CONNECTION_CHECK_DELAY)
            arduino.reconnect()

    def start(self):
        """
        Start communicating with high-level and low-level ROV components.

        Threads are created for each communication channel - one for surface and several for arduino-s
        """
        Thread(name="Surface connection", target=self._surface_thread).start()

        for arduino in self._arduino_connections.arduinos:
            Thread(
                name=" ".join(("Arduino", "connection", "-", str(arduino))),
                target=self._arduino_thread,
                args=(arduino,)
            ).start()


class _SurfaceConnection:
    """
    Communicate with Surface by establishing a 2-way data exchange via a TCP network.

    A surface connection is a non-enforced singleton featuring the following functionalities:

        - accept an incoming client connection (blocking)
        - check if connected by inspecting whether the communication process is running
        - communicate with the client in a non-blocking manner
        - clean up resources

    Ensuring the server runs correctly should be verified by the calling code.
    """

    def __init__(self, dm: DataManager):
        self._dm = dm
        self._ip = CONNECTION_IP
        self._data_size = CONNECTION_DATA_SIZE
        self._port = CONNECTION_PORT
        self._address = self._ip, self._port
        self._socket = self._new_socket()
        self._communication_thread = self._new_thread()
        self._client_socket: Optional[socket] = None
        self._client_address: Optional[Tuple] = None

    @property
    def connected(self) -> bool:
        """
        Check if the communication with surface is still happening.
        """
        return self._communication_thread.is_alive()

    def _new_socket(self) -> socket:
        """
        Create and configure a new TCP socket.
        """
        server_socket = socket()

        try:
            server_socket.bind(self._address)
        except socket_error:
            logger.exception(f"Failed to bind socket to {self._ip}:{self._port}")

        server_socket.listen(1)
        return server_socket

    def _new_thread(self) -> Thread:
        """
        Create a new communication thread.
        """
        return Thread(target=self._communicate)

    def accept(self):
        """
        Accept incoming connections from surface.

        On errors, the cleanup function is called.
        """
        try:
            logger.info(f"{self._socket.getsockname()} is waiting for a client to connect")

            # Wait for a connection (accept function blocks the program until a client connects to the server)
            self._client_socket, self._client_address = self._socket.accept()

            # Once the client is connected, start the data exchange process
            logger.info(f"Client with address {self._client_address} connected")
            self._communication_thread.start()  # TODO: Need this as a thread? Test plz

        except OSError:
            logger.exception("Failed to listen to incoming connections")
            self.cleanup()

    def _communicate(self):
        """
        Exchange the data with surface.

        Breaks the infinite loop on errors, leaving the calling code to accommodate for that.
        """
        while True:
            try:
                data = self._client_socket.recv(self._data_size)

                # Stop the communication process on the connection closed message
                if not data:
                    logger.info("Connection closed by client")
                    break

                try:
                    data = msgpack.unpackb(data.decode("utf-8").strip())
                except (UnicodeError, UnpackException):
                    logger.warning(f"Failed to decode the following data: {data}")

                # Only handle valid, non-empty data
                if data and isinstance(data, dict):
                    self._dm.set(Device.SURFACE, **data)

                # Fetch data to send and transfer it to surface
                data = self._dm.get(Device.SURFACE)
                self._client_socket.sendall(msgpack.packb(data))

            except OSError:
                logger.exception("An error occurred while communicating with the client")
                break

    def cleanup(self):
        """
        Cleanup server-related objects.
        """
        try:
            self._dm.set(Device.SURFACE, set_default=True)
            self._communication_thread = self._new_thread()
            self._client_socket.shutdown(SHUT_RDWR)
            self._client_socket.close()
        except OSError:
            logger.exception("Ignoring an error in the cleanup function")


class _ArduinoConnections:
    """
    Communicate with each Arduino by establishing a 2-way data exchange via a serial network.

    This class creates relevant Arduino instances and allows accessing them via a getter. The calling code must handle
    keeping the networking flow running.
    """

    def __init__(self, dm: DataManager):
        self._dm = dm
        self._arduinos = {self._new_arduino(port) for port in ARDUINO_PORTS}

    @property
    def arduinos(self) -> Set[Arduino]:
        """
        Getter for the collection of Arduino instances.
        """
        return self._arduinos

    def _new_arduino(self, port: str) -> Arduino:
        """
        Instantiate an Arduino.
        """
        return Arduino(self._dm, port)
