#!/usr/bin/env python3
"""
Filter dataset for Catalan slang expressions.
Distinguishes between:
- Catalan-specific slang (Barcelona/Catalonia regional)
- Generic Spanish slang (used all over Spain)
"""

import pandas as pd
import re
import json
from pathlib import Path

# Catalan-specific slang patterns (what we WANT to find)
CATALAN_SLANG = {
    # Everyday Catalan slang
    "address_terms": [
        r"\btio\b", r"\btia\b",  # dude/girl (in Catalan context)
        r"\bnen\b", r"\bnena\b",  # kid/girl (very Catalan)
        r"\bhome\b",  # man/dude (Catalan filler)
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
        r"\bostras?\b",  # oh wow (Catalan expression)
        r"\bche\b",  # hey (Barcelona/Valencia)
    ],
    "emotions_reactions": [
        r"\bflipar?\b", r"\bflipat\b", r"\bflipada\b", r"\bhe flipat\b",  # freak out / amazed
        r"\bquina passada\b",  # that's amazing
        r"\bquin pal\b", r"\bem fa pal\b",  # what a drag / can't be bothered
        r"\bquina mandra\b",  # I'm too lazy
        r"\bmolt heavy\b",  # intense / too much
        r"\btop\b",  # top-tier (in context)
        r"\bestar fatal\b",  # to feel terrible
        r"\bestic mort\b", r"\bestic morta\b",  # I'm dead (tired)
    ],
    "catalan_verbs_phrases": [
        r"\bpetar-ho\b", r"\bho peta\b", r"\bpetarlo\b",  # to kill it (Catalan form)
        r"\bsortir de festa\b",  # to go out partying
        r"\banar torrat\b", r"\btorrada\b",  # drunk
        r"\banar molt content\b",  # tipsy
        r"\bfer el vermut\b",  # day drinking / social aperitif
        r"\bens la fotem\b",  # should we go party?
        r"\bcagar-la\b",  # to screw up
        r"\bquedem\b",  # let's meet (Catalan form)
    ],
    "money_work": [
        r"\bcal[eé]s\b",  # money (very Catalan)
        r"\bpelar-se\b", r"\bestic pelat\b", r"\bestà pelat\b",  # to be broke
        r"\bcurrar\b", r"\bcurro\b",  # to work / job
        r"\bfer hores\b",  # to grind / work long hours
    ],
    "swears_edgy": [
        r"\bh[oò]stia\b",  # damn / holy shit
        r"\bmerda\b",  # shit
        r"\bcollons\b",  # balls / damn it
    ],
    "catalan_spelling": [
        r"\brotllo\b",  # vibe (Catalan spelling)
        r"\bguai\b",  # cool (Catalan spelling)
        r"\btal qual\b",  # exactly (Catalan form)
    ],
}

# Spanish slang that is NOT Catalan-specific (for exclusion/marking)
GENERIC_SPANISH_SLANG = [
    r"\bvale\b",  # okay (used all over Spain)
    r"\ben plan\b",  # like / kind of
    r"\brollo\b",  # vibe (Spanish spelling)
    r"\bmola\b", r"\bmolar\b",  # cool
    r"\bguay\b",  # cool (Spanish spelling)
    r"\btal cual\b",  # exactly (Spanish form)
    r"\bsalir de fiesta\b",  # to go out (Spanish form)
    r"\bde tranquis\b",  # chill
    r"\bresaca\b",  # hangover
    r"\ben serio\b",  # seriously
    r"\bqu[eé] va\b",  # no way
    r"\bpasta\b",  # money (generic Spanish)
    r"\bquedar\b", r"\bquedamos\b",  # to meet (Spanish form)
]


def compile_patterns(pattern_dict):
    """Compile all patterns into a single regex."""
    all_patterns = []
    for category, patterns in pattern_dict.items():
        all_patterns.extend(patterns)
    return re.compile("|".join(all_patterns), re.IGNORECASE)


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
    """Analyze text for Catalan and generic Spanish slang."""
    catalan_matches = find_slang_matches(text, CATALAN_SLANG)
    generic_pattern = re.compile("|".join(GENERIC_SPANISH_SLANG), re.IGNORECASE)
    generic_matches = generic_pattern.findall(text)

    return {
        "catalan_slang": catalan_matches,
        "generic_spanish_slang": generic_matches,
        "has_catalan_slang": bool(catalan_matches),
        "catalan_slang_count": sum(len(v) for v in catalan_matches.values()),
        "generic_slang_count": len(generic_matches)
    }


