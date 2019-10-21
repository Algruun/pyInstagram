from random import choice, randint, random
from time import sleep

import pytest
from instagram_api.entities.account import Account
from instagram_api.entities.location import Location
from instagram_api.entities.media import Media
from instagram_api.entities.tag import Tag

from tests.settings import accounts, auth, locations, photos, photo_sets, tags, videos


@pytest.fixture(scope="function")
def delay():
    if auth.get("local_delay") is not None:
        min_delay = auth.get("local_delay").get("min", 0)
        max_delay = auth.get("local_delay").get("max", 10)
        return random() * (max_delay - min_delay) + min_delay
    return 0


def setup_function():
    Account.clear_cache()
    Media.clear_cache()
    Location.clear_cache()
    Tag.clear_cache()
    if auth.get("global_delay") is not None:
        min_delay = auth.get("global_delay").get("min", 0)
        max_delay = auth.get("global_delay").get("max", 120)
        sleep(random() * (max_delay - min_delay) + min_delay)


def test_update(agent_account, settings):
    data = agent_account.update(settings=settings)

    assert data is not None
    assert agent_account.id is not None
    assert agent_account.full_name is not None
    assert agent_account.profile_pic_url is not None
    assert agent_account.profile_pic_url_hd is not None
    assert agent_account.biography is not None
    assert agent_account.follows_count is not None
    assert agent_account.followers_count is not None
    assert agent_account.media_count is not None
    assert agent_account.is_private is not None
    assert agent_account.is_verified is not None
    assert agent_account.country_block is not None


@pytest.mark.parametrize("username", accounts)
def test_update_account(agent_account, settings, username):
    account = Account(username)
    data = agent_account.update(account, settings=settings)

    assert data is not None
    assert agent_account.id is not None
    assert agent_account.full_name is not None
    assert agent_account.profile_pic_url is not None
    assert agent_account.profile_pic_url_hd is not None
    assert agent_account.biography is not None
    assert agent_account.follows_count is not None
    assert agent_account.followers_count is not None
    assert agent_account.media_count is not None
    assert agent_account.is_private is not None
    assert agent_account.is_verified is not None
    assert agent_account.country_block is not None


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_update_media(agent_account, settings, shortcode):
    media = Media(shortcode)
    data = agent_account.update(media, settings=settings)

    assert data is not None
    assert media.id is not None
    assert media.code is not None
    assert media.date is not None
    assert media.likes_count is not None
    assert media.comments_count is not None
    assert media.comments_disabled is not None
    assert media.is_video is not None
    assert media.display_url is not None
    assert media.resources is not None
    assert media.is_album is not None


@pytest.mark.parametrize("location_id", locations)
def test_update_location(agent_account, settings, location_id):
    location = Location(location_id)
    data = agent_account.update(location, settings=settings)

    assert data is not None
    assert location.id is not None
    assert location.slug is not None
    assert location.name is not None
    assert location.has_public_page is not None
    assert location.coordinates is not None
    assert location.media_count is not None


