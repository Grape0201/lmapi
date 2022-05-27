'''
notes
- unixtime: 16chars, 8chars
- playername: 26chars
- iggid: 16chars
- might: 16chars
- kills: 16chars
- avatar: 8 chars
'''

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Union
from .constants import ITEMS, MONSTER_IDS, FORT_IDS, CASTLE_SKINS, MODES
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
    pass
logger = logging.getLogger(__name__)


GUILD_FEST_RANKS = {
    0: "-",
    1: "Intermediate",
    2: "Advnaced",
    3: "Expert",
    4: "Master",
}
GUILD_BASH_RANKS = {
    1: "-",
    2: "Intermediate",
    3: "Advanced",
    4: "Expert",
    5: "Master",
}


@dataclass
class Gift:
    sort_index: int
    # unknown1: int
    time: int
    gift_id: str
    item_id: str
    number_of_item: int
    # unknown0: int
    material_quality: int
    player: str
    gift_name: str = ""
    gift_rank: int = -1
    gift_source: int = -1
    monster: str = ""
    item_name: str = ""
    item_category: str = ""
    time_gift_opened: int = 0

    def __post_init__(self):
        if self.gift_id in ITEMS:
            _i = ITEMS[self.gift_id]
            self.gift_name = _i[0]
            self.gift_rank = _i[3]
            self.gift_source = _i[4]
            self.monster = _i[5]
        if self.item_id in ITEMS:
            _i = ITEMS[self.item_id]
            self.item_name = _i[0]
            self.item_category = _i[1]

    def __repr__(self):
        return f"Gift {self.player:13} {self.gift_name:20} {self.gift_rank}"


@dataclass
class GiftPopup:
    counter: int
    gift_id: str
    player: str
    unixtime: int = -1
    counter2: int = -1
    gift_name: str = ""
    gift_rank: int = -1
    monster: str = ""

    def __post_init__(self):
        if self.gift_id in ITEMS:
            _i = ITEMS[self.gift_id]
            self.gift_name = _i[0]
            self.gift_rank = _i[2]
            self.monster = _i[5]

    def __repr__(self):
        return f"GiftPopup {self.player} {self.monster} {self.gift_rank}"


@dataclass
class Player:
    iggid: int
    avatar_id: int
    name: str
    guild_rank: int
    might: int
    kills: int
    lastseen: int

    def __repr__(self):
        return f"Player {self.iggid:10d} {self.name:13} {self.might}"


@dataclass
class Castle:
    tile_id: int
    unk_2f: int
    guid: str
    long_guild_name: str
    vip_level: int
    guild_rank: int
    unk4: int
    might: int
    troops_killed: int


@dataclass
class Comment:
    chat_place: str
    time: int
    iggid: int
    comment_count: int
    chat_type: str
    player: str
    unk1: str
    guild_tag: str
    color: str
    title: str
    unk2: str
    comment: str

    def __repr__(self):
        repr = f"Comment: [{self.guild_tag}]{self.player:13}"
        repr += f"@{datetime.fromtimestamp(self.time)}: {self.comment}\n"
        if self.iggid != 0:
            repr += f"iggid = {self.iggid}\n"
        repr += f"unk1  = {self.unk1}\n"
        repr += f"unk2  = {self.unk2}\n"
        return repr


@dataclass
class MapObjectMonster:
    lv: int
    monster_id: str
    time_remain: int
    hp_percentage: float
    monster_name: str = ""

    def __post_init__(self):
        if self.monster_id in MONSTER_IDS:
            self.monster_name = MONSTER_IDS[self.monster_id]
        else:
            logger.warning(f"unknown monster id: {self.monster_id}")

    def __repr__(self) -> str:
        return f"{self.monster_name} lv{self.lv}"


@dataclass
class MapObjectCastle:
    player: str
    guild_tag: str
    kingdom_player: int
    lv: int
    status_flag: int
    title: int
    kingdom_guild: int
    castle_skin_id: str
    castle_skin_lv: int
    castle_skin_name = ""

    def __post_init__(self):
        self.castle_skin_name = CASTLE_SKINS.get(self.castle_skin_id, "")
        if not self.castle_skin_name:
            logger.warning(f"new skin id! {self.castle_skin_id}")

    def __repr__(self) -> str:
        return f"[{self.guild_tag}]{self.player} Lv.{self.lv}"


@dataclass
class MapObjectResourceTile:
    resource: str
    lv: int
    player: str
    guild_tag: str
    kingdom_player: str
    maximum_resource: int
    remaining_percentage: float
    timestamp: int

    def __repr__(self) -> str:
        repr = f"{self.resource:7} lv{self.lv}"
        repr += f" {self.remaining_percentage:6.2f}%"
        if self.player:
            repr += f" [{self.guild_tag:3}]{self.player}"
        return repr


@dataclass
class MapObjectMoving:
    player: str
    guild_tag: str
    kingdom: int
    xfrom: int
    yfrom: int
    xto: int
    yto: int
    time_stamp: int
    total_sec: int
    mode: str

    def __repr__(self) -> str:
        repr = f"[{self.guild_tag:3}]{self.player:13} "
        repr += f"({self.xfrom:3},{self.yfrom:3})->"
        repr += f"({self.xto:3},{self.yto:3}) "
        repr += f"left@{datetime.fromtimestamp(self.time_stamp)} "
        repr += f"{MODES.get(self.mode, self.mode)} "
        return repr


@dataclass
class MapObjectCamp:
    player: str
    guild_tag: str
    kingdom_player: int
    lv: int
    status_flag: int
    title: int
    kingdom_guild: int

    def __repr__(self) -> str:
        return f"camp of [{self.guild_tag:3}]{self.player:13}"


