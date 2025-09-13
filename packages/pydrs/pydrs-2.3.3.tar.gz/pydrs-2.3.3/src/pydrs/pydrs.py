"""Communication overload types"""
import re
import socket
import struct
import typing

import serial

from .base import BaseDRS
from .consts import ETH_ANSWER_ERR, ETH_CMD_REQUEST, ETH_RESET_CMD, ETH_CMD_WRITE, common
from .utils import checksum, get_logger, index_to_hex
from .validation import SerialErrPckgLen, validate




logger = get_logger(name=__file__)


class SerialDRS(BaseDRS):
    """DRS communication through serial ports"""

    def __init__(self, port: str, baud: int = 115200):
        super().__init__()
        self.ser: typing.Optional[serial.Serial] = None

        self.connect(port, baud)

    def _transfer_write(self, msg: str):
        full_msg = (self._slave_addr + msg).encode("ISO-8859-1")
        self.ser.write(checksum(full_msg))

    @validate
    def _transfer(self, msg: str, size: int) -> bytes:
        self._transfer_write(msg)
        return self.ser.read(size)

    def reset_input_buffer(self):
        self.ser.reset_input_buffer()

    @property
    def timeout(self) -> float:
        return self.ser.timeout

    @timeout.setter
    def timeout(self, new_timeout):
        self.ser.timeout = new_timeout

    def is_open(self) -> bool:
        return self.ser.isOpen()

    def connect(self, port: str = "COM2", baud: int = 115200):
        if self.ser and self.ser.is_open:
            logger.warning(
                "PyDRS obj {} serial port {} is already open. Disconnect before opening a new connection.".format(
                    self, self.ser
                )
            )
            return False
        try:
            self.ser = serial.Serial(
                port, baud, timeout=1
            )  # port format should be 'COM'+number
            return True
        except Exception:
            logger.exception("Failed to open serial port ({}, {})".format(port, baud))
            return False

    def disconnect(self):
        if not self.ser or not self.ser.is_open:
            return True

        try:
            self.ser.close()
            return True
        except Exception:
            logger.exception("Failed to disconnect serial port ({})".format(self.ser))
            return False


class EthDRS(BaseDRS):
    """DRS communication through TCP/IP"""

    def __init__(self, address: str, port: int = 5000):
        super().__init__()
        self._serial_timeout = 50
        self.connect(address, port)

    def _format_message(self, msg: bytes, msg_type: bytes) -> bytes:
        if (msg_type == ETH_CMD_WRITE):
            if (msg[4] == common.functions.index("reset_udc")): # Do not wait for a reply
                msg = msg_type + b'\x00' + struct.Struct(">f").pack(0.0) + msg
            else:
                msg = msg_type + b'\x00' + struct.Struct(">f").pack(self._serial_timeout) + msg
        else:
            msg = msg_type + b'\x00' + struct.Struct(">f").pack(self._serial_timeout) + msg

        return msg[0:2] + struct.pack(">I", (len(msg) - 2)) + msg[2:]

    def reset_input_buffer(self):
        self.socket.sendall(ETH_RESET_CMD)
        #self.socket.recv(16)

    @staticmethod
    def _parse_reply_size(reply: bytes) -> int:
        return struct.unpack(">I", reply[2:])[0]

    def _get_reply(self, _: int = None) -> bytes:
        data_size = self._parse_reply_size(self.socket.recv(6))
        payload = b""

        for _ in range(int(data_size / 4096)):
            payload += self.socket.recv(4096)

        payload += self.socket.recv(int(data_size % 4096))

        try:
            if payload[0] == ETH_ANSWER_ERR:
                raise TimeoutError("Server timed out waiting for serial response")
        except IndexError:
            self.reset_input_buffer()
            raise SerialErrPckgLen(
                "Received empty response, check if the controller is on and connected. If you receive garbled output, try disconnecting and reconnecting."
            )

        return payload

    @validate
    def _transfer(self, msg: str, size: int) -> bytes:
        base_msg = (self._slave_addr + msg).encode("ISO-8859-1")
        full_msg = self._format_message(checksum(base_msg), ETH_CMD_REQUEST)
        self.socket.sendall(full_msg)
        return self._get_reply(size)

    def _transfer_write(self, msg: str):
        base_msg = (self._slave_addr + msg).encode("ISO-8859-1")
        full_msg = self._format_message(checksum(base_msg), ETH_CMD_WRITE)
        self.socket.sendall(full_msg)
        try:
            self._get_reply()
            return
        except SerialErrPckgLen:
            pass

    @property
    def timeout(self) -> float:
        return self.socket.timeout

    @timeout.setter
    def timeout(self, new_timeout: float):
        self._serial_timeout = new_timeout * 1000
        self.socket.settimeout(new_timeout)

    def is_open(self) -> bool:
        raise NotImplementedError

    def connect(self, address: str = "127.0.0.1", port: int = 5000):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)

        self.socket.connect((address, port))
        self.socket.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)

    def disconnect(self):
        self.socket.close()


def GenericDRS(com_or_address: str, port_or_baud: int):
    """Factory for DRS communication classes"""
    if re.match(r"(([0-9]{1,3}\.){3}[0-9]{1,3})", com_or_address):
        return EthDRS(com_or_address, port_or_baud)

    return SerialDRS(com_or_address, port_or_baud)
