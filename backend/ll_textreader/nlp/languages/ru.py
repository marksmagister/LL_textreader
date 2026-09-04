"""Russian: spaCy `ru_core_news_md`, POS-tagged lemmas.

The model as it comes, no hand rules yet. Russian is the language that stresses
the novel-form state hardest (decision 0012), so measure its morphology against
real prose the way French was before adding any — see the open question in
`docs/status.md`.
"""

from ._spacy import SpacyAdapter


class RussianAdapter(SpacyAdapter):
    lang = "ru"
    MODEL = "ru_core_news_md"


def adapter() -> RussianAdapter:
    return RussianAdapter()