def filter_dataset(input_path, output_dir):
    """Filter dataset for Catalan slang content."""
    print(f"Reading dataset from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"Total entries: {len(df)}")

    # Analyze each entry
    results = []
    for idx, row in df.iterrows():
        text = str(row.get('text', ''))
        context_before = str(row.get('context_before', ''))
        context_after = str(row.get('context_after', ''))

        # Combine text with context for fuller analysis
        full_text = f"{context_before} {text} {context_after}"

        analysis = analyze_text(full_text)
        analysis['text_only_analysis'] = analyze_text(text)
        results.append(analysis)

    # Add analysis results to dataframe
    df['has_catalan_slang'] = [r['has_catalan_slang'] for r in results]
    df['catalan_slang_count'] = [r['catalan_slang_count'] for r in results]
    df['catalan_slang_found'] = [json.dumps(r['catalan_slang']) for r in results]
    df['generic_spanish_slang_count'] = [r['generic_slang_count'] for r in results]

    # Filter for entries with Catalan slang
    catalan_slang_df = df[df['has_catalan_slang']].copy()

    # Sort by slang count (most slang first)
    catalan_slang_df = catalan_slang_df.sort_values('catalan_slang_count', ascending=False)

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save filtered data
    slang_output = output_path / "catalan_slang_filtered.csv"
    catalan_slang_df.to_csv(slang_output, index=False)
    print(f"\nSaved {len(catalan_slang_df)} entries with Catalan slang to {slang_output}")

    # Generate summary report
    summary = {
        "total_entries": len(df),
        "entries_with_catalan_slang": len(catalan_slang_df),
        "percentage_with_slang": round(len(catalan_slang_df) / len(df) * 100, 2),
        "slang_category_counts": {},
        "top_slang_terms": {}
    }

    # Count slang by category
    all_slang = {}
    for r in results:
        for category, terms in r['catalan_slang'].items():
            if category not in all_slang:
                all_slang[category] = []
            all_slang[category].extend([t.lower() for t in terms])

    for category, terms in all_slang.items():
        term_counts = {}
        for term in terms:
            term_counts[term] = term_counts.get(term, 0) + 1
        summary["slang_category_counts"][category] = len(terms)
        # Top 5 terms per category
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        summary["top_slang_terms"][category] = sorted_terms

    # Save summary
    summary_output = output_path / "slang_filter_summary.json"
    with open(summary_output, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Saved summary to {summary_output}")

    # Print summary
    print("\n" + "="*60)
    print("CATALAN SLANG FILTER SUMMARY")
    print("="*60)
    print(f"Total entries analyzed: {summary['total_entries']}")
    print(f"Entries with Catalan slang: {summary['entries_with_catalan_slang']} ({summary['percentage_with_slang']}%)")
    print("\nSlang by category:")
    for category, count in summary["slang_category_counts"].items():
        print(f"  {category}: {count} occurrences")
        if category in summary["top_slang_terms"]:
            top = summary["top_slang_terms"][category][:3]
            print(f"    Top terms: {', '.join([f'{t[0]} ({t[1]})' for t in top])}")

    return catalan_slang_df, summary


def show_examples(df, n=10):
    """Show example entries with Catalan slang."""
    print(f"\n{'='*60}")
    print(f"TOP {n} EXAMPLES WITH CATALAN SLANG")
    print("="*60)

    for idx, row in df.head(n).iterrows():
        print(f"\n--- Entry {idx} (slang count: {row['catalan_slang_count']}) ---")
        print(f"Text: {row['text']}")
        print(f"Scenario: {row['scenario']}")
        print(f"Catalan slang found: {row['catalan_slang_found']}")
        print(f"Source: {row['source_film']}")


if __name__ == "__main__":
    # Paths
    input_csv = Path(__file__).parent / "data/processed/catalan_spanish_full.csv"
    output_dir = Path(__file__).parent / "data/processed/slang_filtered"

    # Run filter
    filtered_df, summary = filter_dataset(input_csv, output_dir)

    # Show examples
    show_examples(filtered_df)
