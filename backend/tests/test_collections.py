"""Collections: a book, a series, an ordered group of lessons."""


def make(client, title):
    return client.post(
        "/api/lessons", json={"text": "Il marchait le long du quai.", "title": title, "lang": "fr"}
    ).json()["id"]


def put(client, lesson_id, name):
    return client.put(f"/api/lessons/{lesson_id}/collection", json={"name": name})


def library(client):
    return {x["title"]: x for x in client.get("/api/lessons").json()}


def test_naming_a_collection_creates_it(client):
    a = make(client, "Chapitre I")
    assert put(client, a, "L'Étranger").json()["collection"] == "L'Étranger"
    assert library(client)["Chapitre I"]["collection"] == "L'Étranger"


def test_the_same_name_twice_is_the_same_collection(client):
    """There is no screen for managing collections, and there should not need to
    be one: typing the same name is how you put two things together."""
    a, b = make(client, "Chapitre I"), make(client, "Chapitre II")
    put(client, a, "L'Étranger")
    put(client, b, "L'Étranger")
    rows = library(client)
    assert rows["Chapitre I"]["collection_id"] == rows["Chapitre II"]["collection_id"]


def test_lessons_keep_the_order_they_were_added_in(client):
    ids = [make(client, f"Chapitre {n}") for n in ("I", "II", "III")]
    for i in ids:
        put(client, i, "L'Étranger")
    rows = library(client)
    assert [rows[f"Chapitre {n}"]["position"] for n in ("I", "II", "III")] == [1, 2, 3]


def test_an_empty_name_takes_it_back_out(client):
    a = make(client, "Chapitre I")
    put(client, a, "L'Étranger")
    assert put(client, a, "").json()["collection"] is None
    assert library(client)["Chapitre I"]["collection_id"] is None


def test_a_collection_nobody_is_in_disappears(client):
    """Otherwise the suggestions fill up with names of things you dissolved."""
    a = make(client, "Chapitre I")
    put(client, a, "Temporaire")
    put(client, a, "")
    b = make(client, "Chapitre II")
    put(client, b, "Autre")
    # only the collection still in use survives
    assert {x["collection"] for x in client.get("/api/lessons").json() if x["collection"]} == {
        "Autre"
    }


def test_moving_between_collections(client):
    a = make(client, "Chapitre I")
    put(client, a, "Premier")
    put(client, a, "Second")
    assert library(client)["Chapitre I"]["collection"] == "Second"


def test_deleting_a_lesson_leaves_the_others_alone(client):
    a, b = make(client, "Chapitre I"), make(client, "Chapitre II")
    put(client, a, "L'Étranger")
    put(client, b, "L'Étranger")
    client.delete(f"/api/lessons/{a}")
    assert library(client)["Chapitre II"]["collection"] == "L'Étranger"


def test_a_loose_lesson_reports_no_collection(client):
    make(client, "Seul")
    row = library(client)["Seul"]
    assert row["collection"] is None and row["collection_id"] is None
