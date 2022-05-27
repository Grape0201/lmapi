from typing import Callable
import sys
from scapy.all import sniff
from lmapi.pcapReader import (
    get_extracted_packet,
    read_packet
)
from lmapi.hex_funcs import hexstr2int

d = ""


def pkt_handler(packet, codes, codestartswith, pfunc: Callable = None):
    global d
    _dd = get_extracted_packet(packet)
    if _dd is None:
        return
    dd, timestamp = _dd
    d += dd
    while True:
        if len(d) < 10:
            break
        __length = hexstr2int(d[:4])*2
        if len(d) >= __length:
            data = d[:__length]
            d = d[__length:]
        else:
            break

        result = None
        try:
            result = read_packet(data, codes, codestartswith)
        except NotImplementedError:
            pass
        if result:
            for r in result:
                if pfunc is None:
                    print(r)
                else:
                    pfunc(r)
        else:
            pass


def handler(packet):
    # code starts with "ac08": show map info
    # see lmapi/lmpacket.py
    pkt_handler(packet, [], ["ac08"])


sniff(
    offline=sys.stdin.buffer,
    prn=handler,
    store=0
)
