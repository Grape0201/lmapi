[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/lordscounters)

# lmapi
a small project for sniffing packets of Lords Mobile

# Usage
## reading .pcap file
Packets from IGG can be saved with any android app like [PCAPdroid](https://github.com/emanuele-f/PCAPdroid).

```python
from lmapi.pcapReader import read_pcapfile

# packet code of opening gifts at once
code = "370b00"  
contents = read_pcapfile(pcap, [code], [])
for content in contents:
    print(content)  # see lmapi/lmdataclass.py
```

## realtime monitoring
packets can be streamed via apps above.
```python
from lmapi.pcapReader import (
    get_extracted_packet,
    read_packet
)
from lmapi.hex_funcs import hexst2int
from scapy.all import sniff

d = ""
def pkt_handler(packet, codes, codestartswith, pfunc: Callable = None):
    global d
    dd = get_extracted_packet(packet)
    if dd is None:
        return
    d += dd[0]
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
    pkt_handler(packet, [], ["ac08"])

sniff(
    offline=sys.stdin.buffer,
    prn=handler,
    store=0
)
```

With PCAPdroid streaming mode, 
```sh
curl -NLs your.smartphone.ip.address:8080 | python realtime.py -
```