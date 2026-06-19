#!/usr/bin/env python3
"""
schema_map.py — Extract English→Chinese name mappings from 5etools-cn
and apply them to Tetra-cube JSON files by matching ENG_name→name.

Usage:
  python schema_map.py fetch          # Download 5etools-cn data, build mapping
  python schema_map.py apply --dry-run  # Preview replacements
  python schema_map.py apply           # Apply to all Tetra-cube JSON files
"""

import json
import os
import sys
import re
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests

# ── Config ─────────────────────────────────────────────────────────────────

CN_BASE = "https://raw.githubusercontent.com/pttsw/5etools-cn/cn2.0/data"
MAPPING_CACHE = "cn_mapping.json"
TETRA_BASE = Path(".")

# Files to fetch from 5etools-cn and their data structure
CN_SOURCES = {
    "races.json":       {"key": "race",    "nameField": "name", "engField": "ENG_name"},
    "backgrounds.json": {"key": "background", "nameField": "name", "engField": "ENG_name"},
    "skills.json":      {"key": "skill",   "nameField": "name", "engField": "ENG_name"},
    "conditionsdiseases.json": {"key": None, "nameField": "name", "engField": "ENG_name"},
    "books.json":       {"key": "book",    "nameField": "name", "engField": "ENG_name"},
    "senses.json":      {"key": "sense",   "nameField": "name", "engField": "ENG_name"},
}

# Tetra-cube files to apply mapping to
TETRA_FILES = [
    "dnd/js/JSON/races.json",
    "dnd/js/JSON/classes.json",
    "dnd/js/JSON/backgrounds.json",
    "dnd/js/JSON/books.json",
    "dnd/js/JSON/other.json",
    "dnd/js/JSON/ua.json",
    "dnd/js/JSON/npcs.json",
    "dnd/js/JSON/life.json",
    "dnd/js/JSON/magic-items.json",
    "dnd/js/JSON/magic-item-homebrews.json",
    "dnd/js/JSON/magic-item-specials.json",
    "dnd/js/JSON/statblockdata.json",
    "dnd/js/JSON/names.json",
]

