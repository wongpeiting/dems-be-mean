from pipeline.config import side_of, slugify, canonical_name, PARTY

def test_side_of():
    assert side_of("democrats") == "dem"
    assert side_of("dccc") == "dem"
    assert side_of("whitehouse") == "rep"
    assert side_of("republicans") == "rep"

def test_slugify():
    assert slugify("Donald Trump") == "donald-trump"
    assert slugify("Alexandria Ocasio-Cortez") == "alexandria-ocasio-cortez"

def test_alias_resolution():
    assert canonical_name("Trump") == "Donald Trump"
    assert canonical_name("President Donald Trump") == "Donald Trump"
    assert canonical_name("JD Vance") == "JD Vance"
    assert canonical_name("J.D. Vance") == "JD Vance"

def test_party_from_roster():
    assert PARTY["Donald Trump"] == "rep"
