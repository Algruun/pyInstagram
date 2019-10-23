from __future__ import annotations

from typing import Union, Set, Optional, Dict, Any

from instagram.entities.has_media_element import HasMediaElement
from instagram.entities.media import Media


class Tag(HasMediaElement):
    primary_key = "name"
    entry_data_path = ("TagPage", 0, "graphql", "hashtag")
    base_url = "explore/tags/"
    media_path = ("hashtag", "edge_hashtag_to_media")
    media_query_hash = "ded47faa9a1aaded10161a2ff32abb6b"

    def __init__(self, name: Union[Tag, str]):
        self.name: Union[Tag, str] = name
        self.media_count: Optional[int] = None

        self.media: Set[Media] = set()
        self.top_posts: Set[Media] = set()

    def set_data(self, data: Dict[str, Any]):
        self.name = data.get("name")
        self.media_count = data.get("edge_hashtag_to_media").get("count")
        for node in data.get("edge_hashtag_to_top_posts").get("edges"):
            self.top_posts.add(Media(node.get("node").get("shortcode")))
