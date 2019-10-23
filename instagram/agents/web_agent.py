import hashlib
import json
import re
from time import sleep
from typing import Optional, List, Tuple, Dict, Any, Callable

from loguru import logger
from requests import Response, Session, RequestException
from requests.cookies import cookiejar_from_dict

from instagram.entities import (
    Account,
    Comment,
    HasMediaElement,
    UpdatableElement,
    Media,
    Tag,
)
from instagram.exceptions import ExceptionManager, UnexpectedResponse, InternetException

exception_manager = ExceptionManager()


class WebAgent:
    def __init__(
        self,
        cookies: Dict[str, Any] = None,
        proxies: Dict[str, str] = None,
        json_deserializer: Callable[[Any], Dict[Any, Any]] = json.loads,
    ):
        # super(WebAgent, self).__init__(cookies)
        self.rhx_gis = None
        self.csrf_token = None
        self.session = Session()
        self.deserializer = json_deserializer
        if cookies:
            self.session.cookies = cookiejar_from_dict(cookies)
        if proxies:
            self.session.proxies.update(proxies)

    @exception_manager.decorator
    def update(
        self, obj: UpdatableElement = None, settings: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        logger.info(f"Update '{'self' if not obj else obj}' started")
        settings = dict() if not settings else settings.copy()

        query = "https://www.instagram.com/"
        if obj:
            query += f"{obj.base_url}{getattr(obj, obj.primary_key)}"

        response = self.get_request(query, **settings)

        try:
            match = re.search(
                r"<script[^>]*>\s*window._sharedData\s*=\s*((?!<script>).*)\s*;\s*</script>",
                response.text,
            )
            data = self.deserializer(match.group(1))
            self.rhx_gis = data.get("rhx_gis", "")
            self.csrf_token = data.get("config").get("csrf_token")

            if not obj:
                return

            data = data.get("entry_data")
            for key in obj.entry_data_path:
                data = data[key]
            obj.set_data(data)

            logger.info(f"Update '{'self' if not obj else obj}' was successful")
            return data
        except (AttributeError, KeyError, ValueError) as exception:
            logger.error(
                f"Update '{'self' if not obj else obj}' was unsuccessful: {str(exception)}"
            )
            # raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_media(
        self,
        obj: HasMediaElement,
        pointer: str = None,
        count: int = 12,
        limit: int = 50,
        delay: int = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Media], str, bool]:
        logger.info(f"Get media '{obj}' started")

        variables_string = (
            '{{"{name}":"{name_value}","first":{first},"after":"{after}"}}'
        )
        medias = []

        if not pointer:
            try:
                data = self.update(obj, settings=settings)
                data = data.get(obj.media_path[-1])

                edges, page_info, pointer = self.proceed_media_elements(
                    data=data, count=count, obj=obj, medias=medias
                )

                if len(edges) < count and page_info.get("has_next_page"):
                    count = count - len(edges), False
                else:
                    logger.info(f"Get media '{obj}' was successful")
                    return medias, pointer, True
            except (ValueError, KeyError) as exception:
                logger.error(f"Get media '{obj}' was unsuccessful: {str(exception)}")
                raise UnexpectedResponse(
                    exception,
                    "https://www.instagram.com/"
                    + obj.base_url
                    + getattr(obj, obj.primary_key),
                )

        # while True:
        data = {"after": pointer, "first": min(limit, count)}
        if isinstance(obj, Tag):
            data.update({"name": "tag_name"})
            data.update({"name_value": obj.name})
        else:
            data.update({"name": "id"})
            data.update({"name_value": obj.id})

        response = self.graphql_request(
            query_hash=obj.media_query_hash,
            variables=variables_string.format(**data),
            referer="https://instagram.com/"
            + obj.base_url
            + getattr(obj, obj.primary_key),
            settings=settings,
        )

        try:
            data = response.json().get("data")
            for key in obj.media_path:
                data = data.get(key)

            edges, page_info, pointer = self.proceed_media_elements(
                data=data, count=count, obj=obj, medias=medias
            )
            if len(edges) < count and page_info.get("has_next_page"):
                count = count - len(edges)
                sleep(delay)
                return medias, pointer, False
            else:
                logger.info(f"Get media '{obj}' was successful")
                return medias, pointer, True
        except (ValueError, KeyError) as exception:
            logger.error(f"Get media '{obj}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_likes(
        self,
        media: Media,
        pointer: str = None,
        count: int = 20,
        limit: int = 50,
        delay: int = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Account], str, bool]:
        logger.info(f"Get likes '{media}' started")

        if not media.id:
            self.update(media, settings=settings)

        if pointer:
            variables_string = (
                '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
            )
        else:
            variables_string = '{{"shortcode":"{shortcode}","first":{first}}}'
        likes = []

        # while True:
        data = {"shortcode": media.code, "first": min(limit, count)}
        if pointer:
            data.update({"after": pointer})

        response = self.graphql_request(
            query_hash="1cb6ec562846122743b61e492c85999f",
            variables=variables_string.format(**data),
            referer="https://instagram.com/%s%s"
            % (media.base_url, getattr(media, media.primary_key)),
            settings=settings,
        )

        try:
            data = (
                response.json().get("data").get("shortcode_media").get("edge_liked_by")
            )
            edges: dict = data.get("edges")
            page_info: dict = data.get("page_info")
            media.likes_count = data.get("count")

            for index in range(min(len(edges), count)):
                node = edges[index].get("node")
                account = Account(node.get("username"))
                account.id = node.get("id")
                account.profile_pic_url = node.get("profile_pic_url")
                account.is_verified = node.get("is_verified")
                account.full_name = node.get("full_name")
                media.likes.add(account)
                likes.append(account)

            pointer = (
                page_info.get("end_cursor") if page_info.get("has_next_page") else None
            )

            if len(edges) < count and page_info.get("has_next_page"):
                count = count - len(edges)
                variables_string = (
                    '{{"shortcode":"{shortcode}","first":{first},"after":"{after}"}}'
                )
                sleep(delay)
                return likes, pointer, False
            else:
                logger.info(f"Get likes '{media}' was successful")
                return likes, pointer, True
        except (ValueError, KeyError) as exception:
            logger.error(f"Get likes '{media}' was unsuccessful: {str(exception)}")
            raise UnexpectedResponse(exception, response.url)

    @exception_manager.decorator
    def get_comments(
        self,
        media: Media,
        pointer: str = None,
        count: int = 35,
        limit: int = 32,
        delay: int = 0,
        settings: Dict[str, Any] = None,
    ) -> Tuple[List[Comment], str]:
        logger.info(f"Get comments '{media}' started")

        comments = []

        if not pointer:
            try:
                data = self.update(media, settings=settings)
                if "edge_media_to_comment" in data:
                    data = data.get("edge_media_to_comment")
                else:
                    data = data.get("edge_media_to_parent_comment")

                edges, page_info, pointer = self.proceed_comments(
                    data=data, count=count, comments=comments, media=media
                )
                if len(edges) < count and pointer:
                    count = count - len(edges)
                else:
                    logger.info(f"Get comments '{media}' was successful")
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                logger.error(
                    f"Get comments '{media}' was unsuccessful: {str(exception)}"
                )
                raise UnexpectedResponse(exception, media)

        variables_string = '{{"shortcode":"{code}","first":{first},"after":"{after}"}}'
        while True:
            data = {"after": pointer, "code": media.code, "first": min(limit, count)}

            response = self.graphql_request(
                query_hash="f0986789a5c5d17c2400faebf16efd0d",
                variables=variables_string.format(**data),
                referer="https://instagram.com/%s%s"
                % (media.base_url, getattr(media, media.primary_key)),
                settings=settings,
            )

            try:
                data = (
                    response.json()
                    .get("data")
                    .get("shortcode_media")
                    .get("edge_media_to_comment")
                )
                media.comments_count = data.get("count")
                edges, page_info, pointer = self.proceed_comments(
                    data=data, count=count, comments=comments, media=media
                )

                if len(edges) < count and page_info.get("has_next_page"):
                    count = count - len(edges)
                    sleep(delay)
                else:
                    logger.info(f"Get comments '{media}' was successful")
                    return comments, pointer
            except (ValueError, KeyError) as exception:
                logger.error(
                    f"Get comments '{media}' was unsuccessful: {str(exception)}"
                )
                raise UnexpectedResponse(exception, response.url)

    def graphql_request(
        self, query_hash: str, variables: str, referer: str, settings: str = None
    ) -> Response:
        settings = dict() if not settings else settings.copy()

        if "params" not in settings:
            settings.update({"params": dict()})
        settings.get("params").update({"query_hash": query_hash})

        settings.get("params").update({"variables": variables})
        gis = f"{self.rhx_gis}:{variables}"
        if "headers" not in settings:
            settings.update({"headers": dict()})
            settings["headers"] = dict()
        settings.get("headers").update(
            {
                # "X-IG-App-ID": "936619743392459",
                "X-Instagram-GIS": hashlib.md5(gis.encode("utf-8")).hexdigest(),
                "X-Requested-With": "XMLHttpRequest",
                "Referer": referer,
            }
        )

        return self.get_request("https://www.instagram.com/graphql/query/", **settings)

    def action_request(
        self,
        referer: str,
        url: str,
        data: Dict[str, Any] = None,
        settings: Dict[str, Any] = None,
    ) -> Response:
        data = dict() if not data else data.copy()
        settings = dict() if not settings else settings.copy()

        headers = {
            "Referer": referer,
            "X-CSRFToken": self.csrf_token,
            "X-Instagram-Ajax": "1",
            "X-Requested-With": "XMLHttpRequest",
        }
        if "headers" in settings:
            settings.get("headers").update(headers)
        else:
            settings.update({"headers": headers})
        if "data" in settings:
            settings.get("data").update(data)
        else:
            settings.update({"data": data})

        return self.post_request(url, **settings)

    def get_request(self, *args, **kwargs) -> Response:
        try:
            response = self.session.get(*args, **kwargs)
            response.raise_for_status()
            return response
        except (RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)

    def post_request(self, *args, **kwargs) -> Response:
        try:
            response = self.session.post(*args, **kwargs)
            response.raise_for_status()
            return response
        except (RequestException, ConnectionResetError) as exception:
            raise InternetException(exception)

    @staticmethod
    def proceed_media_elements(
        data: Dict[str, Any], count: int, obj: HasMediaElement, medias: List[Media]
    ) -> Tuple[Dict[Any, Any], Dict[Any, Any], Optional[str]]:
        page_info: Dict[str, Any] = data.get("page_info")
        edges: Dict[Any, Any] = data.get("edges")

        for index in range(min(len(edges), count)):
            node = edges[index].get("node")
            m = Media(node.get("shortcode"))
            m.set_data(node)
            if isinstance(obj, Account):
                m.likes_count = node.get("edge_media_preview_like").get("count")
                m.owner = obj
            else:
                m.likes_count = node.get("edge_liked_by")

            obj.media.add(m)
            medias.append(m)

        pointer = (
            page_info.get("end_cursor") if page_info.get("has_next_page") else None
        )
        return edges, page_info, pointer

    @staticmethod
    def proceed_comments(
        data: Dict[str, Any], count: int, comments: List[Comment], media: Media
    ) -> Tuple[Dict[Any, Any], Dict[Any, Any], Optional[str]]:
        edges = data.get("edges")
        page_info = data.get("page_info")

        for index in range(min(len(edges), count)):
            node = edges[index].get("node")
            c = Comment(
                node.get("id"),
                media=media,
                owner=Account(node.get("owner").get("username")),
                text=node.get("text"),
                created_at=node.get("created_at"),
            )
            media.comments.add(c)
            comments.append(c)

        pointer = (
            page_info.get("end_cursor") if page_info.get("has_next_page") else None
        )
        return edges, page_info, pointer
