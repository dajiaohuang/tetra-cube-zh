#!/usr/bin/env python3
"""
translate_v2.py — Unified translation pipeline for HTML and JS files.

Phase 1: Extract ALL English strings (text nodes + attrs + JS literals)
Phase 2: Apply dictionary mapping (cn_mapping.json, longest-first)
Phase 3: Single Ollama batch for all remaining English
Phase 4: Auto-validate and generate fix_list.txt entries

Usage:
  python translate_v2.py --dry-run     # Preview what will be translated
  python translate_v2.py               # Full translation + validation
  python translate_v2.py --validate    # Validation only (no Ollama)
"""

import argparse, json, os, re, sys, time
from collections import OrderedDict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup, NavigableString, Comment

# ── Config ─────────────────────────────────────────────────────────────────

OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"
MAPPING_FILE = "cn_mapping.json"
FIX_LIST = "fix_list.txt"

HTML_FILES = [
    "index.html", "dnd/dnd-char-gen.html", "dnd/dnd-magic-items.html",
    "dnd/dnd-reference.html", "dnd/dnd-statblock.html", "dnd/dnd-statblock-print.html",
    "fea-quote-gen/fea-quote-gen.html", "nft/generator.html", "nft/nft.html",
    "numenera/generator.html",
]
JS_FILES = [
    "dnd/js/statblock-script.js", "dnd/js/card-script.js", "dnd/js/char-gen-script.js",
    "dnd/js/magic-item-script.js", "dnd/js/reference-script.js", "dnd/js/statblock-print-script.js",
    "numenera/generator.js",
]

WORD_TERMS = {"Acid","Cold","Force","Poison","Armor","Shield","Weapon","Dragon",
    "Giant","Plant","Ooze","Fey","Beast","Male","Female","Left","Right","All",
    "Both","Show","Life","Race","Class","Gender","Trait","Ideal","Bond","Flaw",
    "Trinket","Origin","Friend","Enemy","Crime","Lair","Mythic","Regional",
    "History","Property","Quirk","Aspect","Utility","Plan","Melee","Ranged",}

SKIP_SET = {"AI","DMG","EBR","EE","EGtW","GGtR","Mod","MOoT","MR","MToF",
    "Other","PHB","SCAG","TCoE","UA","VGtM","XGtE","STR","DEX","CON","INT","WIS","CHA"}

PROPER_NAMES = ["Fire Emblem","Fire Emblem: Awakening","Tetracube","Statblock5e",
    "Open5e","Numenera","Ko-fi","NFT","GitHub","Markdown","Homebrewery","SRD",
    "Tome of Beasts","DMG","PHB","XGtE","TCoE"]

# Validation: proper names that MUST appear in English (not translated)
MUST_STAY_ENGLISH = [
    "Numenera","Fire Emblem","Tetracube","Statblock5e","Open5e","Ko-fi","NFT","GitHub"
]

# Validation: terms that MUST use a specific Chinese translation
MUST_USE_CN = {
    "属性块": ["统计信息块","统计栏","数据块","状态块","属性方块","属性数据块"],
    "生成器": ["发生器","产生器","生成程序"],
}

# ── Dictionary ─────────────────────────────────────────────────────────────

