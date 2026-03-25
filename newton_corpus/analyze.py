"""
Distant reading of Isaac Newton's corpus:
  - Opticks (33504)
  - Observations upon the Prophecies of Daniel... (16878)
  - The Chronology of Ancient Kingdoms Amended (15784)
  - Philosophiae Naturalis Principia Mathematica (28233) [Latin]

Steps:
  1. Strip Gutenberg headers/footers
  2. Tokenize and lowercase
  3. Remove stopwords (English + Latin)
  4. Compute word frequencies per text
  5. Identify shared key terms (top N words appearing in multiple texts)
  6. Extract KWIC concordances for shared terms
"""

import re
import json
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Stopwords
# ---------------------------------------------------------------------------
ENGLISH_STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because
been before being below between both but by can't cannot could couldn't did didn't
do does doesn't doing don't down during each few for from further get got had hadn't
has hasn't have haven't having he he'd he'll he's her here here's hers herself him
himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself
let's me more most mustn't my myself no nor not of off on once only or other ought
our ours ourselves out over own same shan't she she'd she'll she's should shouldn't
so some such than that that's the their theirs them themselves then there there's
these they they'd they'll they're they've this those through to too under until up
very was wasn't we we'd we'll we're we've were weren't what what's when when's
where where's which while who who's whom why why's will with won't would wouldn't
you you'd you'll you're you've your yours yourself yourselves
th hath doth unto thence whence whereof thereof hereunto hereto wherein whereby
whereat whereas whereunto aforementioned aforesaid abovesaid
""".split())

LATIN_STOPWORDS = set("""
a ab ac ad adhuc aliquam aliquando aliquid aliquis aliquod aliter aliunde alius
alteri alteorum alteri alterum an ante apud at atque aut autem breviter circa
consequenter contra cum de dein deinde dum e eadem eam earum eius enim eorum et
etiam eum ex fere fieri fit forte iam ibi idem ideo igitur in inde ipsum is iste
ita itaque jam maxime me mecum mihi modo nam nec neque nihil nisi nobis non nos
nunc ob omnino omnis per post praeterea proinde propter quae quam quamque quamvis
quando quasi que quem qui quid quidem quis quisquam quisque quod quoque sed si
sic sicut sine sit sub tamen tam tandem te tum tunc ubi una ut vero vel velut
vero
""".split())

ALL_STOPWORDS = ENGLISH_STOPWORDS | LATIN_STOPWORDS

# Additional very-common function words to suppress
EXTRA_STOPS = set("""
one two three four five six seven eight nine ten
also upon which with from that this they them their
same such more than when then where thus hence
said same many much great shall will would could should
may might must now here there yet still again
every part parts same kind whole first second third
upon within without between above below beyond before after
whether whether either neither another other others
every doth hath thee thy thou thine
""".split())
ALL_STOPWORDS |= EXTRA_STOPS

# ---------------------------------------------------------------------------
# 2. Gutenberg header/footer stripping
# ---------------------------------------------------------------------------
HEADER_RE = re.compile(
    r"^\*\*\* START OF (THE|THIS) PROJECT GUTENBERG",
    re.IGNORECASE | re.MULTILINE,
)
FOOTER_RE = re.compile(
    r"^\*\*\* END OF (THE|THIS) PROJECT GUTENBERG",
    re.IGNORECASE | re.MULTILINE,
)

def strip_gutenberg(text: str) -> str:
    m_start = HEADER_RE.search(text)
    m_end = FOOTER_RE.search(text)
    if m_start:
        text = text[m_start.end():]
    if m_end:
        text = text[: m_end.start()]
    return text.strip()


# ---------------------------------------------------------------------------
# 3. Tokenizer
# ---------------------------------------------------------------------------
TOKEN_RE = re.compile(r"[a-zA-Z]+(?:[-'][a-zA-Z]+)*")

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in TOKEN_RE.findall(text)]


def meaningful_tokens(tokens: list[str], min_len: int = 3) -> list[str]:
    return [t for t in tokens if t not in ALL_STOPWORDS and len(t) >= min_len]


# ---------------------------------------------------------------------------
# 4. Load and preprocess each text
# ---------------------------------------------------------------------------
TEXTS = {
    "opticks":    ("opticks.txt",    "Opticks"),
    "prophecies": ("prophecies.txt", "Observations upon the Prophecies"),
    "chronology": ("chronology.txt", "Chronology of Ancient Kingdoms"),
    "principia":  ("principia.txt",  "Principia Mathematica (Latin)"),
}

corpora = {}
raw_tokens_all = {}

for key, (fname, title) in TEXTS.items():
    raw = Path(fname).read_text(encoding="utf-8", errors="replace")
    body = strip_gutenberg(raw)
    tokens = tokenize(body)
    meaningful = meaningful_tokens(tokens)
    corpora[key] = {
        "title": title,
        "body": body,
        "tokens": tokens,
        "meaningful": meaningful,
        "freq": Counter(meaningful),
        "total_tokens": len(tokens),
        "total_meaningful": len(meaningful),
    }
    raw_tokens_all[key] = tokens

print("=== Corpus Statistics ===")
for key, data in corpora.items():
    print(f"  {data['title']}")
    print(f"    Total tokens:      {data['total_tokens']:>7,}")
    print(f"    Meaningful tokens: {data['total_meaningful']:>7,}")
    print(f"    Unique meaningful: {len(data['freq']):>7,}")
    print()


# ---------------------------------------------------------------------------
# 5. Top-40 terms per text
# ---------------------------------------------------------------------------
TOP_N = 40
print("=== Top-40 Terms per Text ===")
top_per_text = {}
for key, data in corpora.items():
    top = data["freq"].most_common(TOP_N)
    top_per_text[key] = top
    print(f"\n  {data['title']}")
    for rank, (word, count) in enumerate(top, 1):
        print(f"    {rank:2}. {word:<22} {count:>5}")


# ---------------------------------------------------------------------------
# 6. Shared key terms
# ---------------------------------------------------------------------------
# A term is "shared" if it appears in at least 2 texts among the top-200 of each.
TOP_POOL = 200
pools = {key: {w for w, _ in data["freq"].most_common(TOP_POOL)}
         for key, data in corpora.items()}

all_words = set.union(*pools.values())
shared = {}
for word in all_words:
    present_in = [key for key, pool in pools.items() if word in pool]
    if len(present_in) >= 2:
        total_freq = sum(corpora[k]["freq"][word] for k in present_in)
        shared[word] = {"texts": present_in, "total_freq": total_freq,
                        "per_text": {k: corpora[k]["freq"][word] for k in present_in}}

# Sort by number of texts (desc), then total frequency (desc)
shared_sorted = sorted(shared.items(),
                       key=lambda x: (-len(x[1]["texts"]), -x[1]["total_freq"]))

print("\n\n=== Shared Key Terms (appearing in ≥2 texts, top-200 pool) ===")
print(f"{'Term':<22} {'Texts':>5}  {'TotalFreq':>9}  Per-text breakdown")
print("-" * 80)
for word, info in shared_sorted[:60]:
    per = "  |  ".join(
        f"{corpora[k]['title'][:18]}: {info['per_text'][k]}"
        for k in info["texts"]
    )
    print(f"  {word:<20} {len(info['texts']):>5}  {info['total_freq']:>9}  {per}")


# ---------------------------------------------------------------------------
# 7. KWIC concordance
# ---------------------------------------------------------------------------
KWIC_WINDOW = 8   # words on each side
KWIC_MAX    = 10  # max hits per (word, text) pair

def kwic(tokens: list[str], term: str, window: int = KWIC_WINDOW,
         max_hits: int = KWIC_MAX) -> list[str]:
    lines = []
    for i, tok in enumerate(tokens):
        if tok == term:
            left  = tokens[max(0, i - window): i]
            right = tokens[i + 1: i + 1 + window]
            left_str  = " ".join(left).rjust(window * 7)
            right_str = " ".join(right)
            lines.append(f"  ...{left_str}  [{term.upper()}]  {right_str}...")
            if len(lines) >= max_hits:
                break
    return lines


# Build KWIC for shared terms that appear in ≥3 texts, plus top shared pairs
kwic_targets = [w for w, info in shared_sorted
                if len(info["texts"]) >= 2][:30]

print("\n\n=== KWIC Concordances ===")
kwic_results = {}
for word in kwic_targets:
    kwic_results[word] = {}
    print(f"\n--- '{word}' ---")
    for key in corpora:
        if corpora[key]["freq"][word] == 0:
            continue
        hits = kwic(raw_tokens_all[key], word)
        if hits:
            kwic_results[word][key] = hits
            print(f"  [{corpora[key]['title']}]")
            for h in hits:
                print(h)


# ---------------------------------------------------------------------------
# 8. Serialize results to JSON for downstream use
# ---------------------------------------------------------------------------
results = {
    "corpus_stats": {
        k: {
            "title": v["title"],
            "total_tokens": v["total_tokens"],
            "total_meaningful": v["total_meaningful"],
            "unique_meaningful": len(v["freq"]),
            "top_40": top_per_text[k],
        }
        for k, v in corpora.items()
    },
    "shared_terms": [
        {"term": w, "n_texts": len(i["texts"]), "total_freq": i["total_freq"],
         "texts": i["texts"], "per_text": i["per_text"]}
        for w, i in shared_sorted[:60]
    ],
    "kwic": {
        word: {k: hits for k, hits in text_hits.items()}
        for word, text_hits in kwic_results.items()
    },
}

with open("analysis_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print("\n\n✓ Results saved to analysis_results.json")
