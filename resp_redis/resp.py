from typing import Optional, Union
from typing import Union, Optional, Tuple

def decode_one(data: bytes) -> Tuple[Union[str, int, list], int, Optional[Exception]]:
    if not data:
        raise ValueError("data is empty")
    first = data[0]

    if first == ord('+'):
        return read_simple_string(data)
    elif first == ord('-'):
        return read_error(data)
    elif first == ord(':'):
        return read_int64(data)
    elif first == ord('$'):
        return read_bulk_string(data)
    elif first == ord('*'):
        return read_array(data)
    else:
        raise ValueError(f"Unknown RESP type: {chr(first)}")

    

def read_length(data: bytes) -> Tuple[int, int]:

    pos, length = 0, 0

    while pos < len(data):
        
        b = data[pos]

        if not (b >= ord('0') and b <= ord('9')):
            return length, pos + 2

        length = length * 10 + (b - ord('0'))
        pos += 1

    return 0, 0




def read_simple_string(data: bytes) -> Tuple[str, int, Optional[Exception]]:
    pos = 1
    while data[pos] != ord('\r'):
        pos += 1
    result = data[1:pos].decode('utf-8')
    return result, pos + 2, None


def read_error(data: bytes) -> Tuple[str, int, Optional[Exception]]:
    return read_simple_string(data)


def read_int64(data: bytes) -> Tuple[int, int, Optional[Exception]]:
    # first character should be ':'
    pos = 1
    value = 0

    while data[pos] != ord('\r'):
        value = value * 10 + (data[pos] - ord('0'))
        pos += 1

    return value, pos + 2, None


def read_bulk_string(data: bytes) -> Tuple[str, int, Optional[Exception]]:
    # first character should be '$'
    pos = 1

    # read the length
    length, delta = read_length(data[pos:])
    pos += delta

    # extract the string of given length
    result = data[pos:pos + length].decode("utf-8")

    return result, pos + length + 2, None

def read_array(data: bytes) -> Tuple[list, int, Optional[Exception]]:
    # first character should be '*'
    pos = 1

    # read the length of the array
    count, delta = read_length(data[pos:])
    pos += delta

    elems = []
    for _ in range(count):
        elem, delta, err = decode_one(data[pos:])
        if err is not None:
            return None, 0, err
        elems.append(elem)
        pos += delta

    return elems, pos, None


def decode(data: bytes) -> Tuple[Union[str, int, list], Optional[Exception]]:
    if not data:
        raise ValueError("data is empty")
    value, _, err = decode_one(data)
    return value, err

def decode_array_string(data: bytes) -> list[str]:
    value, err = decode(data)

    if err:
        raise err

    return [str(item) for item in value]


def encode(value: str, is_simple: bool) -> bytes:
    if is_simple:
        return f"+{value}\r\n".encode("utf-8")

    return f"${len(value)}\r\n{value}\r\n".encode("utf-8")
