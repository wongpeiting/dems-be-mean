"""Aggregate stage2_treatments.csv into the attention-pool dataset.

Each treatment row is (account, video_id, upload_date, subject, side, register…).
A person of interest is a POOL positioned on a platformed(-3)↔attacked(+3) axis by
their mean register, sized by how many posts feature them. Each account that posts
about them feeds a RIBBON whose width = post count and colour = mean register.

Output: src/lib/data/attention.json — people, accounts, months, and monthly flow
bins the frontend accumulates as the reader scrolls through time.
"""
import csv
import json
import re
from collections import defaultdict
from pathlib import Path

SRC = Path("/Users/wongpeiting/Desktop/CU/python-work/all-of-pol-tiktok/party_accounts/data/classification/stage2_treatments.csv")
OUT = Path(__file__).resolve().parents[1] / "src" / "lib" / "data" / "attention.json"

ACCOUNTS = ["democrats", "whitehouse", "republicans"]
TOP_N = 16

# --- canonicalisation: merge the name fragments the LLM produced -------------
ALIASES = {
    "donald j. trump": "Donald Trump",
    "president donald trump": "Donald Trump",
    "president trump": "Donald Trump",
    "trump": "Donald Trump",
    "the trump administration": "Donald Trump",
    "jd vance": "JD Vance",
    "j.d. vance": "JD Vance",
    "vice president jd vance": "JD Vance",
    "kamala harris": "Kamala Harris",
    "vice president kamala harris": "Kamala Harris",
    "joe biden": "Joe Biden",
    "president joe biden": "Joe Biden",
    "president biden": "Joe Biden",
    "barack obama": "Barack Obama",
    "robert f. kennedy, jr.": "Robert F. Kennedy Jr.",
    "robert f. kennedy jr.": "Robert F. Kennedy Jr.",
}

# people-of-interest whitelist (canonical) + the two parties as collective targets
PARTIES = {"Democratic Party", "Republican Party"}
# abstractions / institutions we don't treat as a "person of interest" pool
EXCLUDE = {"America", "The White House", "Congress", "The Supreme Court",
           "U.S. Immigration and Customs Enforcement", "The Media", "The United States"}


def canon(name):
    n = name.strip()
    key = n.lower()
    if key in ALIASES:
        return ALIASES[key]
    # normalise "the X party" / casing → "X Party"
    m = re.match(r"^(the\s+)?(democratic|republican)\s+party$", key)
    if m:
        return f"{m.group(2).capitalize()} Party"
    return n


def is_person_or_party(name):
    if name in EXCLUDE:
        return False
    if name in PARTIES:
        return True
    # drop agencies / institutions caught by name pattern
    if name.startswith("U.S.") or "Immigration" in name or "Department" in name:
        return False
    # a person: at least two capitalised words, not an obvious org/abstraction
    words = name.split()
    if len(words) < 2:
        return False
    orgish = ("Party", "House", "Department", "Administration", "Court",
              "Agency", "Committee", "Media", "Press", "Team", "Force")
    if any(w in orgish for w in words):
        return False
    return True


def month_of(datestr):
    d = str(datestr)[:8]
    return f"{d[:4]}-{d[4:6]}" if len(d) >= 6 else None


def main():
    rows = list(csv.DictReader(open(SRC)))

    # canonical subject per row, filtered to people/parties
    recs = []
    for r in rows:
        subj = canon(r["subject"])
        if not is_person_or_party(subj):
            continue
        try:
            reg = int(r["register"])
        except (ValueError, KeyError):
            continue
        mo = month_of(r["upload_date"])
        if not mo or r["account"] not in ACCOUNTS:
            continue
        recs.append((subj, r["account"], mo, reg))

    # totals per person → pick top N, compute x-position (mean register)
    per_person = defaultdict(lambda: {"n": 0, "sum": 0})
    for subj, acct, mo, reg in recs:
        p = per_person[subj]
        p["n"] += 1
        p["sum"] += reg
    top = sorted(per_person.items(), key=lambda kv: -kv[1]["n"])[:TOP_N]
    keep = {name for name, _ in top}
    people = [
        {"id": name, "name": name, "register": round(v["sum"] / v["n"], 3), "total": v["n"]}
        for name, v in top
    ]

    # monthly flow bins per (account, person)
    bins = defaultdict(lambda: {"count": 0, "sum": 0})
    months = set()
    for subj, acct, mo, reg in recs:
        if subj not in keep:
            continue
        months.add(mo)
        b = bins[(acct, subj, mo)]
        b["count"] += 1
        b["sum"] += reg
    flows = [
        {"account": a, "person": s, "month": m, "count": v["count"], "sumReg": v["sum"]}
        for (a, s, m), v in bins.items()
    ]

    # first month each account appears (for the scroll reveal timing)
    first = {}
    for a, s, m in ((a, s, m) for a in ACCOUNTS for (aa, s, m) in [] if aa == a):
        pass
    for (a, s, m) in bins:
        if a not in first or m < first[a]:
            first[a] = m
    accounts = [{"id": a, "firstMonth": first.get(a)} for a in ACCOUNTS]

    months = sorted(months)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"people": people, "accounts": accounts, "months": months, "flows": flows},
              open(OUT, "w"), indent=1)

    # raw points for the scatter: EVERY treatment (no aggregation), compact.
    # a=account, d=YYYYMMDD date, r=register, s=canonical subject
    pts = []
    for r in rows:
        try:
            reg = int(r["register"])
        except (ValueError, KeyError):
            continue
        d = str(r["upload_date"])[:8]
        if len(d) < 8 or r["account"] not in ACCOUNTS:
            continue
        pts.append({"a": r["account"], "d": d, "r": reg, "s": canon(r["subject"])})
    json.dump(pts, open(OUT.parent / "attention_points.json", "w"))
    print(f"{len(pts)} raw points → attention_points.json")

    # report
    print(f"{len(recs)} person/party treatments · {len(people)} pools · {len(months)} months "
          f"({months[0]}→{months[-1]}) · {len(flows)} flow bins")
    print("accounts first appear:", {a["id"]: a["firstMonth"] for a in accounts})
    print("\nPOOLS (left=platformed … right=attacked):")
    for p in sorted(people, key=lambda p: p["register"]):
        bar = int((p["register"] + 3) / 6 * 30)
        print(f"  {p['name'][:22]:22} reg={p['register']:+.2f} n={p['total']:4} " + " " * bar + "●")


if __name__ == "__main__":
    main()