# Additional hardcoded mappings for terms not covered by 5etools-cn
EXTRA_MAPPINGS = {
    # Core rule terms
    "Armor Class": "护甲等级",
    "Hit Points": "生命值",
    "Hit Dice": "生命骰",
    "Speed": "速度",
    "Proficiency Bonus": "熟练加值",
    "Saving Throw": "豁免",
    "Saving Throws": "豁免",
    "Ability Check": "属性检定",
    "Attack Roll": "攻击检定",
    "Challenge Rating": "挑战等级",
    "Challenge": "挑战等级",
    "Passive Perception": "被动察觉",
    "Spellcasting": "施法",
    "Spellcasting Focus": "施法法器",
    "Spell Save DC": "法术豁免 DC",
    "Short Rest": "短休",
    "Long Rest": "长休",
    "Advantage": "优势",
    "Disadvantage": "劣势",
    "Difficult Terrain": "困难地形",
    # Damage types
    "Acid": "强酸", "Bludgeoning": "钝击", "Cold": "寒冷", "Fire": "火焰",
    "Force": "力场", "Lightning": "闪电", "Necrotic": "暗蚀",
    "Piercing": "穿刺", "Poison": "毒素", "Psychic": "心灵",
    "Radiant": "光耀", "Slashing": "挥砍", "Thunder": "雷鸣",
    # Abilities
    "Strength": "力量", "Dexterity": "敏捷", "Constitution": "体质",
    "Intelligence": "智力", "Wisdom": "感知", "Charisma": "魅力",
    # Sizes
    "Tiny": "微型", "Small": "小型", "Medium": "中型",
    "Large": "大型", "Huge": "巨型", "Gargantuan": "超巨型",
    # Creature types
    "Aberration": "异怪", "Beast": "野兽", "Celestial": "天界生物",
    "Construct": "构装生物", "Dragon": "龙类", "Elemental": "元素生物",
    "Fey": "精类", "Fiend": "魔族", "Giant": "巨人",
    "Humanoid": "类人生物", "Monstrosity": "怪兽",
    "Ooze": "泥怪", "Plant": "植物", "Undead": "亡灵",
    # Conditions
    "Blinded": "目盲", "Charmed": "魅惑", "Deafened": "耳聋",
    "Exhaustion": "力竭", "Frightened": "恐慌", "Grappled": "受擒",
    "Incapacitated": "失能", "Invisible": "隐形", "Paralyzed": "麻痹",
    "Petrified": "石化", "Poisoned": "中毒", "Prone": "倒地",
    "Restrained": "束缚", "Stunned": "震慑", "Unconscious": "昏迷",
    # Senses
    "Blindsight": "盲视", "Darkvision": "黑暗视觉",
    "Tremorsense": "震颤感知", "Truesight": "真实视觉",
    # Alignment
    "Lawful Good": "守序善良", "Neutral Good": "中立善良",
    "Chaotic Good": "混乱善良", "Lawful Neutral": "守序中立",
    "Neutral": "绝对中立", "Chaotic Neutral": "混乱中立",
    "Lawful Evil": "守序邪恶", "Neutral Evil": "中立邪恶",
    "Chaotic Evil": "混乱邪恶",
    "any alignment": "任意阵营", "Unaligned": "无阵营",
    # Class names
    "Barbarian": "野蛮人", "Bard": "吟游诗人", "Cleric": "牧师",
    "Druid": "德鲁伊", "Fighter": "战士", "Monk": "武僧",
    "Paladin": "圣武士", "Ranger": "游侠", "Rogue": "游荡者",
    "Sorcerer": "术士", "Warlock": "邪术师", "Wizard": "法师",
    "Artificer": "奇械师", "Blood Hunter": "血猎人", "Mystic": "灵能师",
    # Genders
    "Male": "男性", "Female": "女性",
    "Nonbinary or Unknown": "非二元性别或未知", "Genderless": "无性别",
    # ── Book names (without year suffixes) ──
    "Player's Handbook": "玩家手册",
    "Dungeon Master's Guide": "城主指南",
    "Monster Manual": "怪物手册",
    "Xanathar's Guide to Everything": "珊娜萨的万事指南",
    "Tasha's Cauldron of Everything": "塔莎的万象坩埚",
    "Mordenkainen's Tome of Foes": "魔邓肯的众敌卷册",
    "Volo's Guide to Monsters": "瓦罗怪物指南",
    "Volo's Guide (Monstrous Races)": "瓦罗怪物指南（怪物种族）",
    "Sword Coast Adventurer's Guide": "剑湾冒险者指南",
    "Eberron: Rising from the Last War": "艾伯伦：从终末战争中崛起",
    "Explorer's Guide to Wildemount": "荒洲探险家指南",
    "Guildmasters' Guide to Ravnica": "拉尼卡公会长指南",
    "Guildmaster's Guide to Ravnica": "拉尼卡公会长指南",
    "Mythic Odysseys of Theros": "塞洛斯之神话奥德赛",
    "Acquisitions Incorporated": "艾奎兹玄有限责任公司",
    "Elemental Evil Player's Companion": "元素邪恶玩家伴侣",
    "Unearthed Arcana": "未发掘的奥秘",
    "Adventure Modules": "冒险模组",
    "Other Content": "其他内容",
    "Other Notable Content": "其他值得关注的内容",

    # ── Remove problematic short words from WORD_TERMS ──
    # "Guide", "Elemental", "Arcana" etc. are removed and handled below
    # as full phrases only.

    # Common UI
    "Actions": "动作", "Bonus Actions": "附赠动作", "Bonus Action": "附赠动作",
    "Reactions": "反应", "Reaction": "反应",
    "Legendary Actions": "传奇动作", "Mythic Actions": "神话动作",
    "Lair Actions": "巢穴动作", "Regional Effects": "区域效应",
    "Damage Vulnerabilities": "伤害易伤", "Damage Resistances": "伤害抗性",
    "Damage Immunities": "伤害免疫", "Condition Immunities": "状态免疫",
    "Senses": "感官", "Languages": "语言", "Skills": "技能",
    "Armor": "护甲", "Weapon": "武器", "Shield": "盾牌",
    "Melee": "近战", "Ranged": "远程",
    "Melee Weapon Attack": "近战武器攻击", "Ranged Weapon Attack": "远程武器攻击",
    "Melee or Ranged Weapon Attack": "近战或远程武器攻击",
    "Spell Attack": "法术攻击",
    # Armor types
    "Studded Leather": "镶钉皮甲", "Chain Mail": "链甲",
    "Chain Shirt": "链甲衫", "Scale Mail": "鳞甲", "Breastplate": "胸甲",
    "Half Plate": "半身板甲", "Natural Armor": "天生护甲",
    "Ring Mail": "环甲", "Padded Armor": "棉甲", "Leather Armor": "皮甲",
    "Hide Armor": "皮甲", "Splint Armor": "板条甲", "Plate Armor": "全身板甲",
    "Plate": "全身板甲", "Padded": "棉甲", "Leather": "皮甲", "Hide": "皮甲",
    "Splint": "板条甲",
    # Subclass categories
    "Primal Path": "原初道途", "Bard College": "吟游诗人学院",
    "Divine Domain": "神圣领域", "Druid Circle": "德鲁伊结社",
    "Martial Archetype": "武术范型", "Monastic Tradition": "宗派传统",
    "Sacred Oath": "圣誓", "Ranger Archetype": "游侠范型",
    "Roguish Archetype": "游荡者范型", "Sorcerous Origin": "术法起源",
    "Otherworldly Patron": "异界宗主", "Arcane Tradition": "奥法传承",
    "Artificer Specialty": "奇械师专精", "Mystic Order": "灵能宗派",
    "Blood Hunter Order": "血猎人宗派",
    # Common trait labels
    "Trait": "特质", "Ideal": "理念", "Bond": "羁绊", "Flaw": "缺陷",
    "Trinket": "饰品", "Guide": "向导", "Guide Name": "向导姓名",
    "Guide Nature": "向导性格",
    "Physical Characteristics": "身体特征",
    "Subraces and Variants": "子种族与变体", "Subrace": "子种族",
    "Racial Traits": "种族特性",
    "Personality": "个性", "Characteristics": "特性",
    "Appearance": "外表", "High Ability": "高属性", "Low Ability": "低属性",
    "Talent": "天赋", "Mannerism": "习癖", "Interaction Trait": "互动特质",
    "Values": "价值观", "Flaw or Secret": "缺陷或秘密",
    "Alignment": "阵营", "Origin": "出身", "Birthplace": "出生地",
    "Parents": "父母", "Absent Parent": "缺席的父母",
    "Family Lifestyle": "家庭生活方式", "Childhood Home": "童年住所",
    "Childhood Memories": "童年记忆", "Siblings": "兄弟姐妹",
    "Life Events": "人生事件", "Weird Stuff": "奇事",
    "Marriage": "婚姻", "Friend": "朋友", "Enemy": "敌人",
    "Job": "工作", "Someone Important": "重要之人",
    "Adventure": "冒险", "Crime": "罪行",
    "Simultaneous": "同时出生", "Older": "年长", "Younger": "年幼",
    "Twin, triplet, or quadruplet": "双胞胎、三胞胎或四胞胎",
    "Order of Construction": "制造顺序", "Birth Order": "出生顺序",
    "Mother and father": "母亲和父亲",
    "Wretched": "悲惨", "Squalid": "肮脏", "Poor": "贫穷",
    "Modest": "简朴", "Comfortable": "舒适", "Wealthy": "富裕",
    "Aristocratic": "贵族",
    "Hostile": "敌对", "Friendly": "友善", "Indifferent": "漠不关心",
    "Proficient": "熟练", "Expert": "专精", "Immune": "免疫",
    "Vulnerable": "易伤", "Resistant": "抗性",
    "Speaks": "可说", "Understands": "可理解",
    "Wondrous Item": "奇物", "Creator": "创造者", "History": "历史",
    "Property": "特性", "Quirk": "怪癖",
    "Major Property": "主要特性", "Minor Property": "次要特性",
    "Special Property": "特殊特性",
    "Academic": "学者", "Aristocrat": "贵族",
    "Artisan or guild member": "工匠或公会成员",
    "Criminal": "罪犯", "Entertainer": "艺人",
    "Exile, hermit, or refugee": "流放者、隐士或难民",
    "Explorer or wanderer": "探险者或流浪者",
    "Farmer or herder": "农夫或牧民", "Hunter or trapper": "猎人或捕兽者",
    "Laborer": "劳工", "Merchant": "商人",
    "Politician or bureaucrat": "政客或官僚",
    "Priest": "祭司", "Sailor": "水手", "Soldier": "士兵",
    "Adventurer": "冒险者", "Civilian": "平民",
    "Wretched": "悲惨", "Squalid": "肮脏", "Poor": "贫穷",
    "Wealthy": "富裕",
}

