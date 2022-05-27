from dataclasses import asdict
from typing import Union
import logging
import binascii
import time
import os
from scapy.all import PcapReader
try:
    from rich.logging import RichHandler
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)],
    )
except ModuleNotFoundError:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(message)s",
        datefmt="[%X]",
    )
from .lmpacket import read_packet
from .lmdataclass import Gift, GiftPopup, Player
from .hex_funcs import hexstr2int

logger = logging.getLogger(__name__)


def get_extracted_packet(
        packet, scapy=True, ipaddrs=[]) -> Union[None, tuple[str, int]]:
    if scapy:
        return __get_extracted_packet_scapy(packet, ipaddrs)
    else:
        return __get_extracted_packet_pyshark(packet, ipaddrs)


def __get_extracted_packet_scapy(
        packet, ipaddrs: list[str]) -> Union[None, tuple[str, int]]:
    '''
    scapy専用
    --------------------------------
    ローモバの受信パケットだけを抽出したい。
    - TCPであることは確か
    - 送信IPは時々変わる
    - 送信ポートはTCP標準の5991で固定っぽい
    - 受信ポートは変わるっぽい
    '''
    if "IP" not in packet or 'TCP' not in packet:
        return None
    if ipaddrs:
        for iggip in ipaddrs:
            if packet['IP'].src == iggip:
                break
        else:
            return None
    if not packet['TCP'].payload:
        return None
    if packet['TCP'].sport != 5991:
        return None

    # if packet['TCP'].dport != 52804:
    #     return
    # print(packet.time, int(packet.time), type(packet.time))
    return packet['TCP'].payload.load.hex(), int(packet.time)


def __get_extracted_packet_pyshark(
        packet, ipaddrs: list[str]) -> Union[None, tuple[str, int]]:
    # packet: pyshark.packet.packet.Packet
    if not hasattr(packet, "tcp") or not hasattr(packet, "data"):
        return None
    if ipaddrs:
        for iggip in ipaddrs:
            if packet.ip.src == iggip:
                break
        else:
            return None
    if packet.tcp.srcport != "5991":
        return None
    return (
        binascii.unhexlify(packet.data.data).hex(),
        int(float(packet.sniff_timestamp))
    )


def read_pcapfile_mh(pcapfile: str, codes=None, codestartwith=[]):
    '''read packet of Gift, Player, GiftPopup'''
    if codes is None:
        codes = [
            "370b00",  # Gift
            "310b00",  # Gift
            "060b00",  # Player
            # "2b0b13",  # Popup
            "2b0b12",  # Popup
        ]
    gifts: list[Gift] = []
    popups: list[GiftPopup] = []
    players: list[Player] = []

    cap = PcapReader(pcapfile).read_all()
    d = ""
    for i, packet in enumerate(cap):
        _dd = get_extracted_packet(packet)
        if not _dd:
            continue
        dd, timestamp = _dd
        d += dd
        while True:
            if len(d) < 10:
                # データ長さとcodeが読み取れないほど短かったら抜ける
                break
            __length = hexstr2int(d[:4])*2  # データ長さ
            if __length == 0:
                # データ長さが0だとどうしようもなくなる。
                # codesが見つかるか試す
                for code in codes:
                    if code in d:
                        pos = d.find(code)
                        d = d[pos-4:]  # 上書き
                        __length = hexstr2int(d[:4])*2  # データ長さ上書き
                        assert d[4:10] == code
                        break
                else:
                    # codesが見つからなかったら関係ないし、丸ごとスキップする
                    logger.warning(f"i= {i+1}, {d[:10]}")
                    logger.warning(f"len(d) = {len(d)}")
                    d = ""
                    break

            if len(d) >= __length:
                data = d[:__length]
                d = d[__length:]
            else:
                # データ長さが足りなかったら次のパケットをもらうために抜ける
                break

            result = read_packet(data, codes, codestartwith)
            if result is None:
                continue

            if len(result) == 0:
                continue
            if isinstance(result[0], Gift):
                gifts += result
            elif isinstance(result[0], Player):
                players += result
            elif isinstance(result[0], GiftPopup):
                popups += result
            else:
                # print(type(result[0]))
                # raise Exception
                pass

    # プレーヤーだけiggidでuniqueにする。
    __iggids = []
    __players = []
    for p in players:
        if p.iggid in __iggids:
            continue
        else:
            __iggids.append(p.iggid)
            __players.append(p)

    return {
        "popups": [asdict(g) for g in popups],
        "playerlist": [asdict(p) for p in __players],
        "giftlist": [asdict(g) for g in gifts]
    }


def get_iggip(cap, scapy=True):
    started = time.time()
    ipaddrs: list[str] = []
    for packet in cap:
        if scapy:
            if "IP" not in packet or 'TCP' not in packet:
                continue
            if not packet['TCP'].payload:
                continue
            if packet['TCP'].sport != 5991:
                continue
            ipaddr = packet['IP'].src
            if ipaddr not in ipaddrs:
                ipaddrs.append(ipaddr)
        else:
            if not hasattr(packet, "tcp") or not hasattr(packet, "data"):
                continue
            if packet.tcp.srcport != "5991":
                continue
            ipaddr = packet.ip.src
            if ipaddr not in ipaddrs:
                ipaddrs.append(ipaddr)
    if len(ipaddrs) != 1:
        logger.warning(f"multiple ip.src found: {ipaddrs}")
    logger.info(
        f"time to get ip.src: {time.time()-started:4.2f}sec, ip:{ipaddrs}")
    return ipaddrs


def read_pcapfile(pcapfile: str, codes, codestartwith,
                  p=True, ipaddrs=[], delim=80) -> list:
    results = []
    __size = os.path.getsize(pcapfile)/1024/1024
    __started = time.time()
    cap = PcapReader(pcapfile).read_all()
    logger.info(
        f"time to load pcap: {time.time()-__started:5.2f}sec/{__size:.2f}MB")
    iggips = get_iggip(cap)
    if ipaddrs:
        for addr in ipaddrs:
            if addr in iggips:
                break
        else:
            assert False, f"ip selected not found: {ipaddrs}"

    d = ""
    for i, packet in enumerate(cap):
        _dd = get_extracted_packet(packet, ipaddrs=ipaddrs)
        if not _dd:
            continue
        dd, timestamp = _dd
        d += dd
        while True:
            # 1690 15002320001d004700d0
            if len(d) < 10:
                # データ長さとcodeが読み取れないほど短かったら抜ける
                break
            __length = hexstr2int(d[:4])*2  # データ長さ
            if __length == 0:
                # データ長さが0だとどうしようもなくなる。
                # codesが見つかるか試す
                for code in codes:
                    if code in d:
                        pos = d.find(code)
                        d = d[pos-4:]  # 上書き
                        __length = hexstr2int(d[:4])*2  # データ長さ上書き
                        assert d[4:10] == code
                        break
                else:
                    # codesが見つからなかったら関係ないし、丸ごとスキップする
                    logger.warning(f"i= {i+1}, {d[:10]}")
                    logger.warning(f"len(d) = {len(d)}")
                    d = ""
                    break

            if len(d) >= __length:
                data = d[:__length]
                d = d[__length:]
            else:
                # データ長さが足りなかったら次のパケットをもらうために抜ける
                break
            if __length < delim:  # CAUTION
                continue
            result = read_packet(data, codes, codestartwith,
                                 timestamp=timestamp)
            if result is None or len(result) == 0:
                continue
            results += result
            if p:
                for r in result:
                    print(r)
    return results
