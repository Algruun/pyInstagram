import json
import re
from time import sleep
from typing import List, Tuple, Union, Optional, Dict, Any

from loguru import logger

from instagram import WebAgent
from instagram.entities import (
    Account,
    UpdatableElement,
    HasMediaElement,
    Media,
    Story,
    Comment,
)
from instagram.exceptions import (
    ExceptionManager,
    InternetException,
    AuthException,
    CheckpointException,
    UnexpectedResponse,
)

exception_manager = ExceptionManager()


class WebAgentAccount(Account, WebAgent):
    @exception_manager.decorator
    def __init__(
        self, username: str, cookies: dict = None, proxies: Dict[str, str] = None
    ):
        # super().__init__(username, cookies)

        Account.__init__(self, username)
        WebAgent.__init__(self, cookies=cookies, proxies=proxies)

    @exception_manager.decorator
    def auth(self, password: str, settings: Dict[str, Any] = None):
        logger.info("Auth started")
        settings = dict() if not settings else settings.copy()

        self.update(settings=settings)

        if "headers" not in settings:
            settings.update({"headers": {}})
        settings.get("headers").update(
            {
                "X-IG-App-ID": "936619743392459",
                # "X_Instagram-AJAX": "ee72defd9231",
                "X-CSRFToken": self.csrf_token,
                "Referer": "https://www.instagram.com/",
            }
        )
        if "data" not in settings:
            settings.update({"data": {}})
        settings.get("data").update({"username": self.username, "password": password})

        try:
            response = self.post_request(
                "https://www.instagram.com/accounts/login/ajax/", **settings
            )
        except InternetException as exception:
            response = exception.response

        try:
            data = response.json()
            if data.get("authenticated") is False:
                raise AuthException(self.username)
            elif data.get("message") == "checkpoint_required":
                checkpoint_url = "https://instagram.com" + data.get("checkpoint_url")
                data = self.checkpoint_handle(url=checkpoint_url, settings=settings)
                raise CheckpointException(
                    username=self.username,
                    checkpoint_url=checkpoint_url,
                    navigation=data.get("navigation"),
                    types=data.get("types"),
                )
        except (ValueError, KeyError) as exception:
            logger.error(f"Auth was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)
        logger.info("Auth was successful")

    @exception_manager.decorator
    def checkpoint_handle(
        self, url: str, settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        logger.info(f"Handle checkpoint page for '{self.username}' started")
        response = self.get_request(url, **settings)
        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = json.loads(match.group(1))
            data = data.get("entry_data").get("Challenge")[0]

            navigation = {
                key: "https://instagram.com" + value
                for key, value in data.get("navigation").items()
            }

            data = data.get("extraData").get("content")
            data = list(
                filter(
                    lambda item: item.get("__typename") == "GraphChallengePageForm",
                    data,
                )
            )
            data = data[0].get("fields")[0].get("values")
            types = []
            for d in data:
                types.append(
                    {
                        "label": d.get("label").lower().split(":")[0],
                        "value": d.get("value"),
                    }
                )
            logger.info(f"Handle checkpoint page for '{self.username}' was successful")
            return {"navigation": navigation, "types": types}
        except (AttributeError, KeyError, ValueError) as exception:
            logger.error(
                f"Handle checkpoint page for '{self.username}' was unsuccessful: {str(exception)}"
            )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def checkpoint_send(
        self,
        checkpoint_url: str,
        forward_url: str,
        choice,
        settings: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        logger.info(f"Send verify code for '{self.username}' started")
        response = self.action_request(
            referer=checkpoint_url,
            url=forward_url,
            data={"choice": choice},
            settings=settings,
        )

        try:
            navigation = response.json().get("navigation")
            logger.info(f"Send verify code for '{self.username}' was successful")
            return {
                key: "https://instagram.com" + value
                for key, value in navigation.items()
            }
        except (ValueError, KeyError) as exception:
            logger.error(
                f"Send verify code by {type} to '{self.username}' was unsuccessful: {str(exception)}"
            )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def checkpoint_replay(
        self, forward_url: str, replay_url: str, settings: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        logger.info(f"Resend verify code for '{self.username}' started")
        response = self.action_request(
            url=replay_url, referer=forward_url, settings=settings
        )
        try:
            navigation = response.json().get("navigation")
            logger.info(f"Resend verify code for '{self.username}' was successful")
            return {
                key: "https://instagram.com" + value
                for key, value in navigation.items()
            }
        except (AttributeError, KeyError, ValueError) as exception:
            logger.error(
                f"Resend verify code for '{self.username}' was unsuccessful: {str(exception)}"
            )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def checkpoint(self, url: str, code, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Verify account '{self.username}' started")
        response = self.action_request(
            referer=url, url=url, data={"security_code": code}, settings=settings
        )

        try:
            result = response.json().get("status") == "ok"
            logger.info(f"Verify account '{self.username}' was successful")
            return result
        except (AttributeError, KeyError, ValueError) as exception:
            logger.error(
                f"Verify account '{self.username}' was unsuccessful: {str(exception)}"
            )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def update(self, obj: UpdatableElement = None, settings: Dict[str, Any] = None):
        if not obj:
            obj = self
        return WebAgent.update(self, obj, settings=settings)

    @exception_manager.decorator
    def get_media(
        self,
        obj: HasMediaElement = None,
        pointer: str = None,
        count: int = 12,
        limit: int = 12,
        delay: int = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Media], str, bool]:
        if not obj:
            obj = self
        return WebAgent.get_media(
            self,
            obj,
            pointer=pointer,
            count=count,
            limit=limit,
            delay=delay,
            settings=settings,
        )

    @exception_manager.decorator
    def get_follows(
        self,
        account: Account = None,
        pointer: str = None,
        count: int = 20,
        limit: int = 50,
        delay: int = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Account], str, bool]:
        if not account:
            account = self
        logger.info(f"Get '{account}' follows started")

        if not account.id:
            self.update(account, settings=settings)

        if not pointer:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        follows = []

        # while True:
        data = {"first": min(limit, count), "id": account.id}
        if pointer:
            data.update({"after": pointer})

        response = self.graphql_request(
            query_hash="58712303d941c6855d4e888c5f0cd22f",
            variables=variables_string.format(**data),
            referer="https://instagram.com/%s%s"
            % (account.base_url, getattr(account, account.primary_key)),
            settings=settings,
        )

        try:
            data = response.json().get("data").get("user").get("edge_follow")
            edges = data.get("edges")
            page_info = data.get("page_info")
            account.follows_count = data.get("count")

            for index in range(min(len(edges), count)):
                node = edges[index].get("node")
                a = Account(node.get("username"))
                a.id = node.get("id")
                a.profile_pic_url = node.get("profile_pic_url")
                a.is_verified = node.get("is_verified")
                a.full_name = node.get("full_name")
                account.follows.add(a)
                follows.append(a)

            pointer = (
                page_info.get("end_cursor") if page_info.get("has_next_page") else None
            )

            if len(edges) < count and page_info.get("has_next_page"):
                count = count - len(edges)
                variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                # sleep(delay)
                return follows, pointer, False
            else:
                logger.info(f"Get '{account}' follows was successful")
                return follows, pointer, True
        except (ValueError, KeyError) as exception:
            logger.error(f"Get '{account}' follows was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_followers(
        self,
        account: Account = None,
        pointer: str = None,
        count: int = 20,
        limit: int = 50,
        delay: int = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Account], str, bool]:
        if not account:
            account = self
        logger.info(f"Get '{account}' followers started")

        if not account.id:
            self.update(account, settings=settings)

        if not pointer:
            variables_string = '{{"id":"{id}","first":{first}}}'
        else:
            variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
        followers = []

        # while True:
        data = {"first": min(limit, count), "id": account.id}
        if pointer:
            data.update({"after": pointer})

        response = self.graphql_request(
            query_hash="37479f2b8209594dde7facb0d904896a",
            variables=variables_string.format(**data),
            referer="https://instagram.com/%s%s"
            % (account.base_url, getattr(account, account.primary_key)),
            settings=settings,
        )

        try:
            data = response.json().get("data").get("user").get("edge_followed_by")
            edges = data.get("edges")
            page_info = data.get("page_info")
            account.followers_count = data.get("count")

            for index in range(min(len(edges), count)):
                node = edges[index].get("node")
                a = Account(node.get("username"))
                a.id = node.get("id")
                a.profile_pic_url = node.get("profile_pic_url")
                a.is_verified = node.get("is_verified")
                a.full_name = node.get("full_name")
                account.followers.add(a)
                followers.append(a)

            pointer = (
                page_info.get("end_cursor") if page_info.get("has_next_page") else None
            )

            if len(edges) < count and page_info.get("has_next_page"):
                count = count - len(edges)
                variables_string = '{{"id":"{id}","first":{first},"after":"{after}"}}'
                # sleep(delay)
                return followers, pointer, False
            else:
                logger.info(f"Get '{account}' followers was successful")
                return followers, pointer, True
        except (ValueError, KeyError) as exception:
            logger.error(
                f"Get '{account}' followers was unsuccessful: {str(exception)}"
            )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def stories(self, settings: Dict[str, Any] = None) -> List[Story]:
        logger.info("Get stories started")
        response = self.graphql_request(
            query_hash="60b755363b5c230111347a7a4e242001",
            variables='{"only_stories":true}',
            referer="https://instagram.com/%s%s"
            % (self.base_url, getattr(self, self.primary_key)),
            settings=settings,
        )

        try:
            data = (
                response.json()
                .get("data")
                .get("user")
                .get("feed_reels_tray")
                .get("edge_reels_tray_to_reel")
            )
            logger.info("Get stories was successful")
            return [Story(edge.get("node").get("id")) for edge in data.get("edges")]
        except (ValueError, KeyError) as exception:
            logger.error(f"Get stories was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def feed(
        self,
        pointer: str = None,
        count: int = 12,
        limit: int = 50,
        delay: Union[int, float] = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Media], str]:
        logger.info("Get feed started")

        variables_string = '{{"fetch_media_item_count":{first},"fetch_media_item_cursor":"{after}",\
            "fetch_comment_count":4,"fetch_like":10,"has_stories":false}}'
        feed = []

        while True:
            response = self.graphql_request(
                query_hash="485c25657308f08317c1e4b967356828",
                variables=variables_string.format(
                    after=pointer, first=min(limit, count)
                )
                if pointer
                else "{}",
                referer="https://instagram.com/%s%s"
                % (self.base_url, getattr(self, self.primary_key)),
                settings=settings,
            )

            try:
                data = (
                    response.json()
                    .get("data")
                    .get("user")
                    .get("edge_web_feed_timeline")
                )
                edges = data.get("edges")
                page_info = data.get("page_info")
                length = len(edges)

                for index in range(min(length, count)):
                    node = edges[index].get("node")
                    if "shortcode" not in node:
                        length -= 1
                        continue
                    m = Media(node.get("shortcode"))
                    m.set_data(node)
                    feed.append(m)

                pointer = (
                    page_info.get("end_cursor")
                    if page_info.get("has_next_page")
                    else None
                )

                if length < count and page_info.get("has_next_page"):
                    count -= length
                    sleep(delay)
                else:
                    logger.info("Get feed was successful")
                    return feed, pointer
            except (ValueError, KeyError) as exception:
                logger.error(f"Get feed was unsuccessful: {str(exception)}")
                raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def like(self, media: Media, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Like '{media}' started")
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if not media.id:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/like/" % media.id,
            settings=settings,
        )

        try:
            logger.info(f"Like '{media}' was successful")
            return response.json().get("status") == "ok"
        except (ValueError, KeyError) as exception:
            logger.error(f"Like '{media}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unlike(self, media: Media, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Unlike '{media}' started")
        if not isinstance(media, Media):
            raise TypeError("'media' must be Media type")

        if not media.id:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/likes/%s/unlike/" % media.id,
            settings=settings,
        )

        try:
            result = response.json().get("status") == "ok"
            logger.info(f"Like '{media}' was successful", media)
            return result
        except (ValueError, KeyError) as exception:
            logger.error(f"Like '{media}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def save(self, media: Media, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Save '{media}' started")

        if not media.id:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/save/%s/save/" % media.id,
            settings=settings,
        )

        try:
            logger.info(f"Save '{media}' was successful", media)
            return response.json().get("status") == "ok"
        except (ValueError, KeyError) as exception:
            logger.error(f"Save '{media}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unsave(self, media: Media, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Unsave '{media}' started")

        if not media.id:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/save/%s/unsave/" % media.id,
            settings=settings,
        )

        try:
            result = response.json().get("status") == "ok"
            logger.info(f"Unsave '{media}' was successful", media)
            return result
        except (ValueError, KeyError) as exception:
            logger.error(f"Unsave '{media}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def add_comment(
        self, media: Media, text: str, settings: Dict[str, Any] = None
    ) -> Optional[Comment]:
        logger.info(f"Comment '{media}' started")

        if not media.id:
            self.update(media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % media.code,
            url="https://www.instagram.com/web/comments/%s/add/" % media.id,
            data={"comment_text": text},
            settings=settings,
        )

        try:
            data = response.json()
            if data.get("status") == "ok":
                comment = Comment(
                    data.get("id"),
                    media=media,
                    owner=self,
                    text=data.get("text"),
                    created_at=data.get("created_time"),
                )
            else:
                comment = None
            logger.info(f"Comment '{media}' was successful")
            return comment
        except (ValueError, KeyError) as exception:
            logger.error(f"Comment '{media}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def delete_comment(self, comment: Comment, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Delete comment '{comment}' started")

        if not comment.media.id:
            self.update(comment.media, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/p/%s/" % comment.media.code,
            url="https://www.instagram.com/web/comments/%s/delete/%s/"
            % (comment.media.id, comment.id),
            settings=settings,
        )

        try:
            result = response.json().get("status") == "ok"
            if result:
                del comment
            logger.info(f"Delete comment '{comment}' was successful")
            return result
        except (ValueError, KeyError) as exception:
            logger.error(
                f"Delete comment '{comment}' was unsuccessful: {str(exception)}"
            )
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def follow(self, account: Account, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Follow to '{account}' started", account)

        if not account.id:
            self.update(account, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/%s" % account.username,
            url="https://www.instagram.com/web/friendships/%s/follow/" % account.id,
            settings=settings,
        )

        try:
            result = response.json().get("status") == "ok"
            logger.info(f"Follow to '{account}' was successful")
            return result
        except (ValueError, KeyError) as exception:
            logger.error(f"Follow to '{account}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def unfollow(self, account: Account, settings: Dict[str, Any] = None) -> bool:
        logger.info(f"Unfollow to '{account}' started")

        if not account.id:
            self.update(account, settings=settings)

        response = self.action_request(
            referer="https://www.instagram.com/%s" % account.username,
            url="https://www.instagram.com/web/friendships/%s/unfollow/" % account.id,
            settings=settings,
        )

        try:
            result = response.json().get("status") == "ok"
            logger.info(f"Unfollow to '{account}' was successful")
            return result
        except (ValueError, KeyError) as exception:
            logger.error(f"Unfollow to '{account}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)
