"""Exporting the lexicon — the one part of the database that cannot be rebuilt."""

import json


def learn(client, lemma, pos="NOUN", status=1, **extra):
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": lemma, "pos": pos, "status": status, **extra},
    )


def get(client, **params):
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return client.get(f"/api/vocab/export?lang=fr&{query}")


def test_anki_file_carries_its_own_import_settings(client):
    """Anki 2.1.55+ reads these, so importing needs no field-mapping dialog."""
    learn(client, "quai")
    body = get(client, format="anki").text
    assert body.startswith("#separator:tab")
    for directive in ("#html:true", "#notetype:Basic", "#tags column:3"):
        assert directive in body


def test_a_card_carries_what_you_know_about_the_word(client):
    learn(client, "quai", note="a quay", context="Il marchait le long du quai.", surface="quai")
    row = [ln for ln in get(client, format="anki").text.splitlines() if ln.startswith("quai")][0]
    front, back, tags = row.split("\t")
    assert front == "quai"
    assert "a quay" in back and "le long du quai" in back and "quai" in back
    assert "ll_textreader" in tags and "fr" in tags and "learning" in tags


def test_homographs_do_not_collide(client):
    """Anki's Basic type deduplicates on the first field, so `porte` the door
    would silently overwrite `porte` the verb."""
    learn(client, "porte", pos="NOUN")
    learn(client, "porte", pos="VERB")
    fronts = [
        ln.split("\t")[0]
        for ln in get(client, format="anki").text.splitlines()
        if not ln.startswith("#")
    ]
    assert sorted(fronts) == ["porte (noun)", "porte (verb)"]


def test_a_lone_lemma_keeps_a_clean_front(client):
    learn(client, "quai")
    fronts = [
        ln.split("\t")[0]
        for ln in get(client, format="anki").text.splitlines()
        if not ln.startswith("#")
    ]
    assert fronts == ["quai"]


def test_tabs_and_newlines_never_break_a_row(client):
    """A note with a newline in it would otherwise split one card into two."""
    learn(client, "quai", note="line one\nline two\twith a tab")
    rows = [ln for ln in get(client, format="anki").text.splitlines() if not ln.startswith("#")]
    assert len(rows) == 1
    assert rows[0].count("\t") == 2  # exactly three fields
    assert "line one<br>line two with a tab" in rows[0]


def test_html_in_a_note_is_escaped_not_rendered(client):
    learn(client, "quai", note="<script>alert(1)</script>")
    assert "&lt;script&gt;" in get(client, format="anki").text


# ---------------------------------------------------------------- choosing what


def test_export_can_be_narrowed_to_one_bucket(client):
    learn(client, "quai", status=1)
    learn(client, "mer", status=5)
    learning = get(client, format="csv", status="learning").text
    assert "quai" in learning and "mer" not in learning


def test_export_can_be_narrowed_to_a_selection(client):
    """The words you ticked in the list."""
    learn(client, "quai")
    learn(client, "mer")
    learn(client, "porte")
    body = get(client, format="csv", keys="quai:NOUN,porte:NOUN").text
    assert "quai" in body and "porte" in body and "mer" not in body


def test_filters_compose(client):
    learn(client, "quai", status=1)
    learn(client, "quille", status=5)
    body = get(client, format="csv", status="learning", q="qu").text
    assert "quai" in body and "quille" not in body


def test_everything_by_default(client):
    for lemma in ("quai", "mer", "porte"):
        learn(client, lemma)
    assert len(get(client, format="json").json()["entries"]) == 3


# ---------------------------------------------------------------- other formats


def test_csv_has_a_header_and_a_row_per_word(client):
    learn(client, "quai", note="a quay")
    lines = get(client, format="csv").text.strip().splitlines()
    assert lines[0].startswith("lemma,pos,status")
    assert len(lines) == 2 and "a quay" in lines[1]


def test_json_round_trips_everything(client):
    learn(client, "quai", note="a quay", context="Il marchait.", surface="quai")
    data = json.loads(get(client, format="json").text)
    entry = data["entries"][0]
    assert data["lang"] == "fr"
    assert entry["lemma"] == "quai" and entry["note"] == "a quay"
    assert entry["context"] == "Il marchait." and entry["forms"] == ["quai"]


def test_the_file_downloads_rather_than_displaying(client):
    learn(client, "quai")
    r = get(client, format="anki", status="learning")
    assert "attachment" in r.headers["content-disposition"]
    assert "ll_textreader-fr-learning.tsv" in r.headers["content-disposition"]


def test_an_unknown_format_is_refused(client):
    assert get(client, format="pdf").status_code == 400
