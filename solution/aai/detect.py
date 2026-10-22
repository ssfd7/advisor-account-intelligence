"""Concept detection (pipeline step 1): link product mentions in a note to the catalog and find asset figures.

Entity linking is deterministic and runs over the approved catalog only: catalog names first, then aliases, the
longest phrase first, whole words only. A word for a kind of product that links to no offering is reported as
unresolved for the SME. Asset figures are read with the metric words in their sentence and keep the sentence's
scope; they are the advisor's statement, not a reported figure. Nothing here writes to memory: the output is
working memory for the semantic QBR draft.
"""
import re
from dataclasses import dataclass, field

import yaml

from . import DATA

SCALE = {"million": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9, "b": 1e9}
MONEY = re.compile(r"\$\s?(\d+(?:\.\d+)?)\s*(million|billion|bn|m|b)\b", re.I)
SCOPE = re.compile(r"\b(across [^.,;]+|on (?:the )?[A-Z][^.,;]+|at [A-Z][^.,;]+)")


@dataclass
class Mention:
    phrase: str
    start: int
    end: int
    sentence: tuple          # (start, end) offsets of the sentence that contains the mention
    target: str | None       # offering or platform id; None when unresolved
    target_kind: str | None  # "offering" or "platform"
    method: str              # "name", "alias" or "unresolved"


@dataclass
class AssetFigure:
    text: str
    start: int
    end: int
    sentence: tuple
    metric: str              # a metric id from asset_definitions.yaml, or "unknown"
    value: float
    currency: str
    scope: str
    rules: list = field(default_factory=list)  # ids of the computation rules that govern the figure


def reference(data=DATA):
    ref = data / "reference"
    return yaml.safe_load((ref / "catalog.yaml").read_text()), yaml.safe_load((ref / "asset_definitions.yaml").read_text())


def sentences(text: str) -> list:
    """(start, end) of each sentence: split at a full stop, question mark or blank line."""
    out, start = [], 0
    for m in re.finditer(r"[.?!](?=\s)|\n\s*\n", text):
        end = m.end()
        if text[start:end].strip():
            lead = len(text[start:end]) - len(text[start:end].lstrip())
            out.append((start + lead, end))
        start = end
    if text[start:].strip():
        out.append((start + len(text[start:]) - len(text[start:].lstrip()), len(text.rstrip())))
    return out


def _sentence_of(spans, pos):
    return next((s for s in spans if s[0] <= pos < s[1]), (pos, pos))


def _phrases(catalog):
    found = []
    for kind, items in (("offering", catalog["offerings"]), ("platform", catalog["platforms"])):
        for item in items:
            found.append((item["name"], item["id"], kind, "name"))
            found += [(a, item["id"], kind, "alias") for a in item.get("aliases", [])]
    return sorted(found, key=lambda p: -len(p[0]))


def _find(text, phrase):
    flags = 0 if phrase.isupper() else re.I  # acronyms match case-sensitively
    return re.finditer(r"(?<![\w-])" + re.escape(phrase) + r"(?![\w-])", text, flags)


def link_products(text: str, catalog: dict) -> list:
    spans, taken, mentions = sentences(text), [], []
    for phrase, target, kind, method in _phrases(catalog):
        for m in _find(text, phrase):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            mentions.append(Mention(m.group(0), m.start(), m.end(), _sentence_of(spans, m.start()), target, kind, method))
    for term in sorted(catalog.get("product_terms", []), key=len, reverse=True):
        for m in _find(text, term):
            if not any(m.start() < e and s < m.end() for s, e in taken):
                taken.append((m.start(), m.end()))
                mentions.append(Mention(m.group(0), m.start(), m.end(), _sentence_of(spans, m.start()), None, None, "unresolved"))
    return sorted(mentions, key=lambda m: m.start)


def asset_figures(text: str, definitions: dict) -> list:
    spans, figures = sentences(text), []
    words = sorted(((w, m["id"]) for m in definitions["metrics"] for w in m["words"]), key=lambda w: -len(w[0]))
    rules = [c["id"] for c in definitions["allowed_computations"]]
    for m in MONEY.finditer(text):
        s = _sentence_of(spans, m.start())
        sentence = text[s[0]:s[1]]
        metric = next((mid for w, mid in words if any(_find(sentence, w))), "unknown")
        scope = SCOPE.search(sentence[m.end() - s[0]:]) or SCOPE.search(sentence)
        figures.append(AssetFigure(m.group(0), m.start(), m.end(), s, metric,
                                   float(m.group(1)) * SCALE[m.group(2).lower()], "USD",
                                   scope.group(1).strip() if scope else "not stated", rules))
    return figures


def detect(text: str, data=DATA) -> dict:
    catalog, definitions = reference(data)
    return {"mentions": link_products(text, catalog), "assets": asset_figures(text, definitions),
            "catalog_version": catalog["catalog_version"]}


def unlinked_findings(candidates: list, mentions: list, text: str) -> dict:
    """Candidates whose product is not named in the sentence of their span: a hint for the SME, not a rejection."""
    spans, hints = sentences(text), {}
    for c in candidates:
        product = c["payload"].get("product") or c["payload"].get("target")
        start = text.find(c["payload"].get("span") or "") if c.get("span_id") is None else int(c["span_id"].split("#")[1].split("-")[0])
        if not product or start < 0 or c["kind"] in ("commitment", "commitment_status", "asset"):
            continue
        sentence = _sentence_of(spans, start)
        named = {m.target for m in mentions if m.sentence == sentence}
        if product not in named:
            hints[c["id"]] = f"{product} is not named in this sentence; check the link"
    return hints
