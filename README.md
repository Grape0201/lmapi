[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://buymeacoffee.com/lordscounters)

# lmapi
a small project for sniffing packets of Lords Mobile

# Usage
## reading .pcap file
Packets from IGG can be saved with any android app like [PCAPdroid](https://github.com/emanuele-f/PCAPdroid).

```python
from lmapi.pcapReader import read_pcapfile

pcapfile = "test.pcap"
# packet code of opening gifts at once
# see lmapi/lmpacket.py
code = "370b00"

contents = read_pcapfile(pcapfile, [code], [])
for content in contents:
    print(content)  # see lmapi/lmdataclass.py
```

## realtime monitoring
With PCAPdroid streaming mode, 
```sh
curl -NLs your.smartphone.ip.address:8080 | python example_realtime.py -
```

## codes
TCP pcakets from IGG consists of:
- length of data (2 bytes)
- "code" (3 bytes)
- body

[lmpacket.py](https://github.com/Grape0201/lmapi/blob/master/lmapi/lmpacket.py) intereprets the packet, currently implemented "codes" are as below:
|code|content|
|:---:|:---|
|5e0d**|hunt monster mail|
|ac08**|map|
|f20a**|guild inner board|
|310b00|open gift one by one|
|2b0b12|gift popup|
|2b0b13|gift -> gift tables|
|2b0b14|gift -> gift tables|
|060b00|might ranking|
|080b00|might ranking of other guilds|
|370b00|open gifts at once|
|ac080c|tap castle|
|7f0500|open chests (not gifts)|
|bb0b00|chat|
|2a0b00|outer guild board|
|232000|familiar skill activated|
|8305**|familiar skill activated|
