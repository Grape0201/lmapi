from lmapi.pcapReader import read_pcapfile

pcapfile = "test.pcap"
# packet code of opening gifts at once
# see lmapi/lmpacket.py
code = "370b00"

contents = read_pcapfile(pcapfile, [code], [])
for content in contents:
    print(content)  # see lmapi/lmdataclass.py
