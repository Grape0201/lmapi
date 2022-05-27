import logging
import time
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
from .hex_funcs import hexstr2int, hexstr2str, guid2xy, hexstr2float
from .constants import OBJECT_TYPES
from .lmdataclass import (
    ChestResult, GiftPopup, Gift, HuntReport, LMItem,
    MapObject, MapObjectCamp, MapObjectCastle,
    MapObjectFort, MapObjectMonster, MapObjectMoving, MapObjectResourceTile, 
    OuterGuildBoard, InnerGuildBoard,
    Player, Castle, Comment, ResultOpenChests, SkillActivated
)

logger = logging.getLogger(__name__)
KINGDOM_MAX = 1200


def is_valid_player_name(name: str) -> bool:
    if len(name) <= 3:
        return False
    if name == "Dark.nest":
        return True
    ok = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    for c in name:
        if c not in ok:
            return False
    return True


def read_packet(hexstr: str,
                codes: list[str],
                codestartswith: list[str],
                timestamp=0,
                mode=None) -> list:
    '''
    ローモバの受信パケットの塊を読む関数
    '''
    __code = hexstr[4:10]
    css_flag = False
    for csw in codestartswith:
        if __code.startswith(csw):
            css_flag = True
    if __code not in codes and not css_flag:
        return

    if __code.startswith("5e0d"):
        # hunt monster mail
        return __read_5e0d(hexstr)
    elif __code.startswith("ac08"):
        # map
        return __read_ac08(hexstr)
    elif __code.startswith("ba08"):
        # map, Dragon Arena
        return __read_ac08(hexstr)
    elif __code.startswith("f20a"):
        # guild inner board
        # f20a96, f20af0
        return __read_f20a(hexstr)
    elif __code == "310b00":
        # open gift one by one
        return __read_310b00(hexstr)
    elif __code == "2b0b12":
        # gift popup
        return __read_2b0b12(hexstr)
    elif __code == "2b0b13":
        # gift -> gift tables
        return __read_2b0b13(hexstr)
    elif __code == "2b0b14":
        # gift -> gift tables
        return __read_2b0b14(hexstr)
    elif __code == "060b00":
        # might ranking
        return __read_060b00(hexstr)
    # elif __code == "080b00":
    #     # might ranking of other guilds
    #     return __read_080b00(hexstr)
    elif __code == "370b00":
        # open gifts at once
        return __read_370b00(hexstr, timestamp)
    elif __code == "ac080c":
        # tap castle
        return __read_ac080c(hexstr)
    elif __code == "7f0500":
        # open chests (not gifts)
        return __read_7f0500(hexstr)
    elif __code == "bb0b00":
        # chat
        return __read_bb0b00(hexstr)
    elif __code == "2a0b00":
        # outer guild board
        return __read_2a0b00(hexstr)
    elif __code == "232000":
        # skill
        return __read_232000(hexstr)
    elif __code.startswith("8305"):
        # skill
        return __read_8305(hexstr)
    else:
        raise NotImplementedError


