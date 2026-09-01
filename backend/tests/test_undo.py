"""Undoing "mark page known".

One misclick changes a hundred words at once. Being unable to take that back was
the single most annoying thing about the app this one is not a copy of.
"""

TEXT = "Il marchait le long du quai. Nous marchons."


def make(client):
    return client.post("/api/lessons", json={"text": TEXT, "lang": "fr"}).json()["id"]


def states(client, lesson):
    return {t["surface"]: t["state"] for t in client.get(f"/api/lessons/{lesson}").json()["tokens"]}


def mark_known(client, lesson):
    return client.post(f"/api/lessons/{lesson}/finish", json={"mark_rest_known": True}).json()


def test_marking_a_page_known_offers_an_undo(client):
    lesson = make(client)
    result = mark_known(client, lesson)
    assert result["undo_id"] is not None
    assert result["undo_n"] > 0
    assert set(states(client, lesson).values()) == {"known"}

    assert client.post(f"/api/lessons/undo/{result['undo_id']}").status_code == 204
    s = states(client, lesson)
    assert s["marchait"] == "new" and s["quai"] == "new"


def test_undo_removes_rows_rather_than_zeroing_them(client):
    """A word you never had an opinion about should go back to having no row,
    not to a row saying 0 — otherwise undo litters the lexicon."""
    lesson = make(client)
    result = mark_known(client, lesson)
    client.post(f"/api/lessons/undo/{result['undo_id']}")
    assert client.get("/api/vocab?lang=fr").json()["total"] == 0


def test_undo_leaves_words_you_had_already_judged_alone(client):
    """Only the blue words were changed, so only they are put back."""
    lesson = make(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 1})
    result = mark_known(client, lesson)
    client.post(f"/api/lessons/undo/{result['undo_id']}")

    s = states(client, lesson)
    assert s["quai"] == "learning"  # your judgement survived both the mark and the undo
    assert s["marchait"] == "new"


def test_undo_is_offered_only_when_something_changed(client):
    lesson = make(client)
    mark_known(client, lesson)
    again = mark_known(client, lesson)  # nothing blue left
    assert again["undo_id"] is None and again["undo_n"] == 0


def test_turning_a_page_normally_is_not_undoable(client):
    """Only bulk actions get an undo; a page turn changes nothing to regret."""
    lesson = make(client)
    assert client.post(f"/api/lessons/{lesson}/finish", json={"page": 0}).json()["undo_id"] is None


def test_an_action_cannot_be_undone_twice(client):
    lesson = make(client)
    result = mark_known(client, lesson)
    assert client.post(f"/api/lessons/undo/{result['undo_id']}").status_code == 204
    assert client.post(f"/api/lessons/undo/{result['undo_id']}").status_code == 409
    assert client.post("/api/lessons/undo/9999").status_code == 404
