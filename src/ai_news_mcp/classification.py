"""Keyword rules that add Categories to an Item beyond its Source's defaults (ADR 0002).

Tune them against real Items with `uv run scripts/classify_sample.py`.
"""

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
# A block tag ends a run of text, so it becomes a space; an inline tag (a link, bold) is
# dropped, so that "<a>llm</a>, " stays "llm, ".
_BLOCK_TAG = re.compile(
    r"</?(?:p|br|hr|div|li|ul|ol|dl|dt|dd|h[1-6]|blockquote|pre|table|tr|td|th|figure|"
    r"figcaption|section|article|header|footer)\b[^>]*>",
    re.IGNORECASE,
)
_ANY_TAG = re.compile(r"<[^>]+>")


def plain_text(summary: str) -> str:
    """A summary without its HTML: tags dropped, entities decoded, whitespace collapsed."""
    text = _ANY_TAG.sub("", _BLOCK_TAG.sub(" ", summary))
    return " ".join(html.unescape(text).split())


def keyword_matches(title: str, summary: str) -> dict[Category, list[str]]:
    """The keywords found in the title or summary, by the Category their rules add.

    Only the first SUMMARY_LEAD characters of the summary's plain text are read.
    """
    lead = plain_text(summary)[:SUMMARY_LEAD]
    text = f"{title}\n{lead}"
    found: dict[Category, list[str]] = {}
    for patterns, searched in ((_PATTERNS, text), (_TITLE_PATTERNS, title)):
        for category, pattern in patterns.items():
            keywords = [match.group(0) for match in pattern.finditer(searched)]
            if keywords:
                found.setdefault(category, []).extend(keywords)
    return found


def categories_for(
    title: str, summary: str, defaults: tuple[Category, ...]
) -> tuple[Category, ...]:
    """The defaults, then every other Category a keyword rule finds (see keyword_matches)."""
    found = keyword_matches(title, summary)
    return defaults + tuple(
        category for category in Category if category in found and category not in defaults
    )


# Read in the title only, and only words that are about AI on their own: not "agents"
# (FBI agents), "transformers", "diffusion", "inference" or "Grok" (to grok). A model
# family name counts only with a version (TITLE_RULES): alone, Opus is also an audio
# codec and Haiku an operating system.
AI_RULES: tuple[str, ...] = (
    r"ai|a\.i|agi|llms?|language models?|machine learning|deep learning|neural networks?",
    r"agentic|coding agents?|multi-agent|chatbots?|fine-?tun\w*",
    r"pre-?training|post-?training|open[- ]weights?|model weights|prompt injection|mcp",
    r"vibe[- ]cod\w*|text-to-(image|video|speech)",
    r"openai|anthropic|deepmind|hugging ?face|chatgpt|claude|gemini|copilot|codex",
    r"llama|qwen|deepseek|mistral|kimi",
)
_AI_PATTERN = re.compile(r"\b(" + "|".join(AI_RULES) + r")\b", re.IGNORECASE)


def is_about_ai(title: str) -> bool:
    """Whether a title is about AI: an AI keyword, or a model family name with a version."""
    return bool(_AI_PATTERN.search(title) or _TITLE_PATTERNS[Category.MODELS].search(title))
