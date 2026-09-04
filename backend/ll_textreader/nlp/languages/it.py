"""Italian: spaCy `it_core_news_md`, POS-tagged lemmas.

The control language (decision 0012): morphologically light, close to French, and
the thing that tells you whether the novel-form state earns its keep. The model
as it comes, no hand rules.
"""

from ._spacy import SpacyAdapter


class ItalianAdapter(SpacyAdapter):
    lang = "it"
    MODEL = "it_core_news_md"


def adapter() -> ItalianAdapter:
    return ItalianAdapter()
