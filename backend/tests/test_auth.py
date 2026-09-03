"""The door, and the wall between readers.

The wall is the part worth being paranoid about. Missing one call site means a
reader seeing somebody else's vocabulary, and that is not a bug you find by
reading — `USER_ID` was read at forty-one places before this. So the first test
here does not list the routes it checks: it enumerates them from the application,
which means a route added next year without a user fails this test on the day it
is written rather than the day somebody notices their words are wrong.
"""

import pytest

from ll_textreader import auth
from ll_textreader.config import settings
from ll_textreader.main import app

from .conftest import sign_in

# The only two routes that may answer without a session, and why.
#   /api/health     something has to reply before anyone has signed in, and it
#                   says nothing about any reader.
#   /api/dictionary Wiktionary glosses. Shared data, identical for everyone,
#                   with no user_id anywhere near it.
# /api/auth/* is the sign-in flow itself and is exempt as a prefix.
#
# This list is two entries long and should stay that way. Adding to it is a
# decision about what strangers can reach, not a way to make a test pass.
OPEN = {"/api/health", "/api/dictionary"}


def user_scoped_routes() -> list[tuple[str, str]]:
    """Every API route that ought to require a session, straight from the app.

    Read off the OpenAPI schema rather than walking `app.routes`, which in this
    version of FastAPI holds opaque wrappers for included routers rather than the
    routes themselves — a walk found nothing at all and the parametrised test
    below passed by vacuum. The schema is the application's own description of
    what it serves, so it cannot drift from what is actually mounted.
    """
    found = []
    for path, methods in app.openapi()["paths"].items():
        if not path.startswith("/api/"):
            continue
        if path in OPEN or path.startswith("/api/auth/"):
            continue
        for method in sorted(methods):
            found.append((method.upper(), path))
    return found


def test_there_are_routes_to_check():
    """A guard on the guard: if the enumeration silently found nothing, the
    parametrised test below would pass by vacuum."""
    assert len(user_scoped_routes()) >= 14


@pytest.mark.parametrize(("method", "path"), user_scoped_routes())
def test_every_user_route_refuses_a_stranger(env, method, path):
    """No session, no data. Whatever the route, whatever the arguments."""
    url = path.replace("{lesson_id}", "1").replace("{undo_id}", "1")
    response = env.request(method, url, json={})
    assert response.status_code == 401, f"{method} {path} answered {response.status_code}"


def test_health_and_dictionary_stay_open(env):
    assert env.get("/api/health").status_code == 200
    assert env.get("/api/dictionary?lang=fr&lemma=chat").status_code == 200


# ---------------------------------------------------------------- sessions


def test_signing_in_and_out(client):
    assert client.get("/api/auth/me").json()["user"]["name"] == "alice"
    assert client.post("/api/auth/logout").status_code == 204
    assert client.get("/api/auth/me").json()["user"] is None
    # The session is gone from the server, not merely from this browser.
    assert client.get("/api/lessons").status_code == 401


def test_logging_out_does_not_end_anyone_elses_session(client, other):
    client.post("/api/auth/logout")
    assert other.get("/api/lessons").status_code == 200


def test_an_unknown_cookie_is_not_a_session(env):
    env.cookies.set(auth.COOKIE, "not-a-real-token")
    assert env.get("/api/lessons").status_code == 401


def test_me_answers_before_anyone_has_signed_in(env):
    """200 with a null user, not 401: 'nobody is signed in' is a normal answer
    to this question, and the front end has to be able to ask it."""
    body = env.get("/api/auth/me").json()
    assert body["user"] is None
    assert body["signup"] is True


# ---------------------------------------------------------------- the cap


def test_signup_closes_when_the_cap_is_reached(env, monkeypatch):
    monkeypatch.setattr(settings, "max_users", 1)
    sign_in(env, "alice", "sub-alice")
    assert env.get("/api/auth/me").json()["signup"] is False


def test_a_full_house_does_not_lock_out_the_people_already_in(env, monkeypatch):
    sign_in(env, "alice", "sub-alice")
    monkeypatch.setattr(settings, "max_users", 0)
    assert env.get("/api/lessons").status_code == 200