def __read_232000(d: str):
    '''
    packet of skill
    15 00 23 20 00
    - 1d 00
    - 47 00 
    - 52 1b 89 62
    - 00 00 00 00 00 00 00 00
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 42
    skill_code = d[10:18]
    time_activated_lasttime = hexstr2int(d[18:18+8])
    assert d[26:42] == "0"*16
    skills = {
        "1d004700": "Refreshed",
        "26005700": "Seasoned Courier",
        "1e005b00": "Nether Quake",
        "3a005600": "Pay Day",
        "3c005200": "Lucky Stars",
        "3b005100": "Stroke of Fortune",
        "4d000a00": "First Class",
        "34004400": "Gold Digger",
        # "": "Fresh Air",
        # "": "",
        "36004800": "Ship Ahoy",
        # "": "Gather Round",  => 別コード
    }
    print(skills.get(skill_code, "### "+skill_code))
    return SkillActivated(
        time_activated_lasttime=time_activated_lasttime,
        skill_code=skill_code
    )


def __read_8305(d: str):
    pass


def __read_5e0d(d: str):
    '''
    packet of monster hunt mail
    '''
    __length = hexstr2int(d[:4])*2
    time_stamp = hexstr2int(d[18:26])
    assert d[26:34] == "0"*8
    kingdom = hexstr2int(d[34:38])
    x, y = guid2xy(d[38:44])
    assert d[44:46] in ["00", "01"]
    killed = d[44:46] == "01"
    # print(killed, d[46:50])    # TODO
    monster_id = d[50:54]
    monster_lv = hexstr2int(d[54:56])
    hp_start = hexstr2int(d[56:64])
    hp_remain = hexstr2int(d[64:72])
    hp_maximum = hexstr2int(d[72:80])
    player_exp = hexstr2int(d[80:88])
    hero_ids = [d[88+ihero*4:92+ihero*4] for ihero in range(5)]
    hero_info = [d[148+ihero*16:148+16+ihero*16] for ihero in range(5)]
    hunt_in_a_row = hexstr2int(d[228:230])
    energy_used = hexstr2int(d[230:232])
    energy_dealt = hexstr2int(d[232:234])
    # damage_bonus = hexstr2int(d[234:242])
    # print(
    #     hexstr2int(d[242:250]),
    #     hexstr2int(d[250:258]),
    #     hexstr2int(d[258:266]),
    #     hexstr2int(d[266:274]),
    #     hexstr2int(d[274:276]),
    #     # d[234:276]
    # )  # TODO

    assert d[276:292] == "1100000001000000"
    num_kinds = hexstr2int(d[292:294])
    items: list[LMItem] = []
    j = 294
    while j+10 <= __length:
        items.append(LMItem(
            item_id=d[j:j+4],
            number_of_item=hexstr2int(d[j+4:j+8]),
            material_quality=hexstr2int(d[j+8:j+10]),
        ))
        j += 10
    hr = HuntReport(
        time_stamp=time_stamp,
        kingdom=kingdom, x=x, y=y,
        killed=killed,
        monster_id=monster_id,
        monster_lv=monster_lv,
        hp_start=hp_start,
        hp_remain=hp_remain,
        hp_maximum=hp_maximum,
        player_exp=player_exp,
        hero_ids=hero_ids,
        hero_infos=hero_info,
        hunt_in_a_row=hunt_in_a_row,
        energy_used=energy_used,
        energy_dealt=energy_dealt,
        num_kinds=num_kinds,
        rewards=items,
    )
    # print(hr)
    return [hr]


def __read_bb0b00(d: str) -> list[Comment]:
    '''
    packet of chat
    - [4 chars]
    - bb0b00

    me
    unk02 = 000000009d9c083300000000
    unk03 = 0000000000
    unk1  = 0e
    unk2  = 000000


    '''
    CHAT_TYPES = {
        "6a": "",  # ?
        "6c": "executed",  # execute leader
        "6d": "em",  # emoticon
        "00": "nc",  # normal comment
        "65": "exit guild",  # exit guild
        "66": "",  # ?
        "69": "enter guild",  # enter guild
        "68": "kicked",  # unknown
    }
    CHAT_PLACES = {
        "000100": "guild",
        "ff0100": "world",
    }
    TITLES = {
        "00": "",
        "01": "",
        "02": "",
        "03": "",
        "04": "",
        "05": "",
        "06": "",
        "07": "",
        "08": "",
        "09": "",
        "0a": "",
        "0b": "",
        "0c": "",
        "0d": "",
        "0e": "",
        "0f": "",
        "10": "",
        "11": "",
        "12": "",
        "13": "",
        "14": "",
    }
    chat_place = d[10:16]
    if chat_place not in CHAT_PLACES:
        logger.warning(f"unknown chat place: {chat_place}")
    time = hexstr2int(d[16:24])
    assert d[24:32] == "0"*8
    iggid = hexstr2int(d[32:40])
    assert d[40:48] == "0"*8
    comment_count = hexstr2int(d[48:54])  # 1づつ増えてる
    assert d[54:64] == "0"*10
    chat_type = d[66:68]
    player = hexstr2str(d[72:98])
    unk1 = d[98:100]
    assert unk1 in ["01", "02", "0a", "0b", "0c", "0d", "0e", "0f"], unk1
    guild_tag = hexstr2str(d[100:106])
    color = d[106:108]  # 05: ギルマス, 04: 不明, 03: 不明
    title = d[108:110]
    unk2 = d[110:112]
    assert color in ["00", "03", "04", "05", "09"], d[106:108]
    assert title in TITLES, d[108:110]
    assert unk2 in ["00", "05"], d[110:112]

    chat_length = hexstr2int(d[112:116])*2
    if chat_type == "00":
        comment = hexstr2str(d[116:])
    elif chat_type == "6d":
        comment = d[114:]
        # assert comment in EMOTICONS, comment
    else:
        comment = CHAT_TYPES[chat_type]
        if chat_type not in ["68", "6c"]:
            assert d[114:] == "00", f"chat_type={chat_type}\n{d[114:]}"
        else:
            comment += " by " + hexstr2str(d[116:])
    assert chat_length == len(d[114:]) - 2
    assert d[66:68] in CHAT_TYPES, d[66:68]
    return [Comment(
        chat_place=chat_place,
        time=time,
        iggid=iggid,
        comment_count=comment_count,
        chat_type=chat_type,
        player=player,
        unk1=unk1,
        guild_tag=guild_tag,
        color=color,
        title=title,
        unk2=unk2,
        comment=comment
    )]


def __read_7f0500(d: str):
    '''
    packet using items
    - open chests (not gifts)
    - using energy
    - usingrandom relocator
    - using boosts

    @@@@@@@@@@@@@
    - [4 chars]
    - ac080c
    - [4 chars]: chest id
    - [4 chars]*6: unk
    - [6 chars]: unk, all 0
    - [12 chars]: unk, 日付依存データ
    - [2 chars]: num_kinds?
    * [10 chars]: item_id, item_group, num, rarity
    * [10 chars]: item_id, item_group, num, rarity
    * ...

    # epic material chest
    94007f0500
      - d407
      - 9303 6265 0000 0000 4f51 0100
      - 000000
      - [12 chars]: 00cccd380018

    # ???
    04047f0500
      - f704
      - 0000 0000 1900 f704 00cb 2062
      - 000000
      - [12 chars]: 004038000000

    # [Rare]Showdown Trove
    3a007f0500
      - a40a
      - 0000 0000 0100 0000 0523 0300
      - 000000
      - [12 chars]: 00a40b460005

    # using 2k, 2k, 1k energy
    99007f0500
      - 8b04
      - df03 0000 e11d 0000 a566 3462
      - 0000 0000 0000.....
    99007f0500
      - 9804
      - 0e00 0000 0b00 9804 a166 3462
      - 0000 0000 0807....
    99007f0500
      - 8a04
      - 6008 0000 921f 0000 ac69 3462
      - 0000 0000 0000....

    # random relo
    99007f0500
      - eb03
      - 220d 0000 4c00 bab2 0200 0000
      - 0000 0000 0000....
    '''
    __length = hexstr2int(d[:4])*2
    chest_id = d[10:14]
    # assert d[38:44] == "0"*6, d[:56]
    # assert d[30:34] != "0"*4, d[:56]
    # print(d)

    items: list[ChestResult] = []
    j = 56
    # num_kinds = hexstr2int(d[54:56])
    # for _ in range(num_kinds+1):
    while j+10 <= __length:
        # item_id = hexstr2int(d[j:j+4])
        # item_group = hexstr2int(d[j+2:j+4])
        # num = hexstr2int(d[j+4:j+8])
        # rarity = hexstr2int(d[j+8:j+10])
        # item_name = f"{item_group} {item_id}"
        # if item_group in ITEMIDS and item_id in ITEMIDS[item_group]:
        #     item_name = ITEMIDS[item_group][item_id][0]
        items.append(ChestResult(
            item_id=d[j:j+4],
            number_of_items=hexstr2int(d[j+4:j+8]),
            rarity=hexstr2int(d[j+8:j+10])
        ))
        j += 10
    assert __length == j
    roc = ResultOpenChests(
        chest_id=chest_id,
        items=items
    )
    # print(roc)
    return [roc]


def __read_ac080c(d: str) -> list[Castle]:
    '''
    packet when tapped a castle
    - [4 chars]
    - ac080c
    - [16 chars]: unknown
    - [4 chars]: unknown
    - [6 chars]: unknown
    - [40 chars]: guild name
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 124
    return [Castle(
        tile_id=hexstr2int(d[10:26]),
        unk_2f=hexstr2int(d[26:28]),
        guid=d[28:36],
        long_guild_name=hexstr2str(d[36:76]),
        vip_level=hexstr2int(d[76:78]),
        guild_rank=hexstr2int(d[78:80]),
        unk4=hexstr2int(d[80:92]),
        might=hexstr2int(d[92:108]),
        troops_killed=hexstr2int(d[108:124])
    )]


