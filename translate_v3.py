#!/usr/bin/env python3
"""
translate_v3.py — Final safe translation pipeline.

Three-phase design:
  Phase 1: PROTECT — replace fragile patterns (IDs, JS hooks) with UUID placeholders
  Phase 2: EXTRACT + DICT + OLLAMA — normalize whitespace, dict-first, Ollama rest
  Phase 3: RESTORE + VALIDATE — put back protected patterns, scan for leaks

Usage:
  python translate_v3.py                # Full pipeline
  python translate_v3.py --dry-run      # Preview only
  python translate_v3.py --validate     # Validation only
"""

import argparse, json, os, re, sys, time, uuid
from collections import OrderedDict

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import requests
from bs4 import BeautifulSoup, NavigableString, Comment

# ── Config ─────────────────────────────────────────────────────────────────

OLLAMA_API = "http://localhost:11434/api/chat"
MODEL = "qwen2.5:14b"
MAPPING_FILE = "cn_mapping.json"
BATCH_SIZE = 12

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
    "Giant","Plant","Ooze","Fey","Beast","Male","Female","All","Both","Show",
    "Life","Race","Class","Gender","Trait","Ideal","Bond","Flaw","Trinket",
    "Origin","Friend","Enemy","Crime","Lair","Mythic","Regional","History",
    "Property","Quirk","Aspect","Utility","Plan","Melee","Ranged",}

SKIP_SET = {"AI","DMG","EBR","EE","EGtW","GGtR","Mod","MOoT","MR","MToF",
    "Other","PHB","SCAG","TCoE","UA","VGtM","XGtE","STR","DEX","CON","INT","WIS","CHA",
    "(AI)","(DMG)","(EBR)","(EE)","(EGtW)","(GGtR)","(Mod)","(MOoT)","(MR)",
    "(MToF)","(Other)","(PHB)","(SCAG)","(TCoE)","(UA)","(VGtM)","(XGtE)"}

# ── Phase 0: Protection Patterns ──────────────────────────────────────────

# Regex patterns for content that must NEVER be translated
# Each pattern is replaced with a UUID placeholder before translation
# Patterns that must survive translation untouched
_protect_counter = [0]

def _next_zz(prefix):
    _protect_counter[0] += 1
    return f"ZZ{prefix}{_protect_counter[0]}ZZ"

PROTECT_PATTERNS = [
    # HTML IDs — replace attribute VALUE only, keep id="..." structure
    (re.compile(r'(\bid=")([^"]*)(")'), lambda m: m.group(1) + _next_zz("ID") + m.group(3)),
    # Event handlers — replace entire attribute with token in valid attribute syntax
    (re.compile(r'(\bon\w+=")([^"]*)(")'), lambda m: m.group(1) + _next_zz("EVENT") + m.group(3)),
    # D&D template variables
    (re.compile(r'\[MON\]'), 'ZZMONZZ'),
    (re.compile(r'\[MONS\]'), 'ZZMONSZZ'),
    (re.compile(r'\[\w+\s+\w+\]'), 'ZZTEMPLATEZZ'),
    (re.compile(r'\[\?\?\?D\?\?\?\]'), 'ZZDICEZZ'),
    # JS template literals
    (re.compile(r'\$\{[^}]+\}'), 'ZZLITZZ'),
]