def test_signup_off_refuses_everyone(env, monkeypatch):
    monkeypatch.setattr(settings, "signup", "off")
    assert env.get("/api/auth/me").json()["signup"] is False


# ---------------------------------------------------------------- the wall
# The tests above prove every route asks *whether* you are signed in. These
# prove it matters *who* you are, which is the failure that would actually hurt.


def make_lesson(c, text="Il marchait le long des quais."):
    return c.post("/api/lessons", json={"text": text, "lang": "fr"}).json()["id"]


def test_one_reader_cannot_see_anothers_library(client, other):
    make_lesson(client)
    assert len(client.get("/api/lessons").json()) == 1
    assert other.get("/api/lessons").json() == []


def test_one_reader_cannot_open_anothers_lesson(client, other):
    lesson = make_lesson(client)
    assert client.get(f"/api/lessons/{lesson}").status_code == 200
    # 404, not 403: whether a lesson exists is itself somebody else's business.
    assert other.get(f"/api/lessons/{lesson}").status_code == 404


def test_one_reader_cannot_delete_anothers_lesson(client, other):
    lesson = make_lesson(client)
    assert other.delete(f"/api/lessons/{lesson}").status_code == 404
    assert client.get(f"/api/lessons/{lesson}").status_code == 200


def test_one_reader_cannot_finish_or_recollect_anothers_lesson(client, other):
    lesson = make_lesson(client)
    assert other.post(f"/api/lessons/{lesson}/finish", json={"page": 0}).status_code == 404
    assert other.put(f"/api/lessons/{lesson}/collection", json={"name": "mine"}).status_code == 404
    assert other.get(f"/api/lessons/{lesson}/translation").status_code == 404


def test_lexicons_do_not_mix(client, other):
    """The one that would be worst: two readers' word statuses running together."""
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "NOUN", "status": 5})
    assert [e["lemma"] for e in client.get("/api/vocab?lang=fr").json()["entries"]] == ["quai"]
    assert other.get("/api/vocab?lang=fr").json()["entries"] == []


def test_marking_a_word_known_does_not_change_anyone_elses_page(client, other):
    """The join is per reader, so the same text reads differently for each. This
    is the whole product working, and the thing user_id has to get right."""
    mine, theirs = make_lesson(client), make_lesson(other)
    # With the surface, so the form counts as met and the word renders plain.
    # Without it this is correctly "novel-form" — marking a lemma known must not
    # claim you have met a shape of it you have never seen.
    client.put(
        "/api/terms",
        json={"lang": "fr", "lemma": "marcher", "pos": "VERB", "status": 5, "surface": "marchait"},
    )
    states = {t["surface"]: t["state"] for t in client.get(f"/api/lessons/{mine}").json()["tokens"]}
    assert states["marchait"] == "known"
    others = {
        t["surface"]: t["state"] for t in other.get(f"/api/lessons/{theirs}").json()["tokens"]
    }
    assert others["marchait"] == "new"


def test_one_reader_cannot_undo_anothers_bulk_action(client, other):
    lesson = make_lesson(client)
    undo = client.post(f"/api/lessons/{lesson}/finish", json={"page": 0, "mark_rest_known": True})
    undo_id = undo.json()["undo_id"]
    assert undo_id is not None
    assert other.post(f"/api/lessons/undo/{undo_id}").status_code == 404
    assert client.post(f"/api/lessons/undo/{undo_id}").status_code == 204


def test_exporting_gives_you_only_your_own(client, other):
    make_lesson(client)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "NOUN", "status": 5})
    assert b"marchait" in client.get("/api/account/export").content
    assert b"marchait" not in other.get("/api/account/export").content


def test_deleting_an_account_leaves_the_other_untouched(client, other):
    make_lesson(client)
    lesson = make_lesson(other)
    client.put("/api/terms", json={"lang": "fr", "lemma": "quai", "pos": "NOUN", "status": 5})
    assert client.delete("/api/account").status_code == 204
    assert other.get(f"/api/lessons/{lesson}").status_code == 200
    assert other.get("/api/lessons").json() != []
