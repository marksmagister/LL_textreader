"""Levels are counted from exposure, not self-assessment (decision 0008).

The user's judgement is the only thing that makes a word known; the app's job is
to notice how often you have met it and, eventually, to ask.
"""

TEXT = "Il marchait le long du quai. Nous marchons."


def make(client):
    return client.post("/api/lessons", json={"text": TEXT, "lang": "fr"}).json()["id"]


def status_of(client, lemma="marcher"):
    entry = next(
        (e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == lemma),
        None,
    )
    return entry and entry["status"]


def states(client, lesson):
    return {t["surface"]: t["state"] for t in client.get(f"/api/lessons/{lesson}").json()["tokens"]}


def learn(client, lemma="marcher"):
    client.put("/api/terms", json={"lang": "fr", "lemma": lemma, "pos": "VERB", "status": 1})


def test_a_learning_word_rises_each_time_you_finish_a_page_with_it(client):
    lesson = make(client)
    learn(client)
    assert status_of(client) == 1
    for expected in (2, 3, 4):
        client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
        assert status_of(client) == expected


def test_it_stops_at_review_and_never_promotes_itself_to_known(client):
    """Only the user gets to say a word is known."""
    lesson = make(client)
    learn(client)
    for _ in range(8):
        client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert status_of(client) == 4  # not 5, however often you meet it


def test_review_is_its_own_render_state_so_the_reader_can_ask(client):
    lesson = make(client)
    learn(client)
    assert states(client, lesson)["marchait"] == "learning"
    for _ in range(3):
        client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert states(client, lesson)["marchait"] == "review"


def test_only_words_on_the_page_rise(client):
    lesson = make(client)
    learn(client, "marcher")
    learn(client, "absent")  # never appears in the text
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert status_of(client, "marcher") == 2
    assert status_of(client, "absent") == 1


def test_new_and_known_words_are_not_touched_by_the_bump(client):
    lesson = make(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    client.put("/api/terms", json={"lang": "fr", "lemma": "long", "pos": "VERB", "status": -1})
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert status_of(client, "quai") == 5
    assert status_of(client, "long") == -1


def test_vocab_reports_how_often_you_have_met_a_word(client):
    lesson = make(client)
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchait"},
    )
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    entry = next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == "marcher"
    )
    assert entry["met"] >= 2  # marchait and marchons both appeared
    assert sorted(entry["forms"]) == ["marchait", "marchons"]


def test_a_word_repeated_on_one_page_counts_once(client):
    """Three occurrences in one paragraph is one encounter, not three: the value
    of a repeat is in the delay before it, and there is none within a page."""
    text = "Le quai. Le quai encore. Toujours le quai."
    lesson = client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 1})

    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert status_of(client, "quai") == 2  # not 4

    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert status_of(client, "quai") == 3


def test_seen_counts_every_occurrence_even_though_the_level_does_not(client):
    """`seen` is how often the word appeared; the level is how many pages. They
    are different numbers on purpose."""
    text = "Le quai. Le quai encore. Toujours le quai."
    lesson = client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5, "surface": "quai"},
    )
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    entry = next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == "quai"
    )
    assert entry["met"] > 1
