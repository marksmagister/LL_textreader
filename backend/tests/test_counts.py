"""The library's counts are cached. This is the test that they never drift.

Every operation that could move a word between new, learning and known is
exercised, and after each one the stored numbers are compared against counting
from scratch. A drifted count is worse than a slow one, so if this file ever
fails, the cache is wrong and not the assertion.
"""

import pytest

from ll_textreader.db import USER_ID, connect

TEXT = "Il marchait le long du quai. Nous marchons vers le quai."

TRUTH = """
SELECT COALESCE(SUM(t.lemma IS NOT NULL AND (s.status IS NULL OR s.status = 0)), 0),
       COALESCE(SUM(t.lemma IS NOT NULL AND s.status BETWEEN 1 AND 4), 0),
       COALESCE(SUM(t.lemma IS NOT NULL AND (s.status >= 5 OR s.status = -1)), 0)
FROM token t
LEFT JOIN lemma_override o ON o.user_id = ? AND o.lang = 'fr' AND o.surface = t.norm
LEFT JOIN lemma_status s ON s.user_id = ? AND s.lang = 'fr'
     AND s.lemma = COALESCE(o.to_lemma, t.lemma) AND s.pos = COALESCE(o.to_pos, t.pos)
WHERE t.lesson_id = ?
"""


def assert_honest(client):
    """Stored counts equal counted-from-scratch, for every lesson."""
    with connect() as conn:
        for row in conn.execute("SELECT id, n_new, n_learning, n_known FROM lesson"):
            truth = conn.execute(TRUTH, (USER_ID, USER_ID, row["id"])).fetchone()
            assert (row["n_new"], row["n_learning"], row["n_known"]) == tuple(truth), (
                f"lesson {row['id']} drifted: stored {tuple(row)[1:]} vs actual {tuple(truth)}"
            )


@pytest.fixture
def lesson(client):
    return client.post("/api/lessons", json={"text": TEXT, "lang": "fr"}).json()["id"]


def test_a_fresh_import_is_counted(client, lesson):
    assert_honest(client)
    row = client.get("/api/lessons").json()[0]
    assert row["n_new"] == row["n_words"] and row["n_known"] == 0


def test_learning_a_word(client, lesson):
    client.put("/api/terms", json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 1})
    assert_honest(client)


def test_knowing_a_word(client, lesson):
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    assert_honest(client)


def test_ignoring_a_word(client, lesson):
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": -1})
    assert_honest(client)


def test_moving_a_word_back_and_forth(client, lesson):
    for status in (1, 5, 1, -1, 0, 5):
        client.put(
            "/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": status}
        )
        assert_honest(client)


def test_a_level_rising_does_not_change_them(client, lesson):
    """1→2→3 stays inside learning, so the counts must not move — and must also
    not go stale."""
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 1})
    before = client.get("/api/lessons").json()[0]
    for page in range(3):
        client.post(f"/api/lessons/{lesson}/finish", json={"page": page})
        assert_honest(client)
    after = client.get("/api/lessons").json()[0]
    assert (before["n_new"], before["n_learning"]) == (after["n_new"], after["n_learning"])


def test_marking_a_page_known(client, lesson):
    client.post(f"/api/lessons/{lesson}/finish", json={"mark_rest_known": True})
    assert_honest(client)
    assert client.get("/api/lessons").json()[0]["n_new"] == 0


def test_undoing_it(client, lesson):
    result = client.post(f"/api/lessons/{lesson}/finish", json={"mark_rest_known": True}).json()
    client.post(f"/api/lessons/undo/{result['undo_id']}")
    assert_honest(client)


def test_an_override_and_its_removal(client, lesson):
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    assert_honest(client)
    client.put("/api/terms/override", json={"lang": "fr", "surface": "quai"})
    assert_honest(client)
    client.delete("/api/terms/override?lang=fr&surface=quai")
    assert_honest(client)


def test_a_second_lesson_sharing_words_is_counted_too(client, lesson):
    """The word is in both, so judging it once has to move both."""
    other = client.post("/api/lessons", json={"text": "Le quai est long.", "lang": "fr"}).json()
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    assert_honest(client)
    assert client.get(f"/api/lessons/{other['id']}").json()["n_known"] > 0


def test_counts_survive_reprocessing(client, lesson):
    """Re-tokenising replaces every token, so the counts are computed over
    different rows afterwards."""
    from ll_textreader.importers.plain_text import reprocess

    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "VERB", "status": 5})
    with connect() as conn:
        # the body changes too, which is the case that would drift
        conn.execute("UPDATE lesson SET body = ? WHERE id = ?", ("Le quai. Le quai.", lesson))
        reprocess(conn, lesson, force=True)
        conn.commit()
    assert_honest(client)
