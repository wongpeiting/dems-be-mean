import re
from pathlib import Path

UPSTREAM = Path("/Users/wongpeiting/Desktop/CU/python-work/all-of-pol-tiktok/party_accounts")
DATA = UPSTREAM / "data"
DESC = DATA / "descriptions" / "gemini_v2"
CLS = DATA / "classification"
VIDEOS = UPSTREAM / "videos"
CLUSTER_CSV = DATA / "embeddings_gemini" / "cluster_data.csv"

PROJECT = Path(__file__).resolve().parents[1]
OUT_DATA = PROJECT / "src" / "lib" / "data"
OUT_STATIC = PROJECT / "static"
OUT_WORK = PROJECT / "pipeline" / "out"

DEM_ACCOUNTS = {"democrats", "dccc", "senatedems", "senatedemshq"}
REP_ACCOUNTS = {"whitehouse", "republicans"}
ALL_ACCOUNTS = sorted(DEM_ACCOUNTS | REP_ACCOUNTS)
ELECTION = "2024-11-06"

def side_of(account: str) -> str:
    if account in DEM_ACCOUNTS: return "dem"
    if account in REP_ACCOUNTS: return "rep"
    raise ValueError(account)

def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")

# Free-text cast names -> canonical. Extend as pipeline logs unknowns.
ALIASES = {
    "trump": "Donald Trump", "donald j. trump": "Donald Trump",
    "president trump": "Donald Trump", "president donald trump": "Donald Trump",
    "j.d. vance": "JD Vance", "jd vance": "JD Vance", "vice president jd vance": "JD Vance",
    "kamala harris": "Kamala Harris", "vice president kamala harris": "Kamala Harris",
    "elon musk": "Elon Musk", "hakeem jeffries": "Hakeem Jeffries",
    # roster uses "Charles Schumer" — map common alias
    "chuck schumer": "Charles Schumer",
    "barack obama": "Barack Obama",
    "joe biden": "Joe Biden", "president joe biden": "Joe Biden",
    "gavin newsom": "Gavin Newsom", "karoline leavitt": "Karoline Leavitt",
    "pete hegseth": "Pete Hegseth", "zohran mamdani": "Zohran Mamdani",
    "alexandria ocasio-cortez": "Alexandria Ocasio-Cortez", "aoc": "Alexandria Ocasio-Cortez",
    # roster uses period-comma form
    "robert f. kennedy jr.": "Robert F. Kennedy, Jr.",
    "robert f kennedy jr": "Robert F. Kennedy, Jr.",
    # roster uses "Douglas Emhoff"
    "doug emhoff": "Douglas Emhoff",
    # additional people identified from unknown_party.txt
    "mikie sherrill": "Mikie Sherrill",
    "ketanji brown jackson": "Ketanji Brown Jackson",
    "maxwell frost": "Maxwell Frost",
    "ken martin": "Ken Martin",
    "alex padilla": "Alex Padilla",
    "jerome powell": "Jerome Powell",
}
def canonical_name(name: str) -> str:
    return ALIASES.get(name.strip().lower(), name.strip())

# Canonical emotion buckets -> hex (smoke palette). Stage-1 emotions map in.
EMOTION_MAP = {
    "pride": ("Pride", "#e4572e"), "patriotism": ("Pride", "#e4572e"),
    "anger": ("Anger", "#c1121f"), "outrage": ("Anger", "#c1121f"), "rage": ("Anger", "#c1121f"),
    "mockery": ("Mockery", "#7b2cbf"), "ridicule": ("Mockery", "#7b2cbf"),
    "contempt": ("Mockery", "#7b2cbf"), "humor": ("Humor", "#f4a261"),
    "amusement": ("Humor", "#f4a261"), "fear": ("Alarm", "#264653"),
    "alarm": ("Alarm", "#264653"), "urgency": ("Alarm", "#264653"),
    "inspiration": ("Hype", "#2a9d8f"), "strength": ("Hype", "#2a9d8f"),
    "triumph": ("Hype", "#2a9d8f"), "excitement": ("Hype", "#2a9d8f"),
    "nostalgia": ("Warmth", "#e9c46a"), "hope": ("Warmth", "#e9c46a"),
}
def emotion_bucket(label: str) -> tuple[str, str]:
    return EMOTION_MAP.get(label.strip().lower(), ("Other", "#8d99ae"))

# Amendment: WATCHLIST path and roster-driven PARTY dict
import csv as _csv
WATCHLIST = Path("/Users/wongpeiting/Desktop/CU/python-work/pol-face/watchlist")

def _load_party():
    """Subject party from pol-face YouGov roster.csv (name,slug,party R/D) + extras."""
    party = {}
    with open(WATCHLIST / "roster.csv", newline="") as f:
        for r in _csv.DictReader(f):
            party[r["name"]] = "rep" if r["party"] == "R" else "dem"
    party.update({
        "Elon Musk": "rep",  # roster lists party='X'; override to rep
        "Karoline Leavitt": "rep",
        # Dem officials not in YouGov roster
        "Mikie Sherrill": "dem", "Ketanji Brown Jackson": "dem",
        "Maxwell Frost": "dem", "Ken Martin": "dem",
        "Alex Padilla": "dem",
    })
    return party

try:
    PARTY = _load_party()
except FileNotFoundError:
    PARTY = {}