def __read_ac08(d: str):
    '''
    ゴミが入っていても強引にMapObjectを取り出す
    '''
    __length = hexstr2int(d[:4])*2
    code = d[4:10]
    if code == "ac080c":
        return __read_ac080c(d)
    elif code == "ac0801":
        print(d)
    # assert code in [
    #     "ac0801", "ac0802", "ac0803",
    #     "ac0809",
    #     "ac080d", "ac080e", "ac080f",
    #     "ac0811", "ac0812",
    #     "ac0816", "ac0817", "ac0818",
    #     "ac0820", "ac082a", "ac082d",
    #     # Chalice
    #     "ac0824", "ac0826", "ac0833",
    # ], code
    j = 10
    objs = []
    while j+98 <= __length:
        while j+98 <= __length:
            try:
                objs.append(__create_map_object(d[j:j+98]))
                break
            except (AssertionError, NotImplementedError, UnicodeDecodeError):
                j += 2
        if d[j+6:j+8] == "00":
            j += 6
        j += 98
    if len(objs) == 0 and __length > 98:
        logger.warning(f"No map object found: {code}, len={__length}")
    # print(f"code={code} len(objs)={len(objs)} len={__length}")
    # ac0801 {0, 1, 2}
    # ac0802 {0, 1}
    # ac0809 {0, 1}
    # ac080d {0, 1, 2}
    # ac080e {0, 1, 2, 33, 4, 5, 6, 3, 8, 14, 18, 23}
    # ac080f {0, 1, 2, 3, 4, 5, 6, 35, 10, 12, 13, 15, 20, 26, 27, 29}
    # ac0812 {0}
    # ac0816 {6, 8, 12, 14, 15, 17, 20, 22, 23,  ... }
    # ac0817 {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, ... }
    # ac0818 {0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, ... }
    # ac0820 {3}
    # ac082a {0}
    return objs


