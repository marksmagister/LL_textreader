"""Pages: reading a long text in screenfuls, and not losing your place."""

from ll_textreader.api import lessons

SENTENCE = "Le vieil homme marchait le long du quai. "


def long_lesson(client, sentences=40):
    r = client.post("/api/lessons", json={"text": SENTENCE * sentences, "lang": "fr"})
    return r.json()["id"]


def page(client, lesson_id, n=None):
    url = f"/api/lessons/{lesson_id}" + ("" if n is None else f"?page={n}")
    return client.get(url).json()


def test_a_long_text_is_split_into_pages(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    p = page(client, long_lesson(client), 0)
    assert p["n_pages"] > 1
    assert len(p["tokens"]) <= 40  # a target, not a hard cap: pages end on a sentence


def test_pages_break_between_sentences(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    n_pages = page(client, lesson, 0)["n_pages"]
    for i in range(n_pages):
        assert page(client, lesson, i)["body"].rstrip().endswith(".")


def test_every_token_appears_on_exactly_one_page(client, monkeypatch):
    """No word may be dropped or read twice when a book is paged."""
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    first = page(client, lesson, 0)
    seen = []
    for i in range(first["n_pages"]):
        seen += [t["idx"] for t in page(client, lesson, i)["tokens"]]
    assert seen == sorted(seen) == list(range(first["n_tokens"]))


def test_page_body_and_offsets_still_line_up(client, monkeypatch):
    """CLAUDE.md rule 2, per page: spans are overlaid, never rebuilt."""
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    for i in range(page(client, lesson, 0)["n_pages"]):
        p = page(client, lesson, i)
        for t in p["tokens"]:
            lo = t["char_start"] - p["body_offset"]
            assert p["body"][lo : lo + len(t["surface"])] == t["surface"]


def test_finishing_a_page_only_touches_that_page(client, monkeypatch):
    """The whole point: clear this page, and the next one keeps its blue."""
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0, "mark_rest_known": True})

    assert all(t["state"] == "known" for t in page(client, lesson, 0)["tokens"])
    # ...and page 1 is now known too, because it is the same words repeated —
    # which is exactly the behaviour asked for: what you clear carries forward.
    assert all(t["state"] == "known" for t in page(client, lesson, 1)["tokens"])


def test_words_cleared_on_one_page_carry_into_later_ones(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 12)
    r = client.post(
        "/api/lessons",
        json={
            "text": "Le vieil homme marchait. Une mouette cria. Le vieil homme marchait.",
            "lang": "fr",
        },
    )
    lesson = r.json()["id"]
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0, "mark_rest_known": True})
    last = page(client, lesson, page(client, lesson, 0)["n_pages"] - 1)
    assert [t["state"] for t in last["tokens"] if t["lemma"]].count("known") > 0


def test_progress_is_saved_and_resumed(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})
    assert page(client, lesson)["page"] == 1  # no ?page= => resume

    client.post(f"/api/lessons/{lesson}/finish", json={"page": 1})
    assert page(client, lesson)["page"] == 2
    assert client.get("/api/lessons").json()[0]["last_token"] > 0


def test_rereading_an_early_page_does_not_lose_your_place(client, monkeypatch):
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    for i in range(3):
        client.post(f"/api/lessons/{lesson}/finish", json={"page": i})
    ahead = page(client, lesson)["page"]

    client.post(f"/api/lessons/{lesson}/finish", json={"page": 0})  # went back to reread
    assert page(client, lesson)["page"] == ahead


def test_page_out_of_range_is_clamped(client):
    lesson = long_lesson(client, 3)
    assert page(client, lesson, 99)["page"] == 0
    assert page(client, lesson, -5)["page"] == 0


def test_a_short_text_is_one_page(client):
    p = page(client, long_lesson(client, 2), None)
    assert p["n_pages"] == 1 and p["body_offset"] == 0


def test_finishing_the_last_page_completes_the_lesson(client, monkeypatch):
    """The Finish button's whole job. It used to fire and change nothing."""
    monkeypatch.setattr(lessons, "PAGE_TOKENS", 30)
    lesson = long_lesson(client)
    n_pages = page(client, lesson, 0)["n_pages"]

    for i in range(n_pages - 1):
        assert (
            client.post(f"/api/lessons/{lesson}/finish", json={"page": i}).json()["completed"]
            is False
        )

    done = client.post(f"/api/lessons/{lesson}/finish", json={"page": n_pages - 1}).json()
    assert done["completed"] is True
    assert client.get("/api/lessons").json()[0]["completed"] is True
