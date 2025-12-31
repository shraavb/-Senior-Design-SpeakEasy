#!/usr/bin/env python3
"""
Filter dataset for BOTH Catalan-specific AND standard Spanish slang.
Creates filtered datasets for language learning purposes.
"""

import pandas as pd
import re
import json
from pathlib import Path
from collections import Counter

# CATALAN-SPECIFIC SLANG
CATALAN_SLANG = {
    "address_terms": [
        r"\bnen\b", r"\bnena\b",  # kid/girl (very Catalan)
        r"\bhome\b",  # man/dude (Catalan filler)
        r"\bnano\b", r"\bnana\b",  # dude/girl
        r"\bmacu\b", r"\bmaco\b",  # cute/handsome
    ],
    "fillers_reactions": [
        r"\bapa\b",  # alright then
        r"\bvinga\b",  # come on / let's go
        r"\bdoncs\b",  # well / so
        r"\bja est[àa]\b",  # that's it
        r"\bni de conya\b",  # no way
        r"\bqu[eè] fort\b",  # that's crazy
        r"\bde deb[oò]\b",  # really?
        r"\b[eé]s veritat\b",  # true / fair point
        r"\bpassa res\b",  # is there a problem?
        r"\bostras?\b",  # oh wow
        r"\bescolta\b",  # listen (Catalan)
        r"\bclar\b",  # of course
    ],
    "emotions_reactions": [
        r"\bflipar?\b", r"\bflipat\b", r"\bflipada\b",
        r"\bquina passada\b",  # that's amazing
        r"\bquin pal\b", r"\bem fa pal\b",  # what a drag
        r"\bquina mandra\b",  # I'm too lazy
        r"\bmolt heavy\b",  # intense
        r"\bestic mort\b", r"\bestic morta\b",  # I'm dead
        r"\bguai\b",  # cool (Catalan spelling)
        r"\bbrutal\b",  # brutal/awesome
    ],
    "catalan_verbs_phrases": [
        r"\bpetar-ho\b", r"\bho peta\b", r"\bpetarlo\b",
        r"\bsortir de festa\b",
        r"\bfer el vermut\b",
        r"\bquedem\b",  # let's meet (Catalan form)
        r"\bfotre\b",  # to do/put (very Catalan)
    ],
    "money_work": [
        r"\bcal[eé]s\b",  # money (very Catalan)
        r"\bpelar-se\b", r"\bestic pelat\b", r"\bpelat\b", r"\bpelada\b",
    ],
    "swears_edgy": [
        r"\bh[oò]stia\b",  # damn / holy shit
        r"\bmerda\b",  # shit (Catalan)
        r"\bcollons\b",  # balls / damn it
        r"\bcony\b",  # damn (Catalan)
        r"\bfill de puta\b",  # son of a bitch (Catalan)
    ],
    "catalan_expressions": [
        r"\bsi us plau\b",  # please
        r"\bgr[àa]cies\b",  # thanks
        r"\bad[eé]u\b",  # goodbye
        r"\bbon dia\b",  # good morning
        r"\bbona nit\b",  # good night
        r"\bmolt b[eé]\b",  # very good
    ],
}

# STANDARD SPANISH SLANG (used all over Spain)
SPANISH_SLANG = {
    "common_expressions": [
        r"\bvale\b",  # okay
        r"\ben plan\b",  # like / kind of
        r"\brollo\b",  # vibe / thing
        r"\btal cual\b",  # exactly
        r"\bde tranquis\b",  # chill
        r"\ben serio\b",  # seriously
        r"\bqu[eé] va\b",  # no way
    ],
    "address_terms": [
        r"\bt[ií]o\b", r"\bt[ií]a\b",  # dude/girl
        r"\bchaval\b", r"\bchavala\b",  # kid
        r"\bcolega\b",  # buddy
        r"\bmacho\b",  # dude
        r"\bpavo\b", r"\bpava\b",  # guy/girl
    ],
    "cool_reactions": [
        r"\bmola\b", r"\bmolar\b",  # cool
        r"\bguay\b",  # cool
        r"\bflipa\w*\b",  # freak out
        r"\balucin\w*\b",  # amazed
        r"\bpasada\b",  # amazing
        r"\bgenial\b",  # great
        r"\bbrutal\b",  # brutal/awesome
        r"\bincre[ií]ble\b",  # incredible
        r"\btope\b",  # very/super
        r"\bmogoll[oó]n\b",  # a lot
        r"\bmazo\b",  # a lot
        r"\bcantidad\b",  # a lot
    ],
    "party_social": [
        r"\bresaca\b",  # hangover
        r"\bsalir de fiesta\b",  # go out partying
        r"\bbotell[oó]n\b",  # outdoor drinking
        r"\bmovida\b",  # thing/scene
        r"\bmarcha\b",  # party vibes
        r"\bfiesta\b",  # party
        r"\bcachondeo\b",  # joking around
    ],
    "money_work": [
        r"\bpasta\b",  # money
        r"\bcurrar\b", r"\bcurro\b",  # work/job
        r"\bquedar\b", r"\bquedamos\b",  # meet up
    ],
    "swears_expressions": [
        r"\bmierda\b",  # shit
        r"\bjoder\b",  # fuck
        r"\bhostia\b",  # damn
        r"\bco[nñ]o\b",  # damn
        r"\bputa\b",  # whore/damn
        r"\bcabr[oó]n\b",  # bastard
        r"\bgilipollas\b",  # idiot
        r"\bcapullo\b",  # jerk
        r"\bimb[eé]cil\b",  # imbecile
    ],
    "other_common": [
        r"\bl[ií]o\b",  # mess
        r"\bchorrada\b",  # nonsense
        r"\bmorro\b",  # nerve/cheek
        r"\bculo\b",  # ass
        r"\bpillar\b",  # to catch/get
        r"\bpringa[od]o?\b",  # loser
    ],
}