# Words that must stay English — replaced with ZZ-prefixed variants
# Pattern: (regex, replacement_word)
PROTECT_WORDS = [
    # JS function hooks
    (r'\bDropdowns\b', 'ZZDROPDOWNS'),
    (r'\bAddToTraitList\b', 'ZZADDTRAIT'),
    (r'\bShowHide\w+\b', 'ZZSHOWHIDE'),
    (r'\bTrySaveFile\b', 'ZZTRYSAVE'),
    (r'\bTryPrint\b', 'ZZTRYPRINT'),
    (r'\bTryImage\b', 'ZZTRYIMAGE'),
    (r'\bTryMarkdown\b', 'ZZTRYMD'),
    (r'\bPrintMultiple\b', 'ZZPRINTMULTI'),
    (r'\bLoadFilePrompt\b', 'ZZLOADFILE'),
    (r'\bGenerateHomebrew\b', 'ZZGENHB'),
    (r'\bGenerateDMG\b', 'ZZGENDMG'),
    (r'\bGetPreset\b', 'ZZGETPRESET'),
    (r'\bUpdateList\b', 'ZZUPDATELIST'),
    # Proper names
    (r'\bNumenera\b', 'ZZNUMENERA'),
    (r'\bFire Emblem\b', 'ZZFIREEMBLEM'),
    (r'\bTetracube\b', 'ZZTETRACUBE'),
    (r'\bStatblock5e\b', 'ZZSB5E'),
    (r'\bOpen5e\b', 'ZZO5E'),
    (r'\bKo-fi\b', 'ZZKOFI'),
    (r'\bNFT\b', 'ZZNFT'),
    (r'\bGitHub\b', 'ZZGITHUB'),
    (r'\bMarkdown\b', 'ZZMARKDOWN'),
    (r'\bHomebrewery\b', 'ZZHOMEBREWERY'),
    (r'\bSRD\b', 'ZZSRD'),
    (r'\bTome of Beasts\b', 'ZZTOB'),
    # Book codes
    (r'\bPHB\b', 'ZZPHB'),
    (r'\bDMG\b', 'ZZDMG'),
    (r'\bXGtE\b', 'ZZXGTE'),
    (r'\bTCoE\b', 'ZZTCOE'),
    (r'\bVGtM\b', 'ZZVGTM'),
    (r'\bMToF\b', 'ZZMTOF'),
    (r'\bSCAG\b', 'ZZSCAG'),
    (r'\bEE\b', 'ZZEE'),
    (r'\bEBR\b', 'ZZEBR'),
    (r'\bEGtW\b', 'ZZEGTW'),
    (r'\bGGtR\b', 'ZZGGTR'),
    (r'\bMOoT\b', 'ZZMOOT'),
    (r'\bUA\b', 'ZZUA'),
]


def _make_replacer(mapping, token):
    def replacer(m):
        mapping[token] = m.group(0)
        return token
    return replacer


def protect(text):
    """Replace fragile patterns with ZZ-tokens. Returns (protected_text, mapping)."""
    mapping = {}
    result = text

    # PROTECT_PATTERNS: whole-attribute/expression replacements
    for pattern, replacement in PROTECT_PATTERNS:
        if callable(replacement):
            # Lambda replacement — generate unique token per match
            def _make_dynamic(pat, repl_fn):
                def _replacer(m):
                    token = repl_fn(m)
                    mapping[token] = m.group(0)
                    return token
                return _replacer
            result = pattern.sub(_make_dynamic(pattern, replacement), result)
        else:
            result = pattern.sub(_make_replacer(mapping, replacement), result)

    # PROTECT_WORDS: word-boundary replacements
    for pattern_str, replacement_word in PROTECT_WORDS:
        pat = re.compile(pattern_str)
        result = pat.sub(_make_replacer(mapping, replacement_word), result)

    return result, mapping


def restore(text, mapping):
    """Restore ZZ-tokens back to original content."""
    for token, original in mapping.items():
        text = text.replace(token, original)
    return text


# ── Dictionary ─────────────────────────────────────────────────────────────

