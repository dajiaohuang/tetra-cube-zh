#!/usr/bin/env python3
"""
fix_terms.py - Spot-check driven correction script.
Reads corrections from fix_list.txt (one English->Chinese pair per line),
scans all translated HTML/JS files, and applies corrections.

Format of fix_list.txt:
  English text -> Correct Chinese
  Statblock Generator -> 属性块生成器
  Numenera -> Numenera

Usage:
  python fix_terms.py --dry-run    # Preview fixes
  python fix_terms.py              # Apply fixes to all HTML/JS files
  python fix_terms.py --file FILE  # Fix a single file
"""

import argparse, os, re, sys, json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

FIX_LIST = "fix_list.txt"
TARGET_DIRS = ["dnd", "fea-quote-gen", "nft", "numenera", "."]

HTML_FILES = [
    "index.html",
    "dnd/dnd-char-gen.html", "dnd/dnd-magic-items.html",
    "dnd/dnd-reference.html", "dnd/dnd-statblock.html",
    "dnd/dnd-statblock-print.html",
    "fea-quote-gen/fea-quote-gen.html",
    "nft/generator.html", "nft/nft.html",
    "numenera/generator.html",
]

JS_FILES = [
    "dnd/js/statblock-script.js", "dnd/js/card-script.js",
    "dnd/js/char-gen-script.js", "dnd/js/magic-item-script.js",
    "dnd/js/reference-script.js", "dnd/js/statblock-print-script.js",
    "numenera/generator.js",
]

JSON_FILES = [
    "dnd/js/JSON/races.json", "dnd/js/JSON/classes.json",
    "dnd/js/JSON/backgrounds.json", "dnd/js/JSON/books.json",
    "dnd/js/JSON/other.json", "dnd/js/JSON/ua.json",
    "dnd/js/JSON/npcs.json", "dnd/js/JSON/life.json",
    "dnd/js/JSON/magic-items.json", "dnd/js/JSON/magic-item-homebrews.json",
    "dnd/js/JSON/magic-item-specials.json", "dnd/js/JSON/statblockdata.json",
    "dnd/js/JSON/names.json",
    "numenera/JSON/book-data.json", "numenera/JSON/tetras-data.json",
]


def load_fixes():
    """Load corrections from fix_list.txt."""
    if not os.path.exists(FIX_LIST):
        print(f"[WARN] {FIX_LIST} not found, creating empty template")
        with open(FIX_LIST, "w", encoding="utf-8") as f:
            f.write("# Fix list - one per line: Wrong text -> Correct text\n")
            f.write("# Lines starting with # are ignored\n")
        return []

    fixes = []
    with open(FIX_LIST, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "->" in line:
                parts = line.split("->", 1)
                wrong = parts[0].strip()
                correct = parts[1].strip()
                if wrong and correct:
                    fixes.append((wrong, correct))
    return fixes


def apply_fixes_to_file(filepath, fixes, dry_run=False):
    """Apply all fixes to a single file."""
    with open(filepath, "r", encoding="utf-8") as f:
        original = f.read()

    result = original
    changes = 0
    for wrong, correct in fixes:
        # Case-insensitive replacement
        pat = re.compile(re.escape(wrong), re.IGNORECASE)
        new_result, n = pat.subn(correct, result)
        if n > 0:
            changes += n
            result = new_result

    if changes > 0:
        print(f"  {filepath}: {changes} fixes")
        if not dry_run:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(result)
    return changes


def main():
    parser = argparse.ArgumentParser(description="Spot-check fix tool")
    parser.add_argument("--dry-run", "-n", action="store_true")
    parser.add_argument("--file", "-f", help="Fix a single file")
    parser.add_argument("--list", "-l", action="store_true", help="Show current fix list")
    args = parser.parse_args()

    fixes = load_fixes()
    if not fixes:
        print("No fixes loaded. Add entries to fix_list.txt")
        return

    if args.list:
        print(f"=== {len(fixes)} fixes in {FIX_LIST} ===")
        for w, c in fixes:
            print(f"  {w} -> {c}")
        return

    print(f"Loaded {len(fixes)} fixes")
    total = 0

    if args.file:
        fp = args.file
        if os.path.exists(fp):
            total += apply_fixes_to_file(fp, fixes, args.dry_run)
    else:
        for fp in HTML_FILES + JS_FILES + JSON_FILES:
            if os.path.exists(fp):
                total += apply_fixes_to_file(fp, fixes, args.dry_run)

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Total: {total} fixes across all files")

    if args.dry_run:
        print("[Dry run — no files modified]")


if __name__ == "__main__":
    main()