# Values to never translate
SKIP_VALUES = {
    "AI","DMG","EBR","EE","EGtW","GGtR","Mod","MOoT","MR",
    "MToF","Other","PHB","SCAG","TCoE","UA","VGtM","XGtE",
    "ERLW","RMB","RMB-EE","RMB-UA",
    "STR","DEX","CON","INT","WIS","CHA",
    "pc","npc","either","standard","real",
}

# Standalone single-word terms needing word boundaries
WORD_TERMS = {
    "Acid","Cold","Fire","Force","Poison","Armor","Shield","Weapon",
    "Dragon","Giant","Plant","Ooze","Fey","Beast","Male","Female",
    "Left","Right","All","Both","Show","Life","Race","Class",
    "Gender","Trait","Ideal","Bond","Flaw","Trinket",
    "Origin","Friend","Enemy","Crime","Lair","Mythic","Regional",
    "History","Property","Quirk","Aspect","Utility","Plan",
    "Criminal","Wretched","Squalid","Poor","Wealthy",
    # Removed from WORD_TERMS (now handled as full phrases only):
    # Guide, Elemental, Arcana - these break book names
}


# ── Fetch & Build Mapping ─────────────────────────────────────────────────

def fetch_mappings(force=False):
    """Download 5etools-cn JSON files and extract ENG_name→name mappings."""
    if os.path.exists(MAPPING_CACHE) and not force:
        with open(MAPPING_CACHE, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(f"Loaded cached mapping: {len(data)} pairs")
            return data

    mapping = dict(EXTRA_MAPPINGS)  # Start with hardcoded (overrides fetched)

    for filename, cfg in CN_SOURCES.items():
        url = f"{CN_BASE}/{filename}"
        print(f"Fetching {filename}...")
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code != 200:
                print(f"  SKIP (HTTP {resp.status_code})")
                continue
            data = resp.json()
            count = _extract_mappings(data, mapping, cfg)
            print(f"  +{count} mappings")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Remove problematic single-word entries that break phrase matching
    # These work better as full phrases only
    _remove_if_shorter_phrase_exists(mapping)

    with open(MAPPING_CACHE, "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent="\t")
    print(f"\nTotal mapping: {len(mapping)} pairs -> {MAPPING_CACHE}")
    return mapping


# Words that should ONLY match as full phrases, not standalone,
# because they appear inside proper names (book titles, etc.)
AMBIGUOUS_TERMS = {
    "Guide", "Elemental", "Arcana", "Races", "Monsters", "Everything",
    "Wildemount", "Ravnica", "Theros", "Eberron", "Acquisitions",
    "Cauldron", "Tome", "Foes", "Odysseys", "Volo", "Xanathar",
    "Mordenkainen", "Tasha", "Sword Coast", "Adventurer",
    "Companion", "Incorporated", "Rising", "Last War",
}


def _remove_if_shorter_phrase_exists(mapping):
    """Remove known-ambiguous single-word terms that break phrase matching."""
    removed = 0
    for term in AMBIGUOUS_TERMS:
        if term in mapping and term not in EXTRA_MAPPINGS:
            del mapping[term]
            removed += 1
    if removed:
        print(f"  Filtered {removed} ambiguous terms")


def _extract_mappings(data, mapping, cfg):
    """Extract ENG_name→name pairs from 5etools-cn data."""
    count = 0
    eng_field = cfg.get("engField")
    name_field = cfg["nameField"]
    array_key = cfg.get("key")

    def walk(obj):
        nonlocal count
        if isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            # Check if this object has both ENG_name and name
            eng = obj.get(eng_field) if eng_field else None
            name = obj.get(name_field)
            if eng and name and eng != name:
                if eng not in mapping:
                    mapping[eng] = name
                    count += 1
                # Also add year-less version for books
                yearless = re.sub(r'\s*\(\d{4}\)\s*$', '', eng).strip()
                if yearless != eng and yearless not in mapping:
                    mapping[yearless] = name
                    count += 1
            # Recurse into children
            for k, v in obj.items():
                if k in (eng_field, name_field):
                    continue
                if isinstance(v, (dict, list)):
                    walk(v)

    if array_key and array_key in data:
        walk(data[array_key])
    else:
        # Walk all top-level sections
        for section, content in data.items():
            if section.startswith("_"):
                continue
            if isinstance(content, dict):
                if array_key and array_key in content:
                    walk(content[array_key])
                else:
                    walk(content)
            elif isinstance(content, list):
                walk(content)

    return count


# ── Apply Mappings to Tetra-cube Files ────────────────────────────────────

def apply_mappings(mapping, dry_run=False, file_list=None):
    """Apply ENG→CN mappings to Tetra-cube JSON files."""
    if file_list is None:
        file_list = TETRA_FILES
    sorted_terms = sorted(mapping.items(), key=lambda x: -len(x[0]))

    for relpath in file_list:
        filepath = TETRA_BASE / relpath
        if not filepath.exists():
            print(f"SKIP: {relpath} (not found)")
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = _apply_to_json(data, sorted_terms)

        if count > 0:
            print(f"{'[DRY RUN] ' if dry_run else ''}{relpath}: {count} replacements")
            if not dry_run:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent="\t")
        else:
            print(f"{relpath}: no matches")


def _apply_to_json(obj, sorted_terms):
    """Recursively apply term replacements to all string values."""
    count = 0
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                new_val = _replace_terms(value, sorted_terms)
                if new_val != value:
                    obj[key] = new_val
                    count += 1
            elif isinstance(value, (dict, list)):
                count += _apply_to_json(value, sorted_terms)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                new_val = _replace_terms(item, sorted_terms)
                if new_val != item:
                    obj[i] = new_val
                    count += 1
            elif isinstance(item, (dict, list)):
                count += _apply_to_json(item, sorted_terms)
    return count


def _replace_terms(text, sorted_terms):
    """Replace known English terms with Chinese, longest-first, word-boundary aware."""
    if not text or not isinstance(text, str):
        return text
    if text in SKIP_VALUES:
        return text
    if not re.search(r'[a-zA-Z]', text):
        return text

    result = text
    for en, zh in sorted_terms:
        # Case-insensitive quick check
        if en.lower() not in result.lower():
            continue
        try:
            if en in WORD_TERMS:
                pat = re.compile(r'\b' + re.escape(en) + r'\b')
            else:
                pat = re.compile(re.escape(en), re.IGNORECASE)
            result = pat.sub(zh, result)
        except re.error:
            continue
    return result


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Schema-map 5etools-cn translations to Tetra-cube JSON files"
    )
    parser.add_argument("action", choices=["fetch", "apply"],
                        help="fetch: download 5etools-cn data; apply: apply to Tetra-cube")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="Preview without writing")
    parser.add_argument("--force", "-f", action="store_true",
                        help="Force re-fetch")
    args = parser.parse_args()

    if args.action == "fetch":
        fetch_mappings(force=args.force)
    elif args.action == "apply":
        mapping = fetch_mappings(force=args.force)
        # Risky files first (targeted handlers)
        _apply_risky_files(mapping, dry_run=args.dry_run)
        # Safe files (full replace)
        safe_files = [f for f in TETRA_FILES if f not in RISKY_FILES]
        apply_mappings(mapping, dry_run=args.dry_run, file_list=safe_files)
        if args.dry_run:
            print("\n[Dry run complete — no files modified]")