def load_dict():
    with open(MAPPING_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    return sorted(raw.items(), key=lambda x: -len(x[0]))


def apply_dict(text, sorted_terms):
    if not text or not isinstance(text, str):
        return text
    if not re.search(r'[a-zA-Z]', text) or text.strip() in SKIP_SET:
        return text

    result = text
    for en, zh in sorted_terms:
        if en.lower() not in result.lower():
            continue
        try:
            if en in WORD_TERMS or ' ' not in en:
                pat = re.compile(r'\b' + re.escape(en) + r'\b')
            else:
                pat = re.compile(re.escape(en), re.IGNORECASE)
            result = pat.sub(zh, result)
        except re.error:
            continue
    return result


def has_english(text):
    if not text or not isinstance(text, str):
        return False
    s = text.strip()
    if len(s) < 4 or s in SKIP_SET:
        return False
    # Must have real English beyond ZZ tokens
    real_text = re.sub(r'ZZ\w+ZZ', '', s)
    if not re.search(r'[a-zA-Z]{3,}', real_text):
        return False
    if not real_text.strip():
        return False
    # Skip code-like strings
    for p in [r'^\[\w+.*\]$', r'^\d+d\d+', r'^DC\s*\d+', r'^https?://',
              r'^[.#][\w-]+$', r'^[a-z][a-z0-9_$-]*$', r'^</?\w+>$',
              r'^\$\{.*\}$', r'^\d+(\.\d+)?\s*(px|em|rem|%|ft|lb|gp|XP)?$']:
        if re.match(p, real_text.strip()):
            return False
    if re.search(r'\.(png|jpg|css|js|json|html|ico|svg|woff|ttf|otf)', real_text):
        return False
    if '/' in s and len(s) < 50:
        return False
    return True


# ── Ollama ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are translating a D&D 5e tools website UI to Simplified Chinese.

CRITICAL RULES:
1. Output ONLY: [N] Chinese translation (one per line)
2. PRESERVE EXACTLY all tokens starting with ZZ (like ZZMONZZ, ZZPHB, ZZNFT, etc.) — these are placeholders, copy them as-is
3. PRESERVE dice expressions (1d20, 2d8+3, DC 15) and all numbers
4. Translate naturally using standard Chinese D&D community terms
5. No extra text, no explanations"""


def ollama_translate(texts):
    if not texts:
        return {}
    results = {}
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        print(f"  Ollama {i//BATCH_SIZE + 1}/{(len(texts)-1)//BATCH_SIZE + 1}...")
        batch_results = _ollama_call(batch)
        results.update(batch_results)
        time.sleep(0.2)
    return results


def _ollama_call(texts):
    items = "\n".join(f"[{i+1}] {t}" for i, t in enumerate(texts))
    payload = {
        "model": MODEL, "stream": False,
        "options": {"temperature": 0.0, "num_predict": 4096},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Translate:\n{items}"},
        ],
    }
    for attempt in range(3):
        try:
            resp = requests.post(OLLAMA_API, json=payload, timeout=300)
            if resp.status_code == 200:
                content = resp.json().get("message", {}).get("content", "")
                if not content:
                    thinking = resp.json().get("message", {}).get("thinking", "")
                    if thinking:
                        drafts = re.findall(r'\[(\d+)\]\s*(.+?)(?:\n|$)', thinking)
                        content = "\n".join(f"[{n}] {t}" for n, t in drafts)
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
        if attempt < 2:
            time.sleep(5)
    return {}


# ── Main Pipeline ──────────────────────────────────────────────────────────

def process_html(filepath, sorted_terms, translation_map, dry_run=False):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    # Phase 1: PROTECT — replace fragile patterns
    protected, pmap = protect(original)

    # Phase 2: EXTRACT text nodes + safe attributes
    soup = BeautifulSoup(protected, "html.parser")

    # Collect text nodes
    replacements = {}  # raw_text -> translated_text
    ollama_set = set()

    for el in soup.descendants:
        if isinstance(el, NavigableString) and not isinstance(el, Comment):
            if el.parent and el.parent.name in ("script", "style"):
                continue
            text = str(el)
            if not re.search(r'[a-zA-Z]{3,}', text):
                continue

            # Normalize whitespace for matching
            normalized = re.sub(r'\s+', ' ', text).strip()
            if not has_english(normalized):
                continue

            # Try dict first
            translated = apply_dict(normalized, sorted_terms)
            if translated != normalized:
                # Preserve original whitespace structure
                prefix = text[:len(text) - len(text.lstrip())]
                suffix = text[len(text.rstrip()):]
                replacements[text] = prefix + translated + suffix
            elif translation_map and normalized in translation_map:
                prefix = text[:len(text) - len(text.lstrip())]
                suffix = text[len(text.rstrip()):]
                replacements[text] = prefix + translation_map[normalized] + suffix
            elif not translation_map:  # Only collect for Ollama if no map provided
                ollama_set.add(normalized)

    # Apply replacements to soup
    dict_count = 0
    ollama_count = 0
    for el in soup.descendants:
        if isinstance(el, NavigableString) and not isinstance(el, Comment):
            if el.parent and el.parent.name in ("script", "style"):
                continue
            text = str(el)
            if text in replacements:
                el.replace_with(replacements[text])
                # Determine source: dict or ollama
                normalized = re.sub(r'\s+', ' ', text).strip()
                if translation_map and normalized in translation_map:
                    ollama_count += 1
                else:
                    dict_count += 1

    result = str(soup)

    # Phase 3: RESTORE protected patterns
    result = restore(result, pmap)

    if result != original and not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result)

    status = f"{dict_count} dict"
    if ollama_count:
        status += f" + {ollama_count} ollama"
    print(f"  [OK] {filepath} ({status})")

    return ollama_set


def process_js(filepath, sorted_terms, translation_map, dry_run=False):
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    # Phase 1: PROTECT
    protected, pmap = protect(original)

    # Phase 2: Translate string literal content
    result = protected

    for pat, q in [(re.compile(r'"((?:[^"\\]|\\.)*)"'), '"'),
                   (re.compile(r"'((?:[^'\\]|\\.)*)'"), "'")]:
        def make_replacer(pat, q, sorted_terms, translation_map):
            def replacer(m):
                inner = m.group(1)
                clean = inner.replace('\\"','"').replace("\\'","'").replace('\\n','\n')
                if not has_english(clean):
                    return m.group(0)
                translated = apply_dict(clean, sorted_terms)
                if translated != clean:
                    return q + translated + q
                if translation_map and clean in translation_map:
                    return q + translation_map[clean] + q
                return m.group(0)
            return replacer
        result = pat.sub(make_replacer(pat, q, sorted_terms, translation_map), result)

    # Phase 3: RESTORE
    result = restore(result, pmap)

    if result != original and not dry_run:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"  [OK] {filepath}")
    else:
        print(f"  [--] {filepath} (no changes)")

    return set()


def validate():
    """Scan all HTML/JS for known issues: Chinese in IDs, broken JS hooks."""
    issues = []

    for fp in HTML_FILES + JS_FILES:
        if not os.path.exists(fp):
            continue
        with open(fp, "r", encoding="utf-8") as f:
            text = f.read()

        # Check: Chinese in HTML IDs
        for m in re.finditer(r'id="([^"]*[一-鿿][^"]*)"', text):
            issues.append((fp, f"Chinese in id: {m.group(0)}"))

        # Check: Chinese in onclick/onchange handlers
        for m in re.finditer(r'on\w+="([^"]*[一-鿿][^"]*)"', text):
            issues.append((fp, f"Chinese in event handler: {m.group(0)[:80]}"))

        # Check: known proper names translated to Chinese
        checks = {
            'Numenera': '数纳美|努美内拉|新梅拉',
            'Fire Emblem': '火纹|火焰纹章|傲蕾',
            'Dropdowns': '拖放|下拉',
            'AddToTraitList': '添加.*列表',
        }
        for en, bad_pattern in checks.items():
            if en not in text:
                for m in re.finditer(bad_pattern, text):
                    context = text[max(0,m.start()-20):m.end()+20]
                    issues.append((fp, f"Proper name '{en}' may be translated: '{m.group()}' in '{context}'"))

    return issues


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--dict-only", action="store_true")
    parser.add_argument("--validate", "-v", action="store_true")
    parser.add_argument("--file", "-f")
    args = parser.parse_args()

    if args.validate:
        issues = validate()
        if issues:
            print(f"=== {len(issues)} validation issues ===")
            for fp, msg in issues:
                print(f"  {fp}: {msg[:120]}")
        else:
            print("=== Validation clean! ===")
        return

    sorted_terms = load_dict()
    print(f"Dict: {len(sorted_terms)} entries\n")

    # Phase 1: Extract all Ollama-needed strings
    if not args.dict_only:
        print("=== Phase 1: Extracting strings ===")
        all_ollama = set()
        for fp in HTML_FILES:
            if os.path.exists(fp):
                ollama_set = process_html(fp, sorted_terms, {}, dry_run=True)
                all_ollama.update(ollama_set)
        for fp in JS_FILES:
            if os.path.exists(fp):
                process_js(fp, sorted_terms, {}, dry_run=True)

        all_ollama = sorted(all_ollama)
        print(f"\nDict handled many, {len(all_ollama)} unique strings need Ollama")

        if args.dry_run:
            print("\nSample strings:")
            for s in all_ollama[:15]:
                print(f"  {s[:100]}")
            return

    # Phase 2: Ollama translation
    translation_map = {}
    if not args.dict_only:
        if all_ollama:
            print(f"\n=== Phase 2: Ollama translation ===")
            t0 = time.time()
            translation_map = ollama_translate(all_ollama)
            print(f"Done: {len(translation_map)}/{len(all_ollama)} in {time.time()-t0:.0f}s")
    else:
        print("=== Dict-only mode ===")

    # Phase 3: Apply translations
    print(f"\n=== Phase 3: Applying translations ===")
    for fp in HTML_FILES:
        if os.path.exists(fp):
            process_html(fp, sorted_terms, translation_map, args.dry_run)
    for fp in JS_FILES:
        if os.path.exists(fp):
            process_js(fp, sorted_terms, translation_map, args.dry_run)

    # Phase 4: Validate
    print(f"\n=== Phase 4: Validation ===")
    issues = validate()
    if issues:
        print(f"{len(issues)} issues found:")
        for fp, msg in issues[:20]:
            print(f"  {fp}: {msg[:120]}")
    else:
        print("Clean!")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