@dataclass
class MapObjectFort:
    fort_id: str
    player_name: str
    guild_tag: str
    kingdom_player: int
    kingdom_guild: int
    kingdom_fort: int
    fort_name: str = ""

    def __repr__(self) -> str:
        self.fort_name = FORT_IDS.get(self.fort_id, self.fort_id)
        return f"{self.fort_name} [{self.guild_tag:3}]{self.player_name:13}"


@dataclass
class MapObject:
    x: int
    y: int
    object_type: str
    obj: Union[
        MapObjectMonster,
        MapObjectCastle,
        MapObjectResourceTile,
        MapObjectMoving]

    def __repr__(self) -> str:
        if self.object_type != "00":
            return f"X:{self.x:3d} Y:{self.y:3d} {self.obj.__repr__()}"
        else:
            return self.obj.__repr__()


@dataclass
class LMItem:
    item_id: str
    number_of_item: int
    material_quality: int

    def __repr__(self) -> str:
        item_name = f"{self.item_id}"
        if self.item_id in ITEMS:
            item_name = ITEMS[self.item_id][0]
        return f"{self.number_of_item} x {item_name}"


@dataclass
class HuntReport:
    time_stamp: int
    kingdom: int
    x: int
    y: int
    killed: bool
    monster_id: str
    monster_lv: int
    hp_start: int
    hp_remain: int
    hp_maximum: int
    player_exp: int
    hero_ids: list[str]
    hero_infos: list[str]
    hunt_in_a_row: int
    energy_used: int
    energy_dealt: int
    # unk3
    num_kinds: int
    rewards: list[LMItem]

    def __repr__(self) -> str:
        name = self.monster_id
        if self.monster_id in MONSTER_IDS:
            name = MONSTER_IDS[self.monster_id]
        damage = (self.hp_start-self.hp_remain)/self.hp_maximum*100
        repr = f"{name} Lv.{self.monster_lv}"
        repr += f"@k{self.kingdom} x:{self.x} y:{self.y}\n"
        repr += f"used/dealt={self.energy_used}/{self.energy_dealt} "
        repr += f"{self.hunt_in_a_row}++ {damage:.1f}%\n"
        for item in self.rewards:
            repr += f"- {item}\n"
        return repr


@dataclass
class ChestResult:
    item_id: str
    number_of_items: int
    rarity: int
    item_name: str = ""
    item_category: str = ""

    def __post_init__(self):
        if self.item_id in ITEMS:
            _i = ITEMS[self.item_id]
            self.item_name = _i[0]
            self.item_category = _i[1]
        else:
            self.item_name = self.item_id

    def __repr__(self) -> str:
        return f"{self.item_name:20}[{self.rarity}] x {self.number_of_items}"


@dataclass
class ResultOpenChests:
    chest_id: str
    items: list[ChestResult]
    chest_name: str = ""

    def __post_init__(self):
        if self.chest_id in ITEMS:
            _i = ITEMS[self.chest_id]
            self.chest_name = _i[0]

    def __repr__(self) -> str:
        repr = f"{self.chest_name}({self.chest_id})"
        for i in self.items:
            repr += f"\n- {i}"
        return repr


@dataclass
class OuterGuildBoard:
    guild_id: str
    guild_leader: str
    guild_tag: str
    long_guild_name: str
    board: str
    guild_slogan: str
    unknown1: str  # 20 chars
    gift_level: int
    kingdom: int
    unknown2: str  # 2 chars, 00 or 01
    guild_fest_rank: int
    guild_showdown_rank: int
    da_cups: int
    guild_bash_rank: int

    def __repr__(self) -> str:
        repr = f"[{self.guild_tag}]{self.long_guild_name} k={self.kingdom}\n"
        repr += f"- guild_id:       {self.guild_id}\n"
        repr += f"- gift_lv:        {self.gift_level}\n"
        repr += f"- guild fest:     {GUILD_FEST_RANKS[self.guild_fest_rank]}\n"
        repr += f"- guild showdown: Division {self.guild_showdown_rank}\n"
        repr += f"- da_cpus:        {self.da_cups} cup\n"
        repr += f"- guild_bash:     {GUILD_BASH_RANKS[self.guild_bash_rank]}\n"
        return repr


@dataclass
class InnerGuildBoard:
    guild_id: str
    guild_leader: str
    unknown1: str  # 8
    unknown2: str  # 2
    guild_tag: str
    long_guild_name: str
    guild_slogan: str
    board: str
    unknown3: str  # 10
    unknown4: str  # 12
    unknown5: str  # 12
    kingdom: int
    unknown6: str  # 8
    unknown7: str  # 4
    unknown8: str  # 4
    unknown9: str  # 6
    guild_fest_rank: int
    guild_showdown_rank: int
    da_cups: int
    guild_bash_rank: int
    unknowna: str  # 2

    def __repr__(self) -> str:
        repr = f"[{self.guild_tag}]{self.long_guild_name} k={self.kingdom}\n"
        repr += f"- guild_id:       {self.guild_id}\n"
        # repr += f"- gift_lv:        {self.gift_level}\n"
        repr += f"- guild fest:     {GUILD_FEST_RANKS[self.guild_fest_rank]}\n"
        repr += f"- guild showdown: Division {self.guild_showdown_rank}\n"
        repr += f"- da_cpus:        {self.da_cups} cup\n"
        repr += f"- guild_bash:     {GUILD_BASH_RANKS[self.guild_bash_rank]}\n"

        repr += " ".join([
            self.unknown1,
            self.unknown2,
            self.unknown3,
            self.unknown4,
            self.unknown5,
            self.unknown6,
            self.unknown7,
            self.unknown8,
            self.unknown9,
            self.unknowna,
        ])
        return repr


@dataclass
class SkillActivated:
    time_activated_lasttime: int
    skill_code: str