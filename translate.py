#!/usr/bin/env python3
"""
translate.py - Phase 2: Dictionary + Ollama for HTML and JS files.
Loads cn_mapping.json (built by schema_map.py) as the dictionary.
Usage:
  python translate.py --all --dry-run
  python translate.py --all
  python translate.py --file index.html
"""

import argparse, json, os, re, sys, time

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup, NavigableString, Comment

# ── Config ─────────────────────────────────────────────────────────────────

OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"
BATCH_SIZE = 8

# ── Load dictionary from schema_map.py output ──────────────────────────────

def load_dict():
    if not os.path.exists("cn_mapping.json"):
        print("[ERROR] cn_mapping.json not found. Run 'python schema_map.py fetch' first.")
        sys.exit(1)
    with open("cn_mapping.json", encoding="utf-8") as f:
        raw = json.load(f)
    # Sort longest-first for safe replacement
    return sorted(raw.items(), key=lambda x: -len(x[0]))


# ── Dictionary matching ────────────────────────────────────────────────────

# Single words that should use word-boundary matching
WORD_TERMS = {
    "Acid","Cold","Force","Poison","Armor","Shield","Weapon",
    "Dragon","Giant","Plant","Ooze","Fey","Beast","Male","Female",
    "Left","Right","All","Both","Show","Life","Race","Class",
    "Gender","Trait","Ideal","Bond","Flaw","Trinket",
    "Origin","Friend","Enemy","Crime","Lair","Mythic","Regional",
    "History","Property","Quirk","Aspect","Utility","Plan","Melee","Ranged",
    # Note: "Fire" removed — breaks "Fire Emblem" proper name
}

SKIP_SET = {
    "AI","DMG","EBR","EE","EGtW","GGtR","Mod","MOoT","MR",
    "MToF","Other","PHB","SCAG","TCoE","UA","VGtM","XGtE",
    "STR","DEX","CON","INT","WIS","CHA",
}

# Proper names that contain dictionary words — protected from partial matching
PROPER_NAMES = [
    "Fire Emblem",
    "Fire Emblem: Awakening",
    "Fire Emblem: Awakening Quote Generator",
    "Statblock5e",
    "Open5e",
    "Tetra",
    "Tetracube",
    "Ko-fi",
    "NFT",
    "Numenera",
    "GitHub",
]


def apply_dict(text, sorted_terms):
    """Replace known English terms with Chinese."""
    if not text or not isinstance(text, str):
        return text
    if not re.search(r'[a-zA-Z]', text):
        return text
    if text.strip() in SKIP_SET:
        return text

    # Protect proper names from partial matching by temporarily replacing them
    placeholders = {}
    for i, name in enumerate(PROPER_NAMES):
        placeholder = f"__PROPER_{i}__"
        # Case-insensitive protection
        pat = re.compile(re.escape(name), re.IGNORECASE)
        if pat.search(text):
            text = pat.sub(placeholder, text)
            placeholders[placeholder] = name  # Keep original English

    result = text
    for en, zh in sorted_terms:
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

    # Restore proper names
    for placeholder, name in placeholders.items():
        result = result.replace(placeholder, name)

    return result


def has_english(text):
    """Check if text still contains English needing Ollama."""
    if not text or not isinstance(text, str):
        return False
    s = text.strip()
    if len(s) < 3 or not re.search(r'[a-zA-Z]{3,}', s):
        return False
    if s in SKIP_SET:
        return False
    # Skip template variables, dice, URLs, CSS selectors, JS identifiers
    for p in [r'^\[\w+.*\]$', r'^\d+d\d+', r'^DC\s*\d+', r'^https?://',
              r'^[.#][\w-]+$', r'^[a-z][a-z0-9_$-]*$', r'^</?\w+>$',
              r'^\d+(\.\d+)?\s*(px|em|rem|%|ft\.?|lbs?\.?|gp|XP)?$']:
        if re.match(p, s):
            return False
    return True


# ── Ollama ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are translating a D&D 5e tools website to Simplified Chinese.

=== CRITICAL: These EXACT strings MUST remain in original English ===
Numenera, Fire Emblem, Fire Emblem: Awakening, Tetracube, Statblock5e, Open5e, Ko-fi, NFT, GitHub, Markdown, Homebrewery, SRD, Tome of Beasts, DMG, PHB, XGtE, TCoE