# ── Targeted Risky-File Handlers ──────────────────────────────────────────

RISKY_FILES = {
    "dnd/js/JSON/statblockdata.json",
    "dnd/js/JSON/races.json",
    "dnd/js/JSON/classes.json",
    "dnd/js/JSON/backgrounds.json",
    "dnd/js/JSON/names.json",
}


def _apply_risky_files(mapping, dry_run=False):
    """Handle files that have JS lookup keys — be careful what we translate."""
    sorted_terms = sorted(mapping.items(), key=lambda x: -len(x[0]))

    for relpath in RISKY_FILES:
        filepath = TETRA_BASE / relpath
        if not filepath.exists():
            continue

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        basename = os.path.basename(relpath)
        count = 0

        if basename == "statblockdata.json":
            count = _handle_statblockdata(data, sorted_terms)
        elif basename in ("races.json", "classes.json", "backgrounds.json"):
            count = _handle_core_data(data, sorted_terms, mapping)
        elif basename == "names.json":
            count = _handle_names(data, sorted_terms)

        if count > 0:
            print(f"{'[DRY RUN] ' if dry_run else ''}{relpath}: {count} targeted replacements")
            if not dry_run:
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent="\t")
        else:
            print(f"{relpath}: no changes")


def _handle_statblockdata(data, sorted_terms):
    """Translate display text in statblockdata.json, preserve lookup keys."""
    count = 0

    # commonAbilities: translate name and desc (display), NOT realname (identifier)
    if "commonAbilities" in data:
        for ab in data["commonAbilities"]:
            if "name" in ab:
                new_name = _replace_terms(ab["name"], sorted_terms)
                if new_name != ab["name"]:
                    ab["name"] = new_name
                    count += 1
            if "desc" in ab and isinstance(ab["desc"], str):
                new_desc = _replace_terms(ab["desc"], sorted_terms)
                if new_desc != ab["desc"]:
                    ab["desc"] = new_desc
                    count += 1

    # attackTypes: translate (display text)
    if "attackTypes" in data:
        for i, at in enumerate(data["attackTypes"]):
            new_at = _replace_terms(at, sorted_terms)
            if new_at != at:
                data["attackTypes"][i] = new_at
                count += 1

    # defaultPreset: translate name and type fields
    if "defaultPreset" in data:
        dp = data["defaultPreset"]
        for key in ("name", "type", "tag", "alignment", "ac_desc"):
            if key in dp and isinstance(dp[key], str):
                new_val = _replace_terms(dp[key], sorted_terms)
                if new_val != dp[key]:
                    dp[key] = new_val
                    count += 1

    # DO NOT translate: allSkills, allConditions, allNormalDamageTypes,
    # sizes keys, types, armors keys — these are JS lookup keys

    return count