def find_slang_matches(text, pattern_dict):
    """Find all matching slang terms in text, organized by category."""
    matches = {}
    for category, patterns in pattern_dict.items():
        category_matches = []
        for pattern in patterns:
            found = re.findall(pattern, text, re.IGNORECASE)
            category_matches.extend(found)
        if category_matches:
            matches[category] = category_matches
    return matches


def analyze_text(text):
    """Analyze text for both Catalan and Spanish slang."""
    catalan_matches = find_slang_matches(text, CATALAN_SLANG)
    spanish_matches = find_slang_matches(text, SPANISH_SLANG)

    return {
        "catalan_slang": catalan_matches,
        "spanish_slang": spanish_matches,
        "has_catalan_slang": bool(catalan_matches),
        "has_spanish_slang": bool(spanish_matches),
        "has_any_slang": bool(catalan_matches) or bool(spanish_matches),
        "catalan_slang_count": sum(len(v) for v in catalan_matches.values()),
        "spanish_slang_count": sum(len(v) for v in spanish_matches.values()),
    }


def filter_dataset(input_path, output_dir):
    """Filter dataset for slang content."""
    print(f"Reading dataset from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"Total entries: {len(df)}")

    # Analyze each entry
    results = []
    catalan_terms = Counter()
    spanish_terms = Counter()

    for idx, row in df.iterrows():
        text = str(row.get('text', ''))
        context_before = str(row.get('context_before', ''))
        context_after = str(row.get('context_after', ''))
        full_text = f"{context_before} {text} {context_after}"

        analysis = analyze_text(full_text)

        # Count terms
        for cat_matches in analysis['catalan_slang'].values():
            for term in cat_matches:
                catalan_terms[term.lower()] += 1
        for spa_matches in analysis['spanish_slang'].values():
            for term in spa_matches:
                spanish_terms[term.lower()] += 1

        results.append(analysis)

    # Add analysis results to dataframe
    df['has_catalan_slang'] = [r['has_catalan_slang'] for r in results]
    df['has_spanish_slang'] = [r['has_spanish_slang'] for r in results]
    df['has_any_slang'] = [r['has_any_slang'] for r in results]
    df['catalan_slang_count'] = [r['catalan_slang_count'] for r in results]
    df['spanish_slang_count'] = [r['spanish_slang_count'] for r in results]
    df['total_slang_count'] = df['catalan_slang_count'] + df['spanish_slang_count']
    df['catalan_slang_found'] = [json.dumps(r['catalan_slang']) for r in results]
    df['spanish_slang_found'] = [json.dumps(r['spanish_slang']) for r in results]

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Filter datasets
    catalan_df = df[df['has_catalan_slang']].sort_values('catalan_slang_count', ascending=False)
    spanish_df = df[df['has_spanish_slang']].sort_values('spanish_slang_count', ascending=False)
    all_slang_df = df[df['has_any_slang']].sort_values('total_slang_count', ascending=False)

    # Save filtered data
    catalan_df.to_csv(output_path / "catalan_slang_only.csv", index=False)
    spanish_df.to_csv(output_path / "spanish_slang_only.csv", index=False)
    all_slang_df.to_csv(output_path / "all_slang_combined.csv", index=False)

    print(f"\nSaved {len(catalan_df)} entries with Catalan slang")
    print(f"Saved {len(spanish_df)} entries with Spanish slang")
    print(f"Saved {len(all_slang_df)} entries with any slang")

    # Summary
    summary = {
        "total_entries": len(df),
        "catalan_slang": {
            "entries": len(catalan_df),
            "percentage": round(len(catalan_df) / len(df) * 100, 2),
            "top_terms": catalan_terms.most_common(20)
        },
        "spanish_slang": {
            "entries": len(spanish_df),
            "percentage": round(len(spanish_df) / len(df) * 100, 2),
            "top_terms": spanish_terms.most_common(30)
        },
        "combined": {
            "entries": len(all_slang_df),
            "percentage": round(len(all_slang_df) / len(df) * 100, 2),
        }
    }

    with open(output_path / "slang_summary.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*70)
    print("SLANG FILTER SUMMARY")
    print("="*70)
    print(f"Total entries: {len(df)}")
    print()
    print("🇦🇩 CATALAN-SPECIFIC SLANG")
    print(f"   Entries: {len(catalan_df)} ({summary['catalan_slang']['percentage']}%)")
    print(f"   Top terms: {', '.join([f'{t[0]}({t[1]})' for t in catalan_terms.most_common(10)])}")
    print()
    print("🇪🇸 STANDARD SPANISH SLANG")
    print(f"   Entries: {len(spanish_df)} ({summary['spanish_slang']['percentage']}%)")
    print(f"   Top terms: {', '.join([f'{t[0]}({t[1]})' for t in spanish_terms.most_common(10)])}")
    print()
    print("📊 COMBINED (any slang)")
    print(f"   Entries: {len(all_slang_df)} ({summary['combined']['percentage']}%)")

    return all_slang_df, summary


if __name__ == "__main__":
    input_csv = Path(__file__).parent / "data/processed/catalan_spanish_full.csv"
    output_dir = Path(__file__).parent / "data/processed/slang_filtered"

    filtered_df, summary = filter_dataset(input_csv, output_dir)
