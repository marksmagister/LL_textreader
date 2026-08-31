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


def test_learning_status_shows_as_learning_whatever_the_form(client):
    lesson = make_lesson(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 1})
    s = states(client, lesson["id"])
    assert s["marchait"] == s["marchons"] == "learning"


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
