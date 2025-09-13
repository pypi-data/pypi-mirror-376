"""Handles received message validation"""
from .consts import ETH_ANSWER_NOQUEUE


class SerialError(Exception):
    """Exception raised when there's a problem with serial."""


class SerialErrCheckSum(SerialError):
    """Exception raised when there'a problem with checksum."""


class SerialErrPckgLen(SerialError):
    """Exception raised when there'a problem with package length."""


class SerialForbidden(SerialError):
    """Exception raised when a given operation is not permitted by the UDC"""


class SerialInvalidCmd(SerialError):
    """Exception raised when the supplied command is invalid"""


SERIAL_ERROR = [
    "Ok",
    "Power supply in local mode",
    "Power supply in PC host mode",
    "Power supply interlocked",
    "UDC stuck",
    "DSP timeout",
    "DSP busy",
    "Resource is busy",
    "Invalid command",
]

ERROR_RESPONSE = {
    0xE1: "Malformed message",
    0xE2: "Operation not supported",
    0xE3: "Invalid ID",
    0xE4: "Invalid value",
    0xE5: "Invalid payload size",
    0xE6: "Read-only",
    0xE7: "Insufficient memory",
    0xE8: "Resource busy",
}


def validate(func):
    """Validates message and raises errors if invalid. In case given size is 0, any size is accepted."""

    def wrapper(*args, **kwargs):
        reply = func(*args, **kwargs)
        if len(reply) == 0 or (len(reply) == 1 and reply[0] == ETH_ANSWER_NOQUEUE):
            args[0].reset_input_buffer()
            raise SerialErrPckgLen(
                "Received empty response, check if the controller is on and connected. If you receive garbled output, try disconnecting and reconnecting."
            )

        reply = reply[1:] if len(reply) - 1 == args[2] or not args[2] else reply
        check_serial_error(reply)

        if args[2] and (
            len(reply) != args[2] or (len(reply) - 1 != args[2] and reply[0] == 0x21)
        ):
            offset = 1 if reply[0] == 0x21 else 0
            if len(reply) > 5:
                check_serial_error(reply[offset:])

            args[0].reset_input_buffer()
            raise SerialErrPckgLen(
                f"Expected {args[2]} bytes, received {len(reply) - offset} bytes"
            )

        if sum(reply) % 256 != 0:
            args[0].reset_input_buffer()
            raise SerialErrCheckSum(
                f"Expected {256 - sum(reply[2:-1])%256} as checksum, received {reply[-1]}"
            )

        return reply

    return wrapper


def print_deprecated(func):
    def wrapper(*args, **kwargs):
        """warn(
            "From 2.0.0, most functions will not loop implicitly. Use a 'for' or 'while' loop instead"
        )"""
        return func(*args, **kwargs)

    return wrapper


def check_serial_error(reply: bytes):
    error_index = 2 if reply[0] == 0x21 else 1
    if reply[error_index] == 0x53:
        if reply[-2] == 4:
            raise SerialForbidden(
                "Command blocked by UDC, unlock with unlock_udc() first"
            )
        if reply[-2] == 8:
            raise SerialInvalidCmd
        raise SerialError(SERIAL_ERROR[reply[-2]])

    if reply[error_index] in ERROR_RESPONSE:
        raise SerialInvalidCmd(ERROR_RESPONSE[reply[error_index]])
