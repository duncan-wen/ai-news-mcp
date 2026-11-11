"""Keyword rules that add Categories to an Item beyond its Source's defaults (ADR 0002)."""

from __future__ import annotations

import html
import re

from .sources import Category

# Only the start of a summary is read: a full-text summary mentions far more than
# the Item is about (a release note lists every model it supports).
SUMMARY_LEAD = 500

_MODEL_FAMILIES = (
    "GPT|Gemini|Gemma|Claude|Fable|Opus|Sonnet|Haiku|Llama|Mistral|Mixtral|Codestral|"
    "Voxtral|Qwen|DeepSeek|Phi|Grok|GLM|Kimi|Nemotron"
)

RULES: dict[Category, tuple[str, ...]] = {
    Category.NEWS: (
        r"raises?|raised|funding|series [a-h]|valuation|ipo|acquires?|acquired|acquisitions?",
        r"mergers?|lawsuits?|sues|sued|court|regulat\w*|laws?|legislation|policy|policies",
        r"ceo|hires?|hired|appoints?|appointed|steps down|resigns?|layoffs?",
        r"partnership|partners with|teams? up|invests?|invested|investments?",
    ),
    Category.APPLICATIONS: (
        r"launch(es|ed|ing)?|rolls? out|rolling out",
        r"apps?|app store|extensions?|browser|assistants?|chatbots?|plugins?|add-ons?",
    ),
    Category.ENGINEERING: (
        r"sdks?|apis?|cli|frameworks?|library|libraries|open[- ]source|github|mcp",
        r"inference|fine-?tun\w*|benchmarks?|evals?|evaluations?",
        r"how (we|to|\w+) buil[dt]",
    ),
    Category.MODELS: (
        r"open[- ]weights?|weights|\d+(\.\d+)?[kmbt] param(eter)?s?",
        r"(new|latest|frontier|foundation|open|reasoning|language|multimodal|embedding|speech"
        r"|vision|small|smallest|largest) (ai )?models?",
    ),
}

# Read in the title only: a summary names models in passing far more often than it
# announces one.
TITLE_RULES: dict[Category, tuple[str, ...]] = {
    Category.MODELS: (
        # A family name with a version, a word or two apart at most: "Gemini 4 Carbon",
        # "Claude Fable 5.2", "Mistral Large 4", "GPT-5".
        rf"({_MODEL_FAMILIES})([\s-]+[a-z]+){{0,2}}[\s-]+v?\d+(\.\d+)?",
    ),
}


def _compile(rules: dict[Category, tuple[str, ...]]) -> dict[Category, re.Pattern[str]]:
    return {
        category: re.compile(r"\b(" + "|".join(patterns) + r")\b", re.IGNORECASE)
        for category, patterns in rules.items()
    }


_PATTERNS = _compile(RULES)
_TITLE_PATTERNS = _compile(TITLE_RULES)
_HTML_TAG = re.compile(r"<[^>]+>")


def categories_for(
    title: str, summary: str, defaults: tuple[Category, ...]
) -> tuple[Category, ...]:
    """The defaults, then every other Category a keyword rule finds in the title or summary.

    The summary's HTML tags are dropped and only its first SUMMARY_LEAD characters read.
    """
    lead = html.unescape(_HTML_TAG.sub(" ", summary))[:SUMMARY_LEAD]
    text = f"{title}\n{lead}"
    found = {category for category, pattern in _PATTERNS.items() if pattern.search(text)}
    found |= {category for category, pattern in _TITLE_PATTERNS.items() if pattern.search(title)}
    return defaults + tuple(
        category for category in Category if category in found and category not in defaults
    )
