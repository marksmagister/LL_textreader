"""Wiktionary glosses: loading them, and looking one up.

The data is a kaikki.org extract of the English Wiktionary's French entries —
French headwords, English definitions. CC BY-SA, downloaded by
`scripts/setup-dictionary.sh`, never vendored (see NOTICE).
"""

import json
import sqlite3
from collections.abc import Iterator
from pathlib import Path

# Wiktionary's part-of-speech names -> the UD tags our tokens carry, so a gloss
# can be matched against the POS the tagger assigned. Anything unmapped is kept
# uppercased and simply won't match a token exactly; lookup falls back to lemma.
UD_POS = {
    "noun": "NOUN",
    "name": "PROPN",
    "proper-noun": "PROPN",
    "verb": "VERB",
    "adj": "ADJ",
    "adv": "ADV",
    "pron": "PRON",
    "det": "DET",
    "article": "DET",
    "prep": "ADP",
    "postp": "ADP",
    "conj": "CCONJ",
    "particle": "PART",
    "intj": "INTJ",
    "num": "NUM",
    "punct": "PUNCT",
}

# Per headword+POS. Wiktionary happily lists twenty senses for "faire"; the
# panel is a reading aid, not the dictionary itself.
MAX_SENSES = 6


def parse(path: Path, lang: str) -> Iterator[tuple[str, str, str, str, int, str]]:
    """Stream the extract, yielding `hint` rows. Never holds the file in memory."""
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue  # a truncated last line from an interrupted download
            if entry.get("lang_code") != lang:
                continue
            word, pos = entry.get("word"), entry.get("pos")
            if not word or not pos:
                continue
            tag = UD_POS.get(pos, pos.upper())
            rank = 0
            for sense in entry.get("senses") or []:
                # Inflected entries ("marchait: third-person singular of marcher")
                # are noise here: the lemmatiser already did that job, and keeping
                # them would put "form of X" where the definition should be.
                if sense.get("form_of") or "form-of" in (sense.get("tags") or []):
                    continue
                glosses = sense.get("glosses") or []
                if not glosses:
                    continue
                yield (lang, "en", word, tag, rank, glosses[-1])
                rank += 1
                if rank >= MAX_SENSES:
                    break


def load(conn: sqlite3.Connection, path: Path, lang: str) -> int:
    """Replace this language's Wiktionary hints. Not user data; safe to rebuild."""
    conn.execute("DELETE FROM hint WHERE lang = ? AND source = 'wiktionary'", (lang,))
    n = 0
    batch: list[tuple] = []
    for lang_, target, word, tag, rank, gloss in parse(path, lang):
        batch.append((lang_, target, word, tag, gloss, rank, "wiktionary"))
        if len(batch) >= 20_000:
            conn.executemany(
                "INSERT INTO hint (lang, target_lang, lemma, pos, gloss, rank, source)"
                " VALUES (?,?,?,?,?,?,?)",
                batch,
            )
            n += len(batch)
            batch.clear()
    if batch:
        conn.executemany(
            "INSERT INTO hint (lang, target_lang, lemma, pos, gloss, rank, source)"
            " VALUES (?,?,?,?,?,?,?)",
            batch,
        )
        n += len(batch)
    conn.commit()
    return n


def lookup(conn: sqlite3.Connection, lang: str, lemma: str, pos: str | None) -> list[dict]:
    """Glosses for a word, the ones matching its part of speech first.

    POS is a sort key rather than a filter: when the tagger and Wiktionary
    disagree, showing the other reading beats showing nothing.
    """
    rows = conn.execute(
        """
        SELECT pos, gloss, source FROM hint
        WHERE lang = ? AND lemma = ?
        ORDER BY (pos = ?) DESC, source = 'user' DESC, rank
        LIMIT 12
        """,
        (lang, lemma, pos or ""),
    ).fetchall()
    return [{"pos": r["pos"], "gloss": r["gloss"], "source": r["source"]} for r in rows]


def _main() -> None:
    """`python -m ll_textreader.dictionary <lang> <path>` — called by scripts/."""
    import sys

    from .db import connect, init_db

    lang, path = sys.argv[1], Path(sys.argv[2])
    init_db()
    with connect() as conn:
        n = load(conn, path, lang)
    print(f"loaded {n:,} glosses for {lang!r}")


if __name__ == "__main__":
    _main()
