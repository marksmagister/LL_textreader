"""The lexicon list, and the escape hatch when the lemmatiser is wrong."""


def make(client, text="Il marchait le long du quai. Nous marchons."):
    return client.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]


def entry(client, lemma):
    return next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == lemma
    )


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


# ---------------------------------------------------------------- sorting


def read_page(client, lesson, page=0):
    client.post(f"/api/lessons/{lesson}/finish", json={"page": page})


def test_last_seen_is_when_you_last_met_it_not_when_you_judged_it(client):
    lesson = make(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 1})
    assert entry(client, "marcher")["last_seen"] is None  # judged, never read past

    read_page(client, lesson)
    assert entry(client, "marcher")["last_seen"] is not None


def test_stale_puts_the_forgotten_words_first(client):
    """The point of the feature: words you were learning that stopped appearing.

    Compared by whether they have been met at all rather than by timestamp —
    seen_at has one-second resolution and two page turns in a test tie."""
    lesson = make(client, "Il marchait le long du quai.")
    client.put("/api/terms", json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 1})
    # flagged once and never met again — the case the feature exists to surface
    client.put("/api/terms", json={"lang": "fr", "lemma": "oublie", "pos": "VERB", "status": 1})
    read_page(client, lesson)

    stale = [e["lemma"] for e in client.get("/api/vocab?lang=fr&sort=stale").json()["entries"]]
    recent = [e["lemma"] for e in client.get("/api/vocab?lang=fr&sort=recent").json()["entries"]]
    assert stale[0] == "oublie"
    assert recent[-1] == "oublie"


def test_alpha_sorts_by_lemma(client):
    for lemma in ("zebre", "abeille", "mouette"):
        client.put("/api/terms", json={"lang": "fr", "lemma": lemma, "pos": "NOUN", "status": 1})
    got = [e["lemma"] for e in client.get("/api/vocab?lang=fr&sort=alpha").json()["entries"]]
    assert got == ["abeille", "mouette", "zebre"]


def test_an_unknown_sort_is_refused_rather_than_ignored(client):
    assert client.get("/api/vocab?lang=fr&sort=sideways").status_code == 400


def test_sorting_does_not_change_what_is_counted(client):
    for lemma in ("zebre", "abeille"):
        client.put("/api/terms", json={"lang": "fr", "lemma": lemma, "pos": "NOUN", "status": 1})
    for sort in ("recent", "stale", "alpha", "forms"):
        assert client.get(f"/api/vocab?lang=fr&sort={sort}").json()["total"] == 2


# ---------------------------------------------------------------- override × bulk
#
# The override has to win in the statements that *write*, not only the ones that
# read. It didn't: "mark page known" wrote to the pipeline's lemma while the undo
# log recorded the override's, so the word stayed blue, undo deleted a row it had
# never created, and the pipeline's lemma was left known for ever.


def test_mark_page_known_follows_the_override(client):
    lesson = make(client, "Les quais sont longs.")
    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais"})
    client.post(f"/api/lessons/{lesson}/finish", json={"mark_rest_known": True})
    assert states(client, lesson)["quais"] == "known"


def test_undoing_it_leaves_no_word_behind(client):
    lesson = make(client, "Les quais sont longs.")
    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais"})
    done = client.post(f"/api/lessons/{lesson}/finish", json={"mark_rest_known": True}).json()
    client.post(f"/api/lessons/undo/{done['undo_id']}")
    assert client.get("/api/vocab?lang=fr").json()["total"] == 0
    assert states(client, lesson)["quais"] == "new"


def test_finishing_a_page_records_forms_for_an_overridden_word(client):
    """Otherwise a word you know reads as a novel form for ever."""
    lesson = make(client, "Les quais sont longs.")
    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais"})
    client.put("/api/terms", json={"lang": "fr", "lemma": "quais", "pos": "X", "status": 5})
    assert states(client, lesson)["quais"] == "novel-form"

    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert states(client, lesson)["quais"] == "known"