@pytest.mark.parametrize("name", tags)
def test_update_tag(agent_account, settings, name):
    tag = Tag(name)
    data = agent_account.update(tag, settings=settings)

    assert data is not None
    assert tag.name is not None
    assert tag.media_count is not None
    assert tag.top_posts is not None


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_media_account(agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent_account.get_media(
        account, count=count, delay=delay, settings=settings
    )

    assert min(account.media_count, count) == len(data)
    assert not pointer == (account.media_count <= count)


@pytest.mark.parametrize("count, location_id", [(randint(100, 500), choice(locations))])
def test_get_media_location(agent_account, delay, settings, count, location_id):
    location = Location(location_id)
    data, pointer = agent_account.get_media(
        location, count=count, delay=delay, settings=settings
    )

    assert min(location.media_count, count) == len(data)
    assert not pointer == (location.media_count <= count)


@pytest.mark.parametrize("count, name", [(randint(100, 500), choice(tags))])
def test_get_media_tag(agent_account, delay, settings, count, name):
    tag = Tag(name)
    data, pointer = agent_account.get_media(
        tag, count=count, delay=delay, settings=settings
    )

    assert min(tag.media_count, count) == len(data)
    assert not pointer == (tag.media_count <= count)


@pytest.mark.parametrize(
    "shortcode", [choice(photos), choice(photo_sets), choice(videos)]
)
def test_get_likes(agent_account, settings, shortcode):
    media = Media(shortcode)
    data, _ = agent_account.get_likes(media, settings=settings)

    assert media.likes_count >= len(data)


@pytest.mark.parametrize(
    "count, shortcode",
    [
        (randint(100, 500), shortcode)
        for shortcode in [choice(photos), choice(photo_sets), choice(videos)]
    ],
)
def test_get_comments(agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    data, pointer = agent_account.get_comments(
        media, count=count, delay=delay, settings=settings
    )

    assert min(media.comments_count, count) == len(data)
    assert not pointer == (media.comments_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_follows(agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent_account.get_follows(
        account, count=count, delay=delay, settings=settings
    )

    assert min(account.follows_count, count) == len(data)
    assert not pointer == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [(randint(100, 500), choice(accounts))])
def test_get_followers(agent_account, delay, settings, count, username):
    account = Account(username)
    data, pointer = agent_account.get_followers(
        account, count=count, delay=delay, settings=settings
    )

    assert min(account.followers_count, count) == len(data)
    assert not pointer == (account.followers_count <= count)


@pytest.mark.parametrize("count", [randint(100, 500)])
def test_get_feed(agent_account, delay, settings, count):
    data, pointer = agent_account.feed(count=count, delay=delay, settings=settings)

    assert (count > len(data)) == (not pointer)


def test_get_stories(agent_account, settings):
    agent_account.stories(settings=settings)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_media_account_pointer(agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_media(
            account, pointer=pointer, settings=settings
        )
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (account.media_count == len(data))


@pytest.mark.parametrize("count, location_id", [(randint(1, 10), choice(locations))])
def test_get_media_location_pointer(agent_account, delay, settings, count, location_id):
    location = Location(location_id)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_media(
            location, pointer=pointer, settings=settings
        )
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (location.media_count == len(data))


@pytest.mark.parametrize("count, name", [(randint(1, 10), choice(tags))])
def test_get_media_tag_pointer(agent_account, delay, settings, count, name):
    tag = Tag(name)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_media(tag, pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (tag.media_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode",
    [
        (randint(1, 10), shortcode)
        for shortcode in [choice(photos), choice(photo_sets), choice(videos)]
    ],
)
def test_get_comments_pointer(agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_comments(
            media, pointer=pointer, settings=settings
        )
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (media.comments_count == len(data))


@pytest.mark.parametrize(
    "count, shortcode", [(randint(1, 10), choice(photos + photo_sets + videos))]
)
def test_get_likes_pointer(agent_account, delay, settings, count, shortcode):
    media = Media(shortcode)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_likes(
            media, pointer=pointer, settings=settings
        )
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (media.likes_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_follows_pointer(agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_follows(
            account, pointer=pointer, settings=settings
        )
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (account.follows_count <= count)


@pytest.mark.parametrize("count, username", [(randint(1, 10), choice(accounts))])
def test_get_followers_pointer(agent_account, delay, settings, count, username):
    account = Account(username)
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.get_followers(
            account, pointer=pointer, settings=settings
        )
        sleep(delay)
        data.extend(tmp)

    assert not pointer == (account.followers_count <= count)

    assert not pointer == (account.followers_count <= count)


@pytest.mark.parametrize("count", [randint(1, 10)])
def test_get_feed_pointer(agent_account, delay, settings, count):
    pointer = None
    data = []

    for _ in range(count):
        tmp, pointer = agent_account.feed(pointer=pointer, settings=settings)
        sleep(delay)
        data.extend(tmp)


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_like_unlike_media(agent_account, delay, settings, shortcode):
    photo = Media(shortcode)

    assert agent_account.like(photo, settings=settings)
    sleep(delay)
    assert agent_account.unlike(photo, settings=settings)


@pytest.mark.parametrize("username", [choice(accounts)])
def test_follow_unfollow(agent_account, delay, settings, username):
    account = Account(username)
    agent_account.update(settings=settings)
    follows_count = agent_account.follows_count

    assert agent_account.follow(account, settings=settings)
    sleep(delay)
    agent_account.update(settings=settings)
    assert agent_account.follows_count == follows_count + 1
    assert agent_account.unfollow(account, settings=settings)
    sleep(delay)
    agent_account.update(settings=settings)
    assert agent_account.follows_count == follows_count


@pytest.mark.parametrize("shortcode", [choice(photos + photo_sets + videos)])
def test_comment(agent_account, delay, settings, shortcode):
    media = Media(shortcode)
    comment = agent_account.add_comment(media, "test", settings=settings)
    sleep(delay)

    assert agent_account.delete_comment(comment, settings=settings)
