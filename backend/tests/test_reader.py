"""End-to-end over the thing that is actually the product: import, then the join."""

TEXT = "Il marchait le long du quai. Nous marchons."


def states(client, lesson_id):
    tokens = client.get(f"/api/lessons/{lesson_id}").json()["tokens"]
    return {t["surface"]: t["state"] for t in tokens}


def make_lesson(client, text=TEXT):
    r = client.post("/api/lessons", json={"text": text, "lang": "fr"})
    assert r.status_code == 201, r.text
    return r.json()


def test_import_stores_a_token_stream(client):
    lesson = make_lesson(client)
    assert lesson["title"] == "Il marchait le long du quai. Nous marchons."
    assert lesson["n_tokens"] == 10  # 8 words + 2 full stops
    assert lesson["n_words"] == 8
    assert client.get("/api/lessons").json()[0]["id"] == lesson["id"]


def test_offsets_index_into_the_original_body(client):
    """CLAUDE.md rule 2: spans are overlaid onto lesson.body, never rebuilt."""
    detail = client.get(f"/api/lessons/{make_lesson(client)['id']}").json()
    body = detail["body"]
    for t in detail["tokens"]:
        assert body[t["char_start"] : t["char_end"]] == t["surface"]


def test_everything_starts_new_and_punctuation_is_plain(client):
    s = states(client, make_lesson(client)["id"])
    assert s["marchait"] == "new"
    assert s["."] == "known"  # nothing to learn; rendered plain, not clickable


def test_known_lemma_in_an_unmet_form_gets_its_own_state(client):
    """The whole reason status is keyed on the lemma and forms are tracked apart."""
    lesson = make_lesson(client)
    r = client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchait"},
    )
    assert r.json()["state"] == "known"

    s = states(client, lesson["id"])
    assert s["marchait"] == "known"  # the form you met
    assert s["marchons"] == "novel-form"  # same word, shape you haven't
    assert s["quai"] == "new"


def test_a_learning_word_still_marks_forms_you_have_not_met(client):
    """Marking `marchait` must not turn `marchons` plain yellow: you have never
    met that shape. Reported from real reading — the novel-form distinction is
    not only for words you already know."""
    lesson = make_lesson(client)
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 1, "surface": "marchait"},
    )
    s = states(client, lesson["id"])
    assert s["marchait"] == "learning"  # the form you met
    assert s["marchons"] == "novel-form"  # same word, shape you have not


def test_finish_records_the_forms_you_have_now_met(client):
    lesson = make_lesson(client)
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchait"},
    )
    assert states(client, lesson["id"])["marchons"] == "novel-form"

    client.post(f"/api/lessons/{lesson['id']}/finish", json={"mark_rest_known": False})
    s = states(client, lesson["id"])
    assert s["marchons"] == "known"  # met it now
    assert s["quai"] == "new"  # not known, so not touched


def test_mark_rest_known_clears_the_page(client):
    """CLAUDE.md rule 8: the pressure valve."""
    lesson = make_lesson(client)
    client.post(f"/api/lessons/{lesson['id']}/finish", json={"mark_rest_known": True})
    assert set(states(client, lesson["id"]).values()) == {"known"}


def test_mark_rest_known_leaves_learning_words_alone(client):
    """ "Rest" means the blue ones. A word you are part-way through learning is not
    "the rest" — you made a decision about it and the button must not undo it."""
    lesson = make_lesson(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 2})
    client.post(f"/api/lessons/{lesson['id']}/finish", json={"mark_rest_known": True})

    # the status is what must survive; the colour depends on which form you met
    quai = next(
        e for e in client.get("/api/vocab?lang=fr").json()["entries"] if e["lemma"] == "quai"
    )
    # The level may have risen -- finishing a page counts as an encounter --
    # but it must not have been marked known.
    assert 1 <= quai["status"] <= 4
    assert states(client, lesson["id"])["long"] == "known"  # was blue, now cleared


def test_mark_rest_known_leaves_ignored_words_ignored(client):
    lesson = make_lesson(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": -1})
    client.post(f"/api/lessons/{lesson['id']}/finish", json={"mark_rest_known": True})
    r = client.get(f"/api/lessons/{lesson['id']}").json()
    assert all(t["state"] == "known" for t in r["tokens"])


def test_delete_and_unknown_lesson(client):
    lesson = make_lesson(client)
    assert client.delete(f"/api/lessons/{lesson['id']}").status_code == 204
    assert client.get(f"/api/lessons/{lesson['id']}").status_code == 404


def test_unknown_language_is_rejected(client):
    r = client.post("/api/lessons", json={"text": "hallo", "lang": "xx"})
    assert r.status_code == 400


def test_lesson_summary_reports_what_you_can_already_read(client):
    """The library needs to show the shape of a text before you open it."""
    lesson = make_lesson(client)
    before = client.get("/api/lessons").json()[0]
    assert before["n_new"] == before["n_words"] and before["n_known"] == 0

    client.put("/api/terms", json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5})
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 2})
    after = client.get("/api/lessons").json()[0]

    assert after["n_known"] == 2  # marchait and marchons
    assert after["n_learning"] == 1
    assert after["n_new"] == after["n_words"] - 3
    # the three buckets must account for every word, or the bar lies
    assert after["n_new"] + after["n_learning"] + after["n_known"] == after["n_words"]
    assert client.get(f"/api/lessons/{lesson['id']}").json()["n_known"] == 2


def test_ignored_words_count_as_readable(client):
    make_lesson(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": -1})
    assert client.get("/api/lessons").json()[0]["n_known"] == 1


def test_tokens_say_whether_you_overrode_them(client):
    lesson = make_lesson(client, "Les quais sont longs.")
    assert not any(
        t["overridden"] for t in client.get(f"/api/lessons/{lesson['id']}").json()["tokens"]
    )

    client.put("/api/terms/override", json={"lang": "fr", "surface": "quais"})
    tokens = client.get(f"/api/lessons/{lesson['id']}").json()["tokens"]
    assert [t["surface"] for t in tokens if t["overridden"]] == ["quais"]


def test_a_blank_import_is_refused(client):
    """Whitespace passes a min-length check; cleaning is what decides. Text is
    optional now that a url can be given instead, so both empty cases are 400."""
    assert client.post("/api/lessons", json={"text": "   \n  ", "lang": "fr"}).status_code == 400
    assert client.post("/api/lessons", json={"text": "", "lang": "fr"}).status_code == 400
    assert client.post("/api/lessons", json={"lang": "fr"}).status_code == 400
    assert client.get("/api/lessons").json() == []


def test_counts_are_zero_not_null_for_a_lesson_with_no_words(client):
    """A lesson of pure punctuation still has to produce a summary."""
    lesson = client.post("/api/lessons", json={"text": "... !!! ...", "lang": "fr"}).json()
    assert lesson["n_words"] == 0
    assert (lesson["n_new"], lesson["n_learning"], lesson["n_known"]) == (0, 0, 0)