def __create_map_object(d: str, lvs: list[int] = []) -> MapObject:
    '''
    [98 chars] are consists of
    - [8 chars]
      - [6 chars]: guid
      - [2 chars]: object_type
    - [90 chars]: content

    [88 chars] are consists of
    - "object_type"== 0a: monster
      - [2 chars]: monster lv
      - [4 chars]: monster id
      - [12 chars]: time remain
      - [8 chars]: HP percentage remain
      - ---------------------------------------
      - [68 chars]: all 0
    - "object_type"== 08: castle or darknest
      - [26 chars]: player_name = hexstr2str(d[10:36])
      - ---------------------------------------
      - [6 chars]: guild_tag = hexstr2str(d[36:42])
      - [4 chars]: kingdom_player = hexstr2int(d[42:46])
      - [2 chars]: level = hexstr2int(d[46:48])
      - [2 chars]: status_flag = hexstr2int(d[48:50])
      - [4 chars]: title = hexstr2int(d[50:54])
      - [4 chars]: kingdom_guild = hexstr2int(d[54:58])
      - [4 chars]: castle_skin = d[58:62]
      - [2 chars]: castle_skin_level = hexstr2int(d[62:64])
      - [36 chars]: in almost all cases all zero TODO
    - "object_type"== 01, 02, 03 ...: resource tiles
      - [26 chars]: player_name in case occupied
      - ---------------------------------------
      - [6 chars]: guild_tag in case occupied
      - [4 chars]: kingdom_player in case occupied
      - [2 chars]: level = hexstr2int(d[46:48])
      - [8 chars]: maximum_resource
      - [8 chars]: remain_percentage
      - [8 chars]: time_stamp
      - [28 chars]: all zero

    '''
    assert len(d) == 98
    guid = d[:6]
    x, y = guid2xy(guid)
    object_type = d[6:8]
    if object_type != '00':
        assert x != -1 and y != -1

    if object_type == "0a":
        # monster
        monster_lv = hexstr2int(d[8:10])
        monster_id = d[10:14]
        time_remain = hexstr2int(d[14:22])
        hp_percentage = hexstr2float(d[22:30])
        assert 1 <= monster_lv <= 5
        assert monster_id[2:] == "00"
        assert monster_id != "0000"
        assert d[30:98] == "0"*68
        if lvs and monster_lv not in lvs:
            return

        return MapObject(
            x=x, y=y, object_type=object_type,
            obj=MapObjectMonster(
                lv=monster_lv,
                monster_id=monster_id,
                time_remain=time_remain,
                hp_percentage=hp_percentage
            )
        )
    elif object_type == "08":
        # castle or darknest
        player_name = hexstr2str(d[8:34])
        guild_tag = hexstr2str(d[34:40])
        kingdom_player = hexstr2int(d[40:44])
        level = hexstr2int(d[44:46])
        status_flag = hexstr2int(d[46:48])
        title = hexstr2int(d[48:52])
        kingdom_guild = hexstr2int(d[52:56])
        castle_skin_id = d[56:60]
        castle_skin_level = hexstr2int(d[60:62])
        # TODO
        # assert d[64:96] == "0"*32, d[64:96] + f"{x},{y}, {repr}"
        assert is_valid_player_name(player_name)
        assert 1 <= level <= 25
        assert kingdom_player < KINGDOM_MAX, f"kingdom: {kingdom_player}\n{d}"
        if kingdom_guild > KINGDOM_MAX:
            logger.warning(f"kingdom: {kingdom_guild}\n{d}")
        return MapObject(
            x=x, y=y, object_type=object_type,
            obj=MapObjectCastle(
                player=player_name,
                guild_tag=guild_tag,
                kingdom_player=kingdom_player,
                lv=level,
                status_flag=status_flag,
                title=title,
                kingdom_guild=kingdom_guild,
                castle_skin_id=castle_skin_id,
                castle_skin_lv=castle_skin_level,
            )
        )
    elif object_type in ["01", "02", "03", "04", "05", "06"]:
        # resouce tile
        level = hexstr2int(d[44:46])
        if lvs and level not in lvs:
            return
        if d[8:44] == "0"*36:
            player_name = ""
            guild_tag = ""
            kingdom_player = ""
        else:
            player_name = hexstr2str(d[8:34])
            guild_tag = hexstr2str(d[34:40])
            kingdom_player = hexstr2int(d[40:44])
            assert is_valid_player_name(player_name)
            assert kingdom_player < KINGDOM_MAX, f"kgdm: {kingdom_player}\n{d}"
        maximum_resource = hexstr2int(d[46:54])
        remain_percentage = hexstr2float(d[54:62])  # something wrong ?
        time_stamp = hexstr2int(d[62:70])
        assert 0 < level < 6, f"resoure tile lv: {level}({d[44:46]})\n{d}"
        assert d[70:98] == "0"*28
        # if d[54:62] != "00000000":
        #     print(f"{d[60:62]}{d[58:60]}{d[56:58]}{d[54:56]}")
        return MapObject(
            x=x, y=y, object_type=object_type,
            obj=MapObjectResourceTile(
                resource=OBJECT_TYPES[object_type],
                lv=level,
                player=player_name,
                guild_tag=guild_tag,
                kingdom_player=kingdom_player,
                maximum_resource=maximum_resource,
                remaining_percentage=remain_percentage,
                timestamp=time_stamp
            )
        )
    elif object_type == "09":
        # camp
        # TODO
        player_name = hexstr2str(d[8:34])
        guild_tag = hexstr2str(d[34:40])
        kingdom_player = hexstr2int(d[40:44])
        level = hexstr2int(d[44:46])
        status_flag = hexstr2int(d[46:48])
        title = hexstr2int(d[48:52])
        kingdom_guild = hexstr2int(d[52:56])
        assert d[66:98] == "0"*32
        assert is_valid_player_name(player_name)
        assert kingdom_player < KINGDOM_MAX, f"kingdom: {kingdom_player}\n{d}"
        assert kingdom_guild < KINGDOM_MAX, f"kingdom: {kingdom_guild}\n{d}"
        assert 1 <= level <= 25
        return MapObject(x=x, y=y, object_type=object_type, obj=MapObjectCamp(
            player=player_name,
            guild_tag=guild_tag,
            kingdom_player=kingdom_player,
            lv=level,
            status_flag=status_flag,
            title=title,
            kingdom_guild=kingdom_guild,
        ))
    elif object_type == "0b":
        # Base or Fort
        # - guild icon
        # - protection/battle phase
        # - fort name: base/lunar fort/sky fort/ ...
        fort_id = d[8:12]
        time_stamp = hexstr2int(d[12:20])  # 454f2762
        # unk1 = d[20:28]  # 00000000
        # unk2 = d[28:32]  # 8097
        # unk3 = d[32:36]  # 0600
        # unk4 = d[36:40]  # 4e01
        player_name = hexstr2str(d[40:66])
        guild_tag = hexstr2str(d[66:72])
        kingdom_player = hexstr2int(d[72:76])  # 順番わからん
        kingdom_guild = hexstr2int(d[78:82])   # 所有者の所属王国、所有者のギルドの所属王国、要塞のある王国
        kingdom_fort = hexstr2int(d[82:86])
        assert is_valid_player_name(player_name)
        assert kingdom_player < KINGDOM_MAX, f"kingdom: {kingdom_player}\n{d}"
        assert kingdom_guild < KINGDOM_MAX, f"kingdom: {kingdom_guild}\n{d}"
        assert kingdom_fort < KINGDOM_MAX, f"kingdom: {kingdom_fort}\n{d}"
        # print(fort_id, datetime.fromtimestamp(time_stamp))
        # print(unk1, unk2, unk3, unk4)
        return MapObject(x=x, y=y, object_type=object_type, obj=MapObjectFort(
            fort_id=fort_id,
            player_name=player_name,
            guild_tag=guild_tag,
            kingdom_player=kingdom_player,
            kingdom_guild=kingdom_guild,
            kingdom_fort=kingdom_fort
        ))
    elif object_type == "00":
        # TODO の項目として考えられるのが
        # - エモーティコン
        #                         58 7b 0b 00 50 55 50 55           X{..PUPU
        # 20 6e 69 67 6f 00 00 00 00 4c 48 41 b2 02 75 01    nigo....LHA..u.
        # 67 65 01 7b fa 66 34 62 00 00 00 00 0e 00 00 00   ge.{.f4b........
        # 00 00 00 00 00 00 00 00 09 00 00 00               ............
        # _guid = hexstr2int(d[:6])   # TODO unixtimeっぽい。ミリ秒？
        player = hexstr2str(d[8:34])
        guild_tag = hexstr2str(d[34:40])
        kingdom = hexstr2int(d[40:44])
        xfrom, yfrom = guid2xy(d[44:50])
        xto, yto = guid2xy(d[50:56])
        time_stamp = hexstr2int(d[56:64])
        unk01 = d[64:72]
        total_sec = hexstr2int(d[72:76])
        unk02 = d[76:80]
        # unk4 = hexstr2int(d[80:82])  # TODO
        unk04 = d[82:88]
        # unk3 = hexstr2int(d[88:90])  # TODO
        unk03 = d[90:96]
        mode = d[96:98]
        assert unk01 == "0"*8
        assert unk02 == "0"*4, unk02
        assert unk03 == "0"*6, unk03
        assert unk04 == "0"*6, unk04
        assert is_valid_player_name(player)
        assert kingdom < KINGDOM_MAX, f"kingdom: {kingdom}\n{d}"
        assert xfrom != -1 and yfrom != -1
        assert xto != -1 and yto != -1
        assert time_stamp > 1640000000
        # print(f"{mode}, {player:13}, {d[:6]}, {_guid}, {time_stamp}
        # {datetime.fromtimestamp(time_stamp)}, {total_sec}, {unk4}, {unk3},
        # {MODES[mode]}")
        return MapObject(
            x=x, y=y, object_type=object_type,
            obj=MapObjectMoving(
                player=player,
                guild_tag=guild_tag,
                kingdom=kingdom,
                xfrom=xfrom,
                yfrom=yfrom,
                xto=xto,
                yto=yto,
                time_stamp=time_stamp,
                total_sec=total_sec,
                mode=mode
            ))
    else:
        raise NotImplementedError(f"unknown obj: {object_type} @{x},{y}\n{d}")