=== CRITICAL: Use these EXACT Chinese translations ===
Statblock = 属性块
Statblock Generator = 属性块生成器

=== PRESERVE EXACTLY ===
- Template variables: [MON], [STR ATK], [DEX 1D8], [WIS SAVE], [???D???]
- Dice expressions: 1d20, 2d8+3, DC 15, all numbers
- Book codes: PHB, DMG, XGtE, TCoE, VGtM, MToF, EBR, EE, EGtW, GGtR, MOoT, SCAG, AI, MR, Mod, Other, UA
- Stat abbreviations: STR, DEX, CON, INT, WIS, CHA
- Markdown formatting: _, **, HTML entities

Return ONLY numbered translations, no extra text.
Format: [N] Chinese translation"""


def ollama_translate(texts):
    if not texts:
        return {}
    items = "\n".join(f"[{i+1}] {t}" for i, t in enumerate(texts))
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate:\n{items}"},
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 4096},
    }
    for attempt in range(3):
        try:
            resp = requests.post(OLLAMA_API, json=payload, timeout=300)
            if resp.status_code == 200:
                c = resp.json().get("message", {}).get("content", "")
                results = {}
                for line in c.strip().split("\n"):
                    m = re.match(r'\[(\d+)\]\s*(.+)', line.strip())
                    if m:
                        idx = int(m.group(1)) - 1
                        if 0 <= idx < len(texts):
                            t = m.group(2).strip()
                            if t and t != "[UNTRANSLATED]" and t != texts[idx]:
                                results[texts[idx]] = t
                return results
            print(f"    [WARN] HTTP {resp.status_code}")
        except Exception as e:
            print(f"    [WARN] {e}")
        if attempt < 2:
            time.sleep(3)
    return {}


# ── HTML ────────────────────────────────────────────────────────────────────

def translate_html(filepath, sorted_terms, dry_run=False, dict_only=False):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    soup = BeautifulSoup(original, "html.parser")

    # Phase 1: Dictionary
    dict_count = 0
    remaining = []
    for el in soup.descendants:
        if isinstance(el, NavigableString) and not isinstance(el, Comment):
            if el.parent and el.parent.name in ("script", "style"):
                continue
            text = str(el)
            if re.search(r'[a-zA-Z]', text.strip()):
                new_text = apply_dict(text, sorted_terms)
                if new_text != text:
                    el.replace_with(new_text)
                    dict_count += 1
                elif has_english(text.strip()):
                    remaining.append(el)

    print(f"  Dict: {dict_count} nodes replaced, remaining English: {len(remaining)}")
    if not remaining or dry_run or dict_only:
        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(str(soup))
            if dict_only and remaining:
                print(f"  [OK] Dict-only save ({dict_count} changes, {len(remaining)} left for Ollama)")
            elif not remaining:
                print(f"  [OK] All translated by dictionary ({dict_count} changes)")
        elif remaining:
            for node in remaining[:10]:
                print(f"    -> {str(node).strip()[:100]}")
        return

    # Phase 2: Ollama
    _ollama_html(remaining, soup, filepath, dict_count)


def _ollama_html(nodes, soup, filepath, dict_count):
    unique = list(dict.fromkeys(str(n).strip() for n in nodes if has_english(str(n).strip())))
    translated = {}
    for i in range(0, len(unique), BATCH_SIZE):
        batch = unique[i:i + BATCH_SIZE]
        print(f"  Ollama {i//BATCH_SIZE + 1}/{(len(unique)-1)//BATCH_SIZE + 1}...")
        translated.update(ollama_translate(batch))
        time.sleep(0.3)

    for node in nodes:
        s = str(node).strip()
        if s in translated:
            node.replace_with(translated[s])

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"  [OK] {filepath} ({dict_count} dict + {len(translated)} ollama)")


# ── JS ──────────────────────────────────────────────────────────────────────

def translate_js(filepath, sorted_terms, dry_run=False, dict_only=False):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    # Phase 1: Dictionary on full text
    result = apply_dict(original, sorted_terms)
    dict_count = 1 if result != original else 0

    # Phase 2: Find string literals still in English
    patterns = [
        (re.compile(r'"((?:[^"\\]|\\.)*)"'), '"'),
        (re.compile(r"'((?:[^'\\]|\\.)*)'"), "'"),
        (re.compile(r'`((?:[^`\\]|\\.)*)`'), '`'),
    ]
    candidates = {}
    for pat, q in patterns:
        for m in pat.finditer(result):
            inner = m.group(1)
            clean = inner.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n')
            if has_english(clean):
                full = m.group(0)
                if full not in candidates:
                    candidates[full] = []
                candidates[full].append((m.start(), m.end()))

    print(f"  Dict: {'yes' if dict_count else 'none'}, remaining English strings: {len(candidates)}")

    if not candidates or dry_run or dict_only:
        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result)
            if dict_only and candidates:
                print(f"  [OK] Dict-only save ({len(candidates)} strings left for Ollama)")
        elif candidates:
            for s in list(candidates.keys())[:10]:
                inner = s[1:-1] if len(s) > 2 else s
                print(f"    -> {inner[:100]}")
        return

    # Phase 2: Ollama
    inners = [s[1:-1] if len(s) >= 2 else s for s in candidates]
    translated = {}
    for i in range(0, len(inners), BATCH_SIZE):
        batch = inners[i:i + BATCH_SIZE]
        print(f"  Ollama {i//BATCH_SIZE + 1}/{(len(inners)-1)//BATCH_SIZE + 1}...")
        translated.update(ollama_translate(batch))
        time.sleep(0.3)

    # Apply
    repl = []
    for full_str, matches in candidates.items():
        q = full_str[0]
        inner = full_str[1:-1] if len(full_str) >= 2 else full_str
        if inner in translated:
            new_full = q + translated[inner] + q
            for start, end in matches:
                repl.append((start, end, new_full))
    repl.sort(key=lambda x: x[0], reverse=True)
    chars = list(result)
    for start, end, new_str in repl:
        chars[start:end] = new_str

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("".join(chars))
    print(f"  [OK] {filepath} ({dict_count} dict + {len(translated)} ollama)")


# ── File lists ─────────────────────────────────────────────────────────────

HTML_FILES = [
    "index.html",
    "dnd/dnd-char-gen.html",
    "dnd/dnd-magic-items.html",
    "dnd/dnd-reference.html",
    "dnd/dnd-statblock.html",
    "dnd/dnd-statblock-print.html",
    "fea-quote-gen/fea-quote-gen.html",
    "nft/generator.html",
    "nft/nft.html",
    "numenera/generator.html",
]

JS_FILES = [
    "dnd/js/statblock-script.js",
    "dnd/js/card-script.js",
    "dnd/js/char-gen-script.js",
    "dnd/js/magic-item-script.js",
    "dnd/js/reference-script.js",
    "dnd/js/statblock-print-script.js",
    "numenera/generator.js",
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", "-a", action="store_true")
    parser.add_argument("--file", "-f")
    parser.add_argument("--type", "-t", choices=["html","js","auto"], default="auto")
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--dict-only", action="store_true", help="Skip Ollama, dict replacement only")
    args = parser.parse_args()

    sorted_terms = load_dict()
    print(f"Loaded {len(sorted_terms)} dictionary entries")

    dict_only = args.dict_only

    def run(fp, ft):
        print(f"\n=== {fp} ===")
        if ft == "html":
            translate_html(fp, sorted_terms, args.dry_run, dict_only=dict_only)
        elif ft == "js":
            translate_js(fp, sorted_terms, args.dry_run, dict_only=dict_only)

    if args.all:
        for fp in HTML_FILES:
            if os.path.exists(fp):
                run(fp, "html")
        for fp in JS_FILES:
            if os.path.exists(fp):
                run(fp, "js")
        print("\n=== Done ===")
    elif args.file:
        fp = args.file
        if not os.path.exists(fp):
            print(f"Not found: {fp}"); sys.exit(1)
        ft = args.type
        if ft == "auto":
            ext = os.path.splitext(fp)[1].lower()
            ft = {"html":"html","htm":"html","js":"js"}.get(ext, "html")
        run(fp, ft)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