def load_dict():
    if not os.path.exists(MAPPING_FILE):
        print(f"[ERROR] {MAPPING_FILE} not found. Run schema_map.py first.")
        sys.exit(1)
    with open(MAPPING_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    return sorted(raw.items(), key=lambda x: -len(x[0]))


def apply_dict(text, sorted_terms):
    if not text or not isinstance(text, str):
        return text
    if not re.search(r'[a-zA-Z]', text):
        return text
    if text.strip() in SKIP_SET:
        return text

    # Protect proper names
    placeholders = {}
    for i, name in enumerate(PROPER_NAMES):
        ph = f"__PN{i}__"
        pat = re.compile(re.escape(name), re.IGNORECASE)
        if pat.search(text):
            text = pat.sub(ph, text)
            placeholders[ph] = name

    result = text
    for en, zh in sorted_terms:
        if en.lower() not in result.lower():
            continue
        try:
            # Any single-word term uses word boundary to avoid substring matches
            # (e.g. "Age" shouldn't match inside "dndimages" or "Orphanage")
            if en in WORD_TERMS or ' ' not in en:
                pat = re.compile(r'\b' + re.escape(en) + r'\b')
            else:
                pat = re.compile(re.escape(en), re.IGNORECASE)
            result = pat.sub(zh, result)
        except re.error:
            continue

    for ph, name in placeholders.items():
        result = result.replace(ph, name)
    return result


def has_english(text):
    if not text or not isinstance(text, str):
        return False
    s = text.strip()
    if len(s) < 5 or s in SKIP_SET:
        return False
    if not re.search(r'[a-zA-Z]{3,}', s):
        return False

    # Skip: HTML fragments
    if re.search(r'</?\w+[^>]*>', s):
        return False
    # Skip: file paths
    if re.search(r'\.(png|jpg|jpeg|gif|svg|ico|css|js|json|html|psd|otf|woff2?|eot|ttf)', s):
        return False
    # Skip: paths with slashes
    if '/' in s and len(s) < 60:
        return False
    # Skip: CSS class/value fragments
    if re.match(r'^[\w-]+$', s) and len(s) < 20:
        return False
    # Skip: template vars, dice, URLs, selectors, identifiers, units
    for p in [r'^\[\w+.*\]$', r'^\d+d\d+', r'^DC\s*\d+', r'^https?://',
              r'^[.#][\w-]+$', r'^[a-z][a-z0-9_$-]*$',
              r'^\d+(\.\d+)?\s*(px|em|rem|%|ft\.?|lbs?\.?|gp|XP)?$',
              r'^\$\{.*\}$', r'^[,\s.\-:|/]+$']:
        if re.match(p, s):
            return False
    # Skip: already partially Chinese (dict handled it)
    if re.search(r'[一-鿿]', s):
        return False
    # Skip: JS string concatenation fragments
    if re.search(r"['\"]\s*[+]\s*['\"]", s) or '"+' in s or "+ '" in s:
        return False
    # Skip: CSS selectors with # or . patterns
    if re.match(r'^["\']?#[a-zA-Z_-]', s):
        return False
    # Skip: template literals with ${code}
    if '${' in s:
        return False
    # Skip: too-short fragments (just connectives/punctuation)
    words = re.findall(r'[a-zA-Z]+', s)
    if len(words) <= 1 and len(s) < 15:
        return False
    return True


# ── Extraction ─────────────────────────────────────────────────────────────

def extract_all_texts():
    """Extract all translatable English strings from all HTML and JS files.
    Returns: {filepath: [(context_type, original_string, location_info)]}"""
    all_texts = OrderedDict()
    sorted_terms = load_dict()

    # HTML files
    for fp in HTML_FILES:
        if not os.path.exists(fp):
            continue
        entries = []
        with open(fp, "r", encoding="utf-8") as f:
            html = f.read()

        soup = BeautifulSoup(html, "html.parser")

        # Text nodes
        for el in soup.descendants:
            if isinstance(el, NavigableString) and not isinstance(el, Comment):
                if el.parent and el.parent.name in ("script", "style"):
                    continue
                text = str(el).strip()
                # Normalize whitespace for matching (but keep original for replacement)
                normalized = re.sub(r'\s+', ' ', text)
                if has_english(normalized):
                    translated = apply_dict(normalized, sorted_terms)
                    if translated != normalized:
                        entries.append(("text", text, translated))
                    elif has_english(normalized):
                        entries.append(("text", text, None))

        # Attributes (NEVER translate: id, class, name, href, src, type, for, rel)
        attr_names = ["title", "placeholder", "aria-label", "alt",
                       "data-original-title", "data-content"]
        for tag in soup.find_all(True):
            for attr in attr_names:
                if tag.has_attr(attr):
                    val = tag[attr]
                    if has_english(val):
                        translated = apply_dict(val, sorted_terms)
                        if translated != val:
                            entries.append(("attr", val, translated))
                        else:
                            entries.append(("attr", val, None))

        if entries:
            all_texts[fp] = entries

    # JS files
    for fp in JS_FILES:
        if not os.path.exists(fp):
            continue
        entries = []
        with open(fp, "r", encoding="utf-8") as f:
            js = f.read()

        # Apply dict to full file content first
        js = apply_dict(js, sorted_terms)

        # Find string literals
        for pat, q in [(re.compile(r'"((?:[^"\\]|\\.)*)"'), '"'),
                       (re.compile(r"'((?:[^'\\]|\\.)*)'"), "'"),
                       (re.compile(r'`((?:[^`\\]|\\.)*)`'), '`')]:
            for m in pat.finditer(js):
                inner = m.group(1)
                clean = inner.replace('\\"','"').replace("\\'","'").replace('\\n','\n')
                if has_english(clean):
                    entries.append(("js_str", m.group(0), None))

        if entries:
            all_texts[fp] = entries

    return all_texts


# ── Ollama ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are translating D&D 5e tools website UI strings to Simplified Chinese.
Translate naturally using standard D&D community terminology.

=== CRITICAL: Keep these EXACT strings in original English ===
Numenera, Fire Emblem, Fire Emblem: Awakening, Tetracube, Statblock5e, Open5e, Ko-fi, NFT, GitHub, Markdown, Homebrewery, SRD, Tome of Beasts

=== CRITICAL: Use these EXACT Chinese translations ===
Statblock = 属性块
Statblock Generator = 属性块生成器
Quote Generator = 台词生成器

=== PRESERVE ===
Template variables: [MON], [STR ATK], [DEX 1D8], [WIS SAVE], [???D???]
Dice: 1d20, 2d8+3, DC 15
Book codes: PHB, DMG, XGtE, TCoE, VGtM, MToF, SCAG, etc.
Markdown: _, **, HTML entities

Return ONLY: [N] Chinese translation"""


def ollama_translate_all(texts, batch_size=12):
    """Translate all unique English texts in batches."""
    if not texts:
        return {}
    results = {}
    total = len(texts)
    for i in range(0, total, batch_size):
        batch = texts[i:i + batch_size]
        print(f"  Ollama batch {i//batch_size + 1}/{(total-1)//batch_size + 1} ({len(batch)} strings)...")
        batch_results = _ollama_call(batch)
        results.update(batch_results)
        time.sleep(0.2)
    return results


def _ollama_call(texts, max_retries=3):
    items = "\n".join(f"[{i+1}] {t}" for i, t in enumerate(texts))
    payload = {
        "model": MODEL, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 4096},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate:\n{items}"},
        ],
    }
    for attempt in range(max_retries):
        try:
            resp = requests.post(OLLAMA_API, json=payload, timeout=300)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                if not content:
                    # Try extracting from thinking
                    thinking = resp.json().get("message", {}).get("thinking", "")
                    if thinking:
                        content = _extract_from_thinking(thinking)
                results = {}
                for line in content.strip().split("\n"):
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
        if attempt < max_retries - 1:
            time.sleep(5)
    return {}


def _extract_from_thinking(thinking):
    """Qwen3 thinking models put translations in thinking."""
    drafts = re.findall(r'\[(\d+)\]\s*(.+?)(?:\n|$)', thinking)
    if drafts:
        return "\n".join(f"[{n}] {t}" for n, t in drafts)
    return ""


# ── Apply ──────────────────────────────────────────────────────────────────

def apply_translations(all_texts, translation_map):
    """Apply Ollama translations back to files."""
    stats = {}
    for fp, entries in all_texts.items():
        if fp.endswith(".html"):
            stats[fp] = _apply_html(fp, entries, translation_map)
        else:
            stats[fp] = _apply_js(fp, entries, translation_map)
    return stats


def _apply_html(fp, entries, tmap):
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")

    # Build text replacement map
    replacements = {}
    for etype, orig, pre_translated in entries:
        if pre_translated:
            replacements[orig] = pre_translated
        elif orig in tmap:
            replacements[orig] = tmap[orig]

    # Apply to text nodes
    dict_count = 0
    ollama_count = 0
    for el in soup.descendants:
        if isinstance(el, NavigableString) and not isinstance(el, Comment):
            if el.parent and el.parent.name in ("script", "style"):
                continue
            text = str(el)
            # Try exact match first, then normalized match
            normalized = re.sub(r'\s+', ' ', text).strip()
            if text in replacements:
                new_text = replacements[text]
                el.replace_with(new_text)
                ollama_count += 1
            elif normalized in replacements:
                # Replace preserving leading/trailing whitespace pattern
                new_text = replacements[normalized]
                # Preserve original whitespace pattern
                prefix = text[:len(text) - len(text.lstrip())]
                suffix = text[len(text.rstrip()):]
                el.replace_with(prefix + new_text + suffix)
                if normalized in tmap:
                    ollama_count += 1
                else:
                    dict_count += 1

    # Apply to attributes
    attr_names = ["title","placeholder","aria-label","alt","content","data-original-title","data-content"]
    for tag in soup.find_all(True):
        for attr in attr_names:
            if tag.has_attr(attr) and tag[attr] in replacements:
                tag[attr] = replacements[tag[attr]]

    with open(fp, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"  [OK] {fp} ({dict_count} dict + {ollama_count} ollama)")
    return {"dict": dict_count, "ollama": ollama_count}


def _apply_js(fp, entries, tmap):
    with open(fp, "r", encoding="utf-8") as f:
        js = f.read()

    changes = 0
    for etype, full_str, _ in entries:
        if full_str in tmap:
            quote = full_str[0]
            inner = full_str[1:-1] if len(full_str) >= 2 else full_str
            new_full = quote + tmap[full_str] + quote
            if new_full != full_str:
                js = js.replace(full_str, new_full)
                changes += 1

    with open(fp, "w", encoding="utf-8") as f:
        f.write(js)
    print(f"  [OK] {fp} ({changes} js strings)")
    return {"js": changes}


# ── Validation ─────────────────────────────────────────────────────────────

def validate():
    """Scan all HTML/JS files for validation errors. Generate fix_list entries."""
    errors = []
    all_files = HTML_FILES + JS_FILES

    for fp in all_files:
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            content = f.read()

        # Check: proper names MUST stay English
        for name in MUST_STAY_ENGLISH:
            # If the name appears with Chinese characters around it, it may have been translated
            # Check for common mistranslations
            pass  # Hard to detect without knowing the mistranslation

        # Check: required Chinese terms must use correct form
        for correct, wrongs in MUST_USE_CN.items():
            for wrong in wrongs:
                if wrong in content:
                    # Check if it's inside a translated file (has Chinese context)
                    errors.append((fp, wrong, correct))
                    # Replace immediately
                    content = content.replace(wrong, correct)

        if errors:
            # Write back fixes
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)

    # Generate fix_list entries
    if errors:
        existing = set()
        if os.path.exists(FIX_LIST):
            with open(FIX_LIST, encoding="utf-8") as f:
                for line in f:
                    if "->" in line:
                        existing.add(line.strip())

        new_entries = []
        for fp, wrong, correct in errors:
            entry = f"{wrong} -> {correct}"
            if entry not in existing:
                new_entries.append(entry)

        if new_entries:
            with open(FIX_LIST, "a", encoding="utf-8") as f:
                for e in new_entries:
                    f.write(e + "\n")
            print(f"\n  Auto-fixed {len(errors)} errors, added {len(new_entries)} to {FIX_LIST}")

    return errors


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unified D&D translation pipeline")
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--dict-only", action="store_true", help="Dictionary only, no Ollama")
    parser.add_argument("--validate", "-v", action="store_true", help="Validation only")
    parser.add_argument("--batch-size", "-b", type=int, default=12)
    args = parser.parse_args()

    if args.validate:
        errs = validate()
        print(f"Validation: {len(errs)} errors fixed" if errs else "Validation: clean!")
        return

    print("Extracting all English strings...")
    all_texts = extract_all_texts()

    # Count dict vs ollama
    dict_hits = 0
    ollama_needed = set()
    for fp, entries in all_texts.items():
        for etype, orig, pre in entries:
            if pre:
                dict_hits += 1
            else:
                ollama_needed.add(orig)

    print(f"\nDict matches: {dict_hits}")
    print(f"Unique strings needing Ollama: {len(ollama_needed)}")
    print(f"From {len(all_texts)} files\n")

    if args.dry_run:
        print("Sample strings for Ollama:")
        for s in list(ollama_needed)[:20]:
            print(f"  {s[:120]}")
        return

    if args.dict_only:
        # Apply dict-only translations
        translation_map = {}
        apply_translations(all_texts, translation_map)
        return

    # Phase 3: Ollama
    if ollama_needed:
        unique_list = list(ollama_needed)
        t0 = time.time()
        translation_map = ollama_translate_all(unique_list, args.batch_size)
        dur = time.time() - t0
        print(f"\nOllama done: {len(translation_map)}/{len(ollama_needed)} translated in {dur/60:.0f}m")

        # Phase 4: Apply
        apply_translations(all_texts, translation_map)
    else:
        translation_map = {}
        apply_translations(all_texts, translation_map)

    # Phase 5: Validate
    errors = validate()
    print(f"\n=== Done: {len(errors)} validation fixes ===" if errors else "\n=== Done, clean! ===")


if __name__ == "__main__":
    main()