def _handle_core_data(data, sorted_terms, mapping):
    """For races/classes/backgrounds: translate content, preserve top-level keys."""
    count = 0

    if isinstance(data, dict):
        for key, value in data.items():
            # Skip special keys
            if key.startswith("_"):
                continue

            # Translate the content of each entry (not the key itself)
            if isinstance(value, dict):
                count += _translate_content_only(value, sorted_terms)

    return count


def _translate_content_only(obj, sorted_terms):
    """Translate all string values in an object recursively,
    but skip values that look like identifiers."""
    count = 0
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str):
                # Skip values that are clearly identifiers (all lowercase, short)
                if re.match(r'^[a-z][a-z0-9_-]*$', value) and len(value) < 20:
                    continue
                # Skip special values
                if value in SKIP_VALUES:
                    continue
                new_val = _replace_terms(value, sorted_terms)
                if new_val != value:
                    obj[key] = new_val
                    count += 1
            elif isinstance(value, (dict, list)):
                count += _translate_content_only(value, sorted_terms)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, str):
                if re.match(r'^[a-z][a-z0-9_-]*$', item) and len(item) < 20:
                    continue
                if item in SKIP_VALUES:
                    continue
                new_val = _replace_terms(item, sorted_terms)
                if new_val != item:
                    obj[i] = new_val
                    count += 1
            elif isinstance(item, (dict, list)):
                count += _translate_content_only(item, sorted_terms)
    return count


def _handle_names(data, sorted_terms):
    """For names.json: translate category labels, preserve all proper names."""
    count = 0

    if isinstance(data, dict):
        for race_key, race_data in data.items():
            if isinstance(race_data, dict):
                for category_key, category_val in race_data.items():
                    # Translate category labels (Female, Male, Clan, etc.)
                    if isinstance(category_key, str):
                        new_key = _replace_terms(category_key, sorted_terms)
                        if new_key != category_key:
                            # Can't rename key in place, would need restructure
                            # For now, skip key translation to avoid breaking lookups
                            pass

                    # Translate category values if they're labels (not name lists)
                    if isinstance(category_val, str):
                        new_val = _replace_terms(category_val, sorted_terms)
                        if new_val != category_val:
                            race_data[category_key] = new_val
                            count += 1
                    # Skip arrays (name lists) — proper nouns

    return count


if __name__ == "__main__":
    main()