def __read_370b00(d: str, timestamp: int) -> list[Gift]:
    '''
    packet when opened gifts at once
    - [4 chars]
    - 370b00
    - [8 chars]: unknown
    - [10 chars]: unknown
    - [2 chars]: number of gift entries
      - [66 chars]: gift entry 1
      - [66 chars]: gift entry 2
      - [66 chars]: ...

    [66 chars]: see __create_gift()
    '''
    __length = hexstr2int(d[:4])*2
    num_gifts = hexstr2int(d[28:30])
    # logger.debug(f"{d[10:28]} {hexstr2int(d[10:18])} {hexstr2int(d[18:28])}")
    assert __length == 30 + 66*num_gifts
    gifts = []
    j = 30
    for _ in range(num_gifts):
        gifts.append(__create_gift(d[j:j+66], timestamp=timestamp))
        j += 66
    return gifts


def __read_060b00(d: str) -> list[Player]:
    '''
    packet of might ranking(your guild)
    - [4 chars]
    - 060b00
    - [2 chars]: unkonwn
    - [2 chars]: number of player entries
      - [96 chars]: player entry 1
      - [96 chars]: player entry 2
      - ...

    [96 chars] consists of
    - [16 chars]: igg id
    - [4 chars]: avatar_id
    - [26 chars]: player name
    - [2 chars]: guild rank in your guild, like r4
    - [16 chars]: might
    - [16 chars]: kills
    - [16 chars]: last seen, unix-time
    '''
    __length = hexstr2int(d[:4])*2
    num_members = hexstr2int(d[12:14])
    assert __length == 14 + 96*num_members
    players = []
    j = 14
    for _ in range(num_members):
        players.append(Player(
            iggid=hexstr2int(d[j:j+16]),
            avatar_id=hexstr2int(d[j+16:j+20]),
            name=hexstr2str(d[j+20:j+46]),
            guild_rank=hexstr2int(d[j+46:j+48]),
            might=hexstr2int(d[j+48:j+64]),
            kills=hexstr2int(d[j+64:j+80]),
            lastseen=hexstr2int(d[j+80:j+96]),
        ))
        j += 96
    return players


