import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import AsyncGenerator
from typing import Dict
from typing import List
from unittest.mock import MagicMock
from xml.etree import ElementTree

import aiohttp
import pydantic
import pytest
import pytest_mock

from hoyolabrssfeeds import models
from hoyolabrssfeeds.loaders import AbstractFeedFileLoader
from hoyolabrssfeeds.writers import AbstractFeedFileWriter


# ---- GENERAL FIXTURES ----


@pytest.fixture()
async def client_session() -> AsyncGenerator[aiohttp.ClientSession, Any]:
    loop = asyncio.get_running_loop()
    async with aiohttp.ClientSession(loop=loop, raise_for_status=True) as cs:
        yield cs


# ---- PATH FIXTURES ----


@pytest.fixture
def json_path(tmp_path: Path) -> Path:
    return tmp_path / Path("json_feed.json")


@pytest.fixture
def atom_path(tmp_path: Path) -> Path:
    return tmp_path / Path("atom_feed.xml")


@pytest.fixture
def config_path(tmp_path: Path) -> Path:
    return tmp_path / Path("feeds.toml")


# ---- MODEL FIXTURES ----


@pytest.fixture(
    params=[g for g in models.Game], ids=[g.name.lower() for g in models.Game]
)
def game(request: Any) -> Any:
    return request.param


@pytest.fixture(
    params=[c for c in models.FeedItemCategory],
    ids=[c.name.lower() for c in models.FeedItemCategory],
)
def category(request: Any) -> Any:
    return request.param


@pytest.fixture(params=[la for la in models.Language])
def language(request: Any) -> Any:
    return request.param


# ---- CONFIG FIXTURES ----


@pytest.fixture
def json_feed_file_writer_config(json_path: Path) -> models.FeedFileWriterConfig:
    return models.FeedFileWriterConfig(
        feed_type=models.FeedType.JSON,
        path=json_path,
        url=pydantic.parse_obj_as(pydantic.HttpUrl, "https://example.org/"),
    )


@pytest.fixture
def atom_feed_file_writer_config(atom_path: Path) -> models.FeedFileWriterConfig:
    return models.FeedFileWriterConfig(
        feed_type=models.FeedType.ATOM,
        path=atom_path,
        url=pydantic.parse_obj_as(pydantic.HttpUrl, "https://example.org/"),
    )


@pytest.fixture
def json_feed_file_config(json_path: Path) -> models.FeedFileConfig:
    return models.FeedFileConfig(feed_type=models.FeedType.JSON, path=json_path)


@pytest.fixture
def atom_feed_file_config(atom_path: Path) -> models.FeedFileConfig:
    return models.FeedFileConfig(feed_type=models.FeedType.ATOM, path=atom_path)


@pytest.fixture
def feed_config(
    feed_meta: models.FeedMeta,
    json_feed_file_writer_config: models.FeedFileWriterConfig,
    json_feed_file_config: models.FeedFileConfig,
) -> models.FeedConfig:
    return models.FeedConfig(
        feed_meta=feed_meta,
        writer_configs=[json_feed_file_writer_config],
        loader_config=json_feed_file_config,
    )


@pytest.fixture
def feed_config_no_loader(
    feed_meta: models.FeedMeta,
    json_feed_file_writer_config: models.FeedFileWriterConfig,
) -> models.FeedConfig:
    return models.FeedConfig(
        feed_meta=feed_meta,
        writer_configs=[json_feed_file_writer_config],
    )


@pytest.fixture
def toml_config_dict(
    feed_meta: models.FeedMeta,
    json_feed_file_writer_config: models.FeedFileWriterConfig,
    atom_feed_file_writer_config: models.FeedFileWriterConfig,
) -> Dict[str, Any]:
    return {
        "category_size": feed_meta.category_size,
        "language": str(feed_meta.language),
        feed_meta.game.name.lower(): {
            "feed": {
                str(models.FeedType.JSON): {
                    "path": str(json_feed_file_writer_config.path),
                    "url": str(json_feed_file_writer_config.url),
                }
            },
            "title": feed_meta.title,
            "icon": str(feed_meta.icon),
        },
        models.Game.ZENLESS.name.lower(): {
            "feed": {
                str(models.FeedType.ATOM): {
                    "path": str(atom_feed_file_writer_config.path)
                }
            },
            "categories": [models.FeedItemCategory.EVENTS.name.lower()],
        },
    }


# ---- FEED FIXTURES ----


@pytest.fixture
def feed_item() -> models.FeedItem:
    return models.FeedItem(
        id=42,
        title="Test Article",
        author="John Doe",
        content="<p>Hello World!</p>",
        summary="Hello!",
        category=models.FeedItemCategory.INFO,
        published=datetime(2022, 10, 3, 16).astimezone(),
        updated=datetime(2022, 10, 3, 18).astimezone(),
        image=pydantic.parse_obj_as(pydantic.HttpUrl, "https://example.org/"),
    )


@pytest.fixture
def feed_item_list(feed_item: models.FeedItem) -> List[models.FeedItem]:
    other_item = feed_item.copy()
    other_item.id -= 1
    return [feed_item, other_item]


