from __future__ import annotations

from typing import Union, Set, Tuple, Optional, Dict, Any

from instagram.entities.has_media_element import HasMediaElement
from instagram.entities.media import Media


class Location(HasMediaElement):
    primary_key = "id"
    entry_data_path = ("LocationsPage", 0, "graphql", "location")
    base_url = "explore/locations/"
    media_path = ("location", "edge_location_to_media")
    media_query_hash = "ac38b90f0f3981c42092016a37c59bf7"

    def __init__(self, location_id: Union[Location, str]):
        self.id: Union[Location, str] = location_id
        self.slug: Optional[str] = None
        self.name: Optional[str] = None
        self.has_public_page: Optional[bool] = None
        self.directory: Optional[str] = None
        self.coordinates: Optional[Tuple[str, str]] = None
        self.media_count: Optional[int] = None

        self.media: Set[Media] = set()
        self.top_posts: Set[Media] = set()

    def set_data(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.slug = data.get("slug")
        self.name = data.get("name")
        self.has_public_page = data.get("has_public_page")
        if "directory" in data:
            self.directory = data.get("directory")
        self.coordinates = (data.get("lat"), data.get("lng"))
        self.media_count = data.get("edge_location_to_media").get("count")
        for node in data.get("edge_location_to_top_posts").get("edges"):
            self.top_posts.add(Media(node.get("node").get("shortcode")))