def __read_2b0b14(d: str) -> list[GiftPopup]:
    '''
    packet unknown
    - 3000: 固定長
    - 2b0b14
    - [10 chars]: 8605000000
    - [16 chars]: be102a6200000000
    - [14 chars]: e3071c04010000
    - [26 chars]: 4e454f205a454f4e00000000
    - [10 chars]: 0000000000
    - [12 chars]: e30775200000
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 96
    player = hexstr2str(d[50:76])
    print(f"2b0b14: {player} {d[10:50]} {d[76:]}")


def __read_2b0b13(d: str) -> list[GiftPopup]:
    '''
    packet when a gift inserted in gift table
    - [4 chars]
    - 2b0b13
    - [10 chars]: counter 1
    - [16 chars]: unixtimte
    - [4 chars]:  gift id
    - [10 chars]: always 0 ?
    - [26 chars]: playername
    - [8 chars]:  counter 2
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 84
    counter1 = hexstr2int(d[10:20])
    unixtime = hexstr2int(d[20:36])
    gift_id = d[36:40]
    unknown0 = hexstr2int(d[40:50])
    player = hexstr2str(d[50:76])
    counter2 = hexstr2int(d[76:84])

    # monster = GIFTIDS[gift_id][0] if gift_id in GIFTIDS else ""
    # gift_rank = GIFTIDS[gift_id][1] if gift_id in GIFTIDS else 0
    if unknown0 != 0:
        logger.warning("__read_2b0b13, unkonw0 != 0")
    return [GiftPopup(
        counter=counter1,
        gift_id=gift_id,
        player=player,
        unixtime=unixtime,
        counter2=counter2
    )]


