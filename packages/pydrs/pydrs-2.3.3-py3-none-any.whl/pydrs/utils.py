"""Utility functions"""
import logging as _logging
import struct
import typing as _typing


def get_logger(
    name=__file__,
    level: int = _logging.INFO,
    handlers: _typing.Optional[_typing.List[_logging.Handler]] = None,
) -> _logging.Logger:
    """Returns a logger object"""

    logger = _logging.getLogger(name)

    if not logger.handlers and not handlers:
        formatter = _logging.Formatter(
            "[%(asctime)s %(levelname)s %(filename)s:%(lineno)s - %(funcName)s] %(message)s"
        )
        logger.setLevel(level)
        console = _logging.StreamHandler()
        console.setFormatter(formatter)
        logger.addHandler(console)
    return logger


def float_to_hex(value: float):
    hex_value = struct.pack("f", value)
    return hex_value.decode("ISO-8859-1")


def float_list_to_hex(value_list: list):
    hex_list = b""
    for value in value_list:
        hex_list = hex_list + struct.pack("f", value)
    return hex_list.decode("ISO-8859-1")


def format_list_size(in_list: list, max_size: int):
    out_list = in_list[0:max_size]
    if max_size > len(in_list):
        for _ in range(max_size - len(in_list)):
            out_list.append(0)
    return out_list


def double_to_hex(value: int):
    hex_value = struct.pack("H", value)
    return hex_value.decode("ISO-8859-1")


def uint32_to_hex(value: int):
    hex_value = struct.pack("I", value)
    return hex_value.decode("ISO-8859-1")


def index_to_hex(value: int):
    hex_value = struct.pack("B", value)
    return hex_value.decode("ISO-8859-1")


def size_to_hex(value: int):
    hex_value = struct.pack(">H", value)
    return hex_value.decode("ISO-8859-1")


def checksum(packet: bytes) -> bytes:
    csum = (256 - sum(packet)) % 256
    return packet + bytes([csum])


def prettier_print(var_input: dict, prefix: str = ""):
    for key, value in var_input.items():
        if isinstance(value, dict):
            prettier_print(value, "".join([prefix, key.replace("_", " ").upper(), " "]))
        else:
            key_words = key.split("_")

            for i in range(0, len(key_words)):
                key_words[i] = (
                    key_words[i].upper()
                    if key_words[i] in ["igbt", "dc", "iib", "ps", "ip", "idb"]
                    else key_words[i].capitalize()
                )
            print(f"{prefix}{' '.join(key_words)}: {value}")
