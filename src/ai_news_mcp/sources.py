from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from urllib.parse import urlencode


class Category(StrEnum):
    NEWS = "News"
    APPLICATIONS = "Applications"
    ENGINEERING = "Engineering"
    MODELS = "Models"


SourceKind = Literal["rss", "anthropic-sitemap", "hn-algolia"]
"""How a Source's response is read. An `anthropic-sitemap` Source collects only the URLs
its sitemap did not list before (see Store.newly_listed)."""


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    kind: SourceKind
    url: str
    default_categories: tuple[Category, ...]


def _rss(id: str, name: str, url: str, *default_categories: Category) -> Source:
    return Source(id=id, name=name, kind="rss", url=url, default_categories=default_categories)


HACKER_NEWS_MIN_POINTS = 100

# The most recent stories at HACKER_NEWS_MIN_POINTS or more, about 12 days of them: a story
# that reaches the threshold days after it was posted is still in the next collection.
HACKER_NEWS_URL = "https://hn.algolia.com/api/v1/search_by_date?" + urlencode(
    {
        "tags": "story",
        "numericFilters": f"points>={HACKER_NEWS_MIN_POINTS}",
        "hitsPerPage": 500,
        "attributesToRetrieve": "title,url,points,created_at,story_text",
        "attributesToHighlight": "none",
    }
)

# The first version's Sources; URLs and quirks: docs/research/ai-news-sources.md.
DEFAULT_SOURCES: tuple[Source, ...] = (
    _rss("openai-news", "OpenAI News", "https://openai.com/news/rss.xml", Category.NEWS),
    _rss(
        "google-deepmind",
        "Google DeepMind Blog",
        "https://deepmind.google/blog/rss.xml",
        Category.NEWS,
    ),
    _rss(
        "google-ai",
        "Google AI (The Keyword)",
        "https://blog.google/innovation-and-ai/technology/ai/rss/",
        Category.NEWS,
    ),
    # No RSS: its sitemap's /news/ URLs (not /research/) give the Items.
    Source(
        id="anthropic-news",
        name="Anthropic News",
        kind="anthropic-sitemap",
        url="https://www.anthropic.com/sitemap.xml",
        default_categories=(Category.NEWS,),
    ),
    # Served as text/plain: the adapter must not go by the content type.
    _rss("mistral-news", "Mistral News", "https://mistral.ai/news/rss", Category.NEWS),
    _rss(
        "microsoft-ai",
        "Microsoft Source: AI",
        "https://news.microsoft.com/source/topics/ai/feed/",
        Category.NEWS,
    ),
    _rss(
        "techcrunch-ai",
        "TechCrunch AI",
        "https://techcrunch.com/category/artificial-intelligence/feed/",
        Category.NEWS,
    ),
    _rss(
        "the-verge-ai",
        "The Verge AI",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        Category.NEWS,
    ),
    _rss(
        "mit-technology-review-ai",
        "MIT Technology Review AI",
        "https://www.technologyreview.com/topic/artificial-intelligence/feed",
        Category.NEWS,
    ),
    _rss(
        "simon-willison",
        "Simon Willison",
        "https://simonwillison.net/atom/everything/",
        Category.ENGINEERING,
    ),
    _rss("latent-space", "Latent Space", "https://www.latent.space/feed", Category.ENGINEERING),
    _rss(
        "langchain-blog",
        "LangChain Blog",
        "https://www.langchain.com/blog/rss.xml",
        Category.ENGINEERING,
    ),
    _rss("vercel-blog", "Vercel Blog", "https://vercel.com/atom", Category.ENGINEERING),
    _rss(
        "cloudflare-blog",
        "Cloudflare Blog",
        "https://blog.cloudflare.com/rss/",
        Category.ENGINEERING,
    ),
    _rss(
        "hugging-face-blog",
        "Hugging Face Blog",
        "https://huggingface.co/blog/feed.xml",
        Category.ENGINEERING,
    ),
    _rss("nvidia-blog", "NVIDIA Blog", "https://blogs.nvidia.com/feed/", Category.ENGINEERING),
    _rss(
        "aws-machine-learning",
        "AWS Machine Learning Blog",
        "https://aws.amazon.com/blogs/machine-learning/feed/",
        Category.ENGINEERING,
    ),
    _rss(
        "vllm-releases",
        "vLLM releases",
        "https://github.com/vllm-project/vllm/releases.atom",
        Category.ENGINEERING,
    ),
    _rss(
        "transformers-releases",
        "Transformers releases",
        "https://github.com/huggingface/transformers/releases.atom",
        Category.ENGINEERING,
    ),
    # Only the stories whose title is about AI (classification.is_about_ai).
    Source(
        id="hacker-news-ai",
        name="Hacker News: AI",
        kind="hn-algolia",
        url=HACKER_NEWS_URL,
        default_categories=(Category.APPLICATIONS,),
    ),
    _rss(
        "product-hunt-ai",
        "Product Hunt: AI",
        "https://www.producthunt.com/feed?category=artificial-intelligence",
        Category.APPLICATIONS,
    ),
)
