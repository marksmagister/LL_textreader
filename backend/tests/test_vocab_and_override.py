"""The lexicon list, and the escape hatch when the lemmatiser is wrong."""


def make(client, text="Il marchait le long du quai. Nous marchons."):
    return client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]


def states(client, lesson_id):
    return {
        t["surface"]: t["state"] for t in client.get(f"/api/lessons/{lesson_id}").json()["tokens"]
    }


def lemmas(client, lesson_id):
    return {
        t["surface"]: t["lemma"] for t in client.get(f"/api/lessons/{lesson_id}").json()["tokens"]
    }


# ---------------------------------------------------------------- vocab


def test_vocab_lists_what_you_know_with_the_forms_you_have_met(client):
    make(client)
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchait"},
    )
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchons"},
    )
    v = client.get("/api/vocab?lang=fr").json()
    entry = next(e for e in v["entries"] if e["lemma"] == "marcher")
    assert entry["forms"] == ["marchait", "marchons"]
    assert entry["status"] == 5


def test_vocab_counts_by_bucket(client):
    client.put("/api/terms", json={"lang": "fr", "lemma": "a", "pos": "X", "status": 5})
    client.put("/api/terms", json={"lang": "fr", "lemma": "b", "pos": "X", "status": 2})
    client.put("/api/terms", json={"lang": "fr", "lemma": "c", "pos": "X", "status": -1})
    v = client.get("/api/vocab?lang=fr").json()
    assert v["total"] == 3
    assert v["by_status"] == {"known": 1, "learning": 1, "ignored": 1}


def test_vocab_filters_but_counts_stay_whole(client):
    """Totals must not move while you type in the search box."""
    client.put("/api/terms", json={"lang": "fr", "lemma": "porte", "pos": "NOUN", "status": 5})
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "NOUN", "status": 2})
    v = client.get("/api/vocab?lang=fr&status=known").json()
    assert [e["lemma"] for e in v["entries"]] == ["porte"]
    assert v["total"] == 2 and v["by_status"]["learning"] == 1

    assert [e["lemma"] for e in client.get("/api/vocab?lang=fr&q=qu").json()["entries"]] == ["quai"]


def test_homographs_are_separate_vocab_entries(client):
    client.put("/api/terms", json={"lang": "fr", "lemma": "porte", "pos": "NOUN", "status": 5})
    client.put("/api/terms", json={"lang": "fr", "lemma": "porte", "pos": "VERB", "status": 1})
    v = client.get("/api/vocab?lang=fr").json()
    assert sorted((e["pos"], e["status"]) for e in v["entries"]) == [("NOUN", 5), ("VERB", 1)]


# ---------------------------------------------------------------- override


def test_override_detaches_a_form_from_its_lemma(client):
    """CLAUDE.md rule 5. The stub lemmatises quais -> quai; say that is wrong."""
    lesson = make(client, "Les quais sont longs.")
    assert lemmas(client, lesson)["quais"] == "quai"

    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais", "from_lemma": "quai"})
    assert lemmas(client, lesson)["quais"] == "quais"  # now its own entry


def test_override_can_name_the_right_lemma(client):
    lesson = make(client, "Les quais sont longs.")
    client.put(
        "/api/terms/override",
        json={"lang": "fr", "surface": "quais", "to_lemma": "Quai", "to_pos": "NOUN"},
    )
    assert lemmas(client, lesson)["quais"] == "quai"  # case-folded


def test_status_follows_the_override_not_the_pipeline(client):
    lesson = make(client, "Les quais sont longs.")
    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais"})
    # marking the pipeline's lemma known must NOT colour the overridden word
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    assert states(client, lesson)["quais"] == "new"

    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "quais", "pos": "X", "status": 5, "surface": "quais"},
    )
    assert states(client, lesson)["quais"] == "known"


def test_override_can_be_undone(client):
    lesson = make(client, "Les quais sont longs.")
    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais"})
    assert lemmas(client, lesson)["quais"] == "quais"

    assert client.delete("/api/terms/override?lang=fr&surface=quais").status_code == 204
    assert lemmas(client, lesson)["quais"] == "quai"


def test_override_is_idempotent(client):
    lesson = make(client, "Les quais sont longs.")
    for _ in range(3):
        client.put("/api/terms/override", json={"lang": "fr", "surface": "Quais"})
    assert lemmas(client, lesson)["quais"] == "quais"


def test_the_sentence_you_met_a_word_in_is_kept(client):
    make(client)
    client.put(
        "/api/terms",
        json={
            "lang": "fr",
            "lemma": "quai",
            "pos": "VERB",
            "status": 1,
            "context": "Il marchait le long du quai.",
        },
    )
    entry = next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == "quai"
    )
    assert entry["context"] == "Il marchait le long du quai."


def test_the_first_context_is_the_one_that_sticks(client):
    """Where you first met a word is the memorable one; later sightings aren't."""
    make(client)
    for ctx in ("first sighting", "second sighting"):
        client.put(
            "/api/terms",
            json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 1, "context": ctx},
        )
    entry = next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == "quai"
    )
    assert entry["context"] == "first sighting"