def __read_2b0b12(d: str) -> list[GiftPopup]:
    '''
    packet when you got a gift
    - [4 chars]
    - 2b0b12
    - [34 chars]: Gift Popup
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 44
    j = 10
    gift_id = d[j+4:j+8]
    # monster = GIFTIDS[gift_id][0] if gift_id in GIFTIDS else ""
    # gift_rank = GIFTIDS[gift_id][1] if gift_id in GIFTIDS else 0
    return [GiftPopup(
        counter=hexstr2int(d[j:j+4]),
        gift_id=gift_id,
        player=hexstr2str(d[j+8:j+34]),
        unixtime=int(time.time()),
    )]


def __read_310b00(d: str) -> list[Gift]:
    '''
    packet when opened a gift (one by one)
    - [4 chars]
    - 310b00
    - [66 chars]: see __create_gift
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 92
    d = d[10:]
    return [__create_gift(d)]


def __create_gift(d: str, timestamp=0) -> Gift:
    unknown1 = hexstr2int(d[8:10])
    unknown0 = hexstr2int(d[36:38])
    if unknown0 != 0:
        logger.warning("__create_gift, unkonw0 != 0")
    if unknown1 != 1:
        logger.warning("__create_gift, unkonw1 != 1")
    return Gift(
        sort_index=hexstr2int(d[:8]),
        time=hexstr2int(d[10:26]),
        gift_id=d[26:30],
        item_id=d[30:34],
        number_of_item=hexstr2int(d[34:36]),
        material_quality=hexstr2int(d[38:40]),
        player=hexstr2str(d[40:66]),
        time_gift_opened=timestamp,
    )


