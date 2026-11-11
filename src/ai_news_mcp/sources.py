from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal


class Category(StrEnum):
    NEWS = "News"
    APPLICATIONS = "Applications"
    ENGINEERING = "Engineering"
    MODELS = "Models"


SourceKind = Literal["rss"]


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    kind: SourceKind
    url: str
    default_categories: tuple[Category, ...]


def _rss(id: str, name: str, url: str, *default_categories: Category) -> Source:
    return Source(id=id, name=name, kind="rss", url=url, default_categories=default_categories)


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
    _rss(
        "product-hunt-ai",
        "Product Hunt: AI",
        "https://www.producthunt.com/feed?category=artificial-intelligence",
        Category.APPLICATIONS,
    ),
)
