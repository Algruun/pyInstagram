from __future__ import annotations

from typing import Union, Set, Dict, Any, Optional, List

from instagram.entities.account import Account
from instagram.entities.updatable_element import UpdatableElement


class Media(UpdatableElement):
    primary_key = "code"
    entry_data_path = ("PostPage", 0, "graphql", "shortcode_media")
    base_url = "p/"

    def __init__(self, code: Union[Media, str]):
        self.id: Optional[str] = None
        self.code: Union[Media, str] = code
        self.caption = None
        self.owner: Optional[Account] = None
        self.date = None
        from instagram.entities.location import Location

        self.location: Optional[Location] = None
        self.likes_count = None
        self.comments_count = None
        self.comments_disabled = None
        self.is_video = None
        self.video_url = None
        self.is_ad = None
        self.display_url = None
        self.resources: Optional[List[str]] = None
        self.is_album: Optional[bool] = None

        self.album: Set[Media] = set()
        self.likes: Set[Account] = set()
        from instagram.entities.comment import Comment

        self.comments: Set[Comment] = set()

    def set_data(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.code = data.get("shortcode")
        if data.get("edge_media_to_caption").get("edges"):
            self.caption = (
                data.get("edge_media_to_caption")
                .get("edges")[0]
                .get("node")
                .get("text")
            )
        else:
            self.caption = None
        if "username" in data.get("owner"):
            self.owner = Account(data.get("owner").get("username"))
        self.date = data.get("taken_at_timestamp")
        if "location" in data and data.get("location") and "id" in data.get("location"):
            from instagram_api.entities.location import Location

            self.location = Location(data.get("location").get("id"))
        self.likes_count = data.get("edge_media_preview_like").get("count")
        if "edge_media_to_comment" in data:
            self.comments_count = data.get("edge_media_to_comment").get("count")
        else:
            self.comments_count = data.get("edge_media_to_parent_comment").get("count")
        self.comments_disabled = data.get("comments_disabled")
        self.is_video = data.get("is_video")
        if self.is_video and "video_url" in data:
            self.video_url = data.get("video_url")
        if "is_ad" in data:
            self.is_ad = data.get("is_ad")
        self.display_url = data.get("display_url")
        if "display_resources" in data:
            self.resources = [
                resource.get("src") for resource in data.get("display_resources")
            ]
        else:
            self.resources = [
                resource.get("src") for resource in data.get("thumbnail_resources")
            ]
        self.album = set()
        self.is_album = data.get("__typename") == "GraphSidecar"
        if "edge_sidecar_to_children" in data:
            for edge in data.get("edge_sidecar_to_children").get("edges"):
                if edge.get("node").get("shortcode", self.code) != self.code:
                    self.album.add(Media(edge.get("node").get("shortcode")))
