"""The pages that have to exist before strangers do.

Google's consent screen wants a privacy policy at a URL it can fetch, and anyone
deciding whether to sign up has to be able to read one *without* signing up. Both
would be easy to break silently — a static mount at "/" swallows any path not
claimed before it — so they are pinned here.
"""

import pytest


@pytest.mark.parametrize("path", ["/privacy", "/terms"])
def test_the_legal_pages_are_readable_without_signing_in(env, path):
    r = env.get(path)
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]


@pytest.mark.parametrize("path", ["/privacy", "/terms"])
def test_they_say_the_things_that_make_them_useful(env, path):
    body = env.get(path).text
    # Deletion and export are the two rights the app actually implements, and
    # the policy promising them is what makes them meaningful.
    assert "delete" in body.lower()
    assert "GDPR" in body or "AGPL" in body


def test_they_are_still_marked_as_a_draft(env):
    """Deliberately failing once the placeholders are filled in and the box is
    removed. Better a test that has to be deleted on purpose than a policy that
    quietly goes live saying [OPERATOR NAME]."""
    assert "[OPERATOR NAME]" in env.get("/privacy").text
    assert "draft" in env.get("/terms").text.lower()
