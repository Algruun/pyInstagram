from __future__ import annotations

from typing import Union, Set, Dict, Optional, Any

from instagram.entities.has_media_element import HasMediaElement


class Account(HasMediaElement):
    primary_key = "username"
    entry_data_path = ("ProfilePage", 0, "graphql", "user")
    base_url = ""
    media_path = ("user", "edge_owner_to_timeline_media")
    media_query_hash = "c6809c9c025875ac6f02619eae97a80e"

    def __init__(self, username: Union[Account, str]):
        # super(Account, self).__init__(username)
        self.id: Optional[str] = None
        self.username: Union[Account, str] = username
        self.full_name: Optional[str] = None
        self.profile_pic_url: Optional[str] = None
        self.profile_pic_url_hd: Optional[str] = None
        self.fb_page: Optional[str] = None
        self.biography: Optional[str] = None
        self.follows_count: Optional[int] = None
        self.followers_count: Optional[int] = None
        self.media_count: Optional[int] = None
        self.is_private: Optional[bool] = None
        self.is_verified: Optional[bool] = None
        self.country_block: Optional[bool] = None

        from instagram.entities.media import Media

        self.media: Set[Media] = set()
        self.follows: Set[Account] = set()
        self.followers: Set[Account] = set()

    def set_data(self, data: Dict[str, Any]):
        self.id = data.get("id")
        self.full_name = data.get("full_name")
        self.profile_pic_url = data.get("profile_pic_url")
        self.profile_pic_url_hd = data.get("profile_pic_url_hd")
        self.fb_page = data.get("connected_fb_page")
        self.biography = data.get("biography")
        self.follows_count = data.get("edge_follow").get("count")
        self.followers_count = data.get("edge_followed_by").get("count")
        self.media_count = data.get("edge_owner_to_timeline_media").get("count")
        self.is_private = data.get("is_private")
        self.is_verified = data.get("is_verified")
        self.country_block = data.get("country_block")
