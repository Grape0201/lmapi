import struct


def hexstr2str(hexstring: str, encoding="utf-8", delim=True) -> str:
    if delim:
        while hexstring[-2:] == "00":
            hexstring = hexstring[:-2]
    return bytes.fromhex(hexstring).decode(encoding)


def hexstr2int(hexstring: str) -> int:
    assert len(hexstring) % 2 == 0
    reversed = ""
    for i in range(len(hexstring)//2):
        reversed = hexstring[i*2:i*2+2] + reversed
    return int('0x'+reversed, base=16)


def hexstr2float(hexstring: str) -> float:
    assert len(hexstring) % 2 == 0
    reversed = ""
    for i in range(len(hexstring)//2):
        reversed = hexstring[i*2:i*2+2] + reversed
    return struct.unpack('!f', bytes.fromhex(reversed))[0]


def float2hexstr(f: float) -> str:
    return struct.pack('!f', f).hex()


def guid2xy(hexstring: str) -> tuple[int, int]:
    assert len(hexstring) == 6
    guid_bytes = [int('0x'+hexstring[x*2:x*2+2], base=16) for x in range(3)]
    y4bits = [
        (guid_bytes[2] & 240) >> 4,
        (guid_bytes[0] & 240) >> 4,
        (guid_bytes[1] & 15),
        0,
    ]
    x4bits = [
        (guid_bytes[2] & 15),
        (guid_bytes[0] & 15),
        0,
        0,
    ]
    # print("x4bits", x4bits)
    # print("y4bits", y4bits)
    # print("guid bytes", guid_bytes)
    y = (y4bits[0]) | (y4bits[1] << 4) | (y4bits[2] << 8)
    x = (y & 1) + 2 * ((x4bits[0]) | (x4bits[1] << 4))
    x = x if 0 <= x <= 511 else -1
    y = y if 0 <= y <= 1023 else -1
    return (x, y)


def xy2guid(x: int, y: int) -> str:
    '''
    TODO
    struct IngameGUIDStruct
    {
        unsigned int unused1 : 8;
        unsigned int x1 : 4;
        unsigned int y1 : 4;
        unsigned int y2 : 4;
        unsigned int unused2 : 4;
        unsigned int x0 : 4;
        unsigned int y0 : 4;
    };
    '''
    y4bits = [
        y >> 0 & 15,
        y >> 4 & 15,
        y >> 8 & 15,
        0
    ]
    x4bits = [
        x >> 1 & 15,
        x >> 5 & 15,
        x >> 9 & 15,
        0
    ]
    guid_bytes = [
        0,
        y4bits[1]*2**4+x4bits[1],  # wrong
        y4bits[2],
        x4bits[0]
    ]
    print("x4bits", x4bits)
    print("y4bits", y4bits)
    print("guid bytes", guid_bytes)
    guid = ""
    for b in guid_bytes:
        guid += '{:02x}'.format(b)
    return guid


if __name__ == "__main__":
    import sys
    x, y = guid2xy(sys.argv[1])
    print(f"x={x}, y={y}")
