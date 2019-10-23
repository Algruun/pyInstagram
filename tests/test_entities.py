from random import randint, choice
from string import ascii_uppercase, ascii_lowercase, digits

import pytest

from instagram.entities.account import Account
from instagram.entities.comment import Comment
from instagram.entities.location import Location
from instagram.entities.media import Media
from instagram.entities.story import Story
from instagram.entities.tag import Tag


def setup_function():
    Account.clear_cache()
    Comment.clear_cache()
    Location.clear_cache()
    Media.clear_cache()
    Story.clear_cache()
    Tag.clear_cache()


def create_id():
    return "".join(
        choice(ascii_uppercase + ascii_lowercase + digits)
        for _ in range(randint(1, 50))
    )


@pytest.mark.parametrize("account_id", [create_id() for _ in range(3)])
def test_clear_cache_account(account_id):
    account = Account(account_id)
    assert Account.cache == {account_id: account}

    Account.clear_cache()
    assert Account.cache == dict()


@pytest.mark.parametrize("media_id", [create_id() for _ in range(3)])
def test_clear_cache_media(media_id):
    media = Media(media_id)
    assert Media.cache == {media_id: media}

    Media.clear_cache()
    assert Media.cache == dict()


@pytest.mark.parametrize("location_id", [create_id() for _ in range(3)])
def test_clear_cache_location(location_id):
    location = Location(location_id)
    assert Location.cache == {location_id: location}

    Location.clear_cache()
    assert Location.cache == dict()


@pytest.mark.parametrize("tag_id", [create_id() for _ in range(3)])
def test_clear_cache_tag(tag_id):
    tag = Tag(tag_id)
    assert Tag.cache == {tag_id: tag}

    Tag.clear_cache()
    assert Tag.cache == dict()


@pytest.mark.parametrize("comment_id", [create_id() for _ in range(3)])
def test_clear_cache_comment(comment_id):
    account = Account("test")
    media = Media("test")
    comment = Comment(comment_id, media=media, owner=account, text="test", created_at=0)
    assert Comment.cache == {comment_id: comment}

    Comment.clear_cache()
    assert Comment.cache == dict()
    assert Media.cache == {"test": media}
    assert Account.cache == {"test": account}


@pytest.mark.parametrize("story_id", [create_id() for _ in range(3)])
def test_clear_cache_story(story_id):
    story = Story(story_id)
    assert Story.cache == {story_id: story}

    Story.clear_cache()
    assert Story.cache == dict()