@pytest.fixture
def json_feed_items(feed_item_list: List[models.FeedItem]) -> Dict[str, Any]:
    return {
        "items": [
            {
                "id": feed_item.id,
                "url": "https://example.org",
                "title": feed_item.title,
                "authors": [{"name": feed_item.author}],
                "tags": [feed_item.category.name.title()],
                "content_html": feed_item.content,
                "summary": feed_item.summary,
                "date_published": feed_item.published.astimezone().isoformat(),
                "date_modified": (
                    feed_item.updated.astimezone().isoformat()
                    if feed_item.updated
                    else ""
                ),
                "image": feed_item.image,
            }
            for feed_item in feed_item_list
        ]
    }


@pytest.fixture
def atom_feed_entries(feed_item_list: List[models.FeedItem]) -> ElementTree.Element:
    # omitting namespace declarations because they should be removed before
    root = ElementTree.Element("feed")

    for feed_item in feed_item_list:
        entry = ElementTree.SubElement(root, "entry")

        id_str = "tag:hoyolab.com,{}:{}".format(
            feed_item.published.date().isoformat(), feed_item.id
        )
        ElementTree.SubElement(entry, "id").text = id_str

        ElementTree.SubElement(entry, "title").text = feed_item.title
        ElementTree.SubElement(entry, "content").text = feed_item.content
        ElementTree.SubElement(entry, "summary").text = feed_item.summary
        ElementTree.SubElement(
            entry, "category", {"term": feed_item.category.name.title()}
        )

        author = ElementTree.SubElement(entry, "author")
        ElementTree.SubElement(author, "name").text = feed_item.author

        published_str = feed_item.published.astimezone().isoformat()
        ElementTree.SubElement(entry, "published").text = published_str

        if feed_item.updated is not None:
            updated_str = feed_item.updated.astimezone().isoformat()
            ElementTree.SubElement(entry, "updated").text = updated_str

    return root


@pytest.fixture
def feed_meta() -> models.FeedMeta:
    return models.FeedMeta(
        game=models.Game.GENSHIN,
        category_size=1,
        categories=[c for c in models.FeedItemCategory],
        language=models.Language.GERMAN,
        title="Example Feed",
        icon=pydantic.parse_obj_as(pydantic.HttpUrl, "https://example.org/"),
    )


@pytest.fixture
def category_feeds(feed_item: models.FeedItem) -> List[List[models.FeedItem]]:
    cat_feeds: List[List[models.FeedItem]] = []
    for i, cat in enumerate(models.FeedItemCategory):
        item = feed_item.copy()
        item.id += i
        item.category = cat
        cat_feeds.append([item])

    return cat_feeds


@pytest.fixture
def combined_feed(category_feeds: List[List[models.FeedItem]]) -> List[models.FeedItem]:
    comb_feed: List[models.FeedItem] = []
    for item_list in category_feeds:
        comb_feed.extend(item_list)
    comb_feed.sort(key=lambda x: x.id, reverse=True)

    return comb_feed


# ---- MOCK FIXTURES ----


@pytest.fixture
def mocked_loader(mocker: pytest_mock.MockFixture) -> MagicMock:
    loader: MagicMock = mocker.create_autospec(AbstractFeedFileLoader, instance=True)
    loader.get_feed_items = mocker.AsyncMock(return_value=[])

    return loader


@pytest.fixture
def mocked_writers(mocker: pytest_mock.MockFixture) -> List[MagicMock]:
    writer: MagicMock = mocker.create_autospec(AbstractFeedFileWriter, instance=True)
    writer.config.feed_type = models.FeedType.JSON  # needed for logger calls

    return [writer]


# ---- ASSERTION HELPERS ----

# https://docs.pytest.org/en/6.2.x/assert.html#assertion-introspection-details


def validate_hoyolab_post(post: Dict[str, Any], is_full_post: bool) -> None:
    assert type(post["post"]["post_id"]) is str
    assert re.fullmatch(r"\d+", post["post"]["post_id"]) is not None

    assert type(post["post"]["created_at"]) is int
    assert post["post"]["created_at"] > 0

    assert type(post["last_modify_time"]) is int
    assert post["last_modify_time"] >= 0

    if is_full_post:
        assert type(post["post"]["official_type"]) is int
        assert post["post"]["official_type"] in [
            c.value for c in models.FeedItemCategory
        ]

        assert type(post["user"]["nickname"]) is str
        assert len(post["user"]["nickname"]) > 0

        assert type(post["post"]["content"]) is str
        assert len(post["post"]["content"]) > 0

        assert type(post["post"]["structured_content"]) is str
        assert len(post["post"]["structured_content"]) > 0

        assert type(post["post"]["subject"]) is str
        assert len(post["post"]["subject"]) > 0

        assert type(post["cover_list"]) is list
        assert len(post["cover_list"]) >= 0

        assert type(post["post"]["desc"]) is str
        assert len(post["post"]["desc"]) >= 0