def __read_f20a(d: str) -> list:
    '''inner guild board

    - 20 04: length
    - f2 0a f0: code
    - 6b 14 00 17: unk1
    - 52 30 43 4b 48 45 41 52 54 00 00 00 00: Guild Master
    - bc ad aa 30: unk2
    - 10 00 00 00: unk3
    - 4c 48 41: Guild Tag
    - 4c 75 6e 65 72 20 48 75 6e 74 65 72 20 41 72 6d 79 00 00 00: Guild Name
    - 4c 69 76 65 20 74 68 65 20 4c 65 67 65 6e 64 00 00 00 00 00: Guild slogan
    - board: 1800
    - 4e 01 57 01 00: unk4
    - e4 07 e1 61 18 00: unk5
    - 44 cb 5e 05 0c 17: unk6
    - 00 00 00 00 00 00
    - b2 02: kingdom
    - 00 00 00 00 00 00 00 00 00 00 00 00
    - 01 03: unk7
    - 00....
    - 0f 37 4f 33 5f 62
    - 00 00 00 00
    - 04 0f 00 d6 11 05 05 00 01
    '''
    __length = hexstr2int(d[:4])*2
    assert __length == 2112

    assert d[54:60] == "0"*6
    assert d[1956:1960] in ["e207", "e307", "e407"]
    assert d[1980:1992] == "0"*12
    if d[1996:2012] != "0"*16:
        logger.warning(f"d[1996:2012]@f20a: {d[1996:2012]}")
    if d[2024:2074] != "0"*50:
        logger.warning(f"d[2024:2074]@f20a: {d[2024:2074]}")
        # f2747f000600000000000000000000000000000032281e140a
    assert d[2084:2094] in ["6200000000", "0"*10], d[2084:2094]
    if d[2108:2112] != "0001":
        logger.warning(f"d[2108:2112]@f20a: {d[2108:2112]}")
        # 0003
    result = InnerGuildBoard(
        guild_id=d[10:18],   # 6b1400 17
        guild_leader=hexstr2str(d[18:44]),
        unknown1=d[44:52],  # 同じギルドでも激しく変化している
        unknown2=d[52:54],  # 同じギルドで最初の4文字は変化なし？残りは激しく変化している
        guild_tag=hexstr2str(d[60:66]),
        long_guild_name=hexstr2str(d[66:106]),
        guild_slogan=hexstr2str(d[106:146]),
        board=d[146:1946],
        unknown3=d[1946:1956],
        unknown4=d[1956:1968],
        unknown5=d[1968:1980],
        kingdom=hexstr2int(d[1992:1996]),
        unknown6=d[2012:2020],  # 00000000, or
        unknown7=d[2020:2024],
        unknown8=d[2074:2078],
        unknown9=d[2078:2084],  # 4f335f, 5d463,
        guild_fest_rank=hexstr2int(d[2094:2096]),
        guild_showdown_rank=hexstr2int(d[2096:2100]),
        da_cups=hexstr2int(d[2100:2104]),
        guild_bash_rank=hexstr2int(d[2104:2106]),
        unknowna=d[2106:2108],  # 01 or 05
    )
    # print(result)
    return [result]


def __read_2a0b00(d: str) -> list:
    '''outer guild board'''
    __length = hexstr2int(d[:4])*2
    assert __length == 2780

    try:
        long_guild_name = hexstr2str(d[52:92])
    except UnicodeDecodeError:
        long_guild_name = d[52:92]

    assert d[2752:2758] == "0"*6
    assert d[2764:2766] in ["00", "01"]
    assert d[2770:2772] == "0"*2
    assert d[2778:2780] == "01"

    result = OuterGuildBoard(
        guild_id=d[10:20],  # f0 6b1400 00
        guild_leader=hexstr2str(d[20:46]),
        guild_tag=hexstr2str(d[46:52]),
        long_guild_name=long_guild_name,
        board=d[92:2692],
        guild_slogan=hexstr2str(d[2692:2732]),
        unknown1=d[2732:2752],
        gift_level=hexstr2int(d[2758:2760]),
        kingdom=hexstr2int(d[2760:2764]),
        unknown2=d[2764:2766],
        guild_fest_rank=hexstr2int(d[2766:2768]),
        guild_showdown_rank=hexstr2int(d[2768:2770]),
        da_cups=hexstr2int(d[2772:2776]),
        guild_bash_rank=hexstr2int(d[2776:2778]),
    )
    return [result]
