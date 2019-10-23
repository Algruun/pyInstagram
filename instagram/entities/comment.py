from __future__ import annotations

from typing import Union

from instagram.entities.account import Account
from instagram.entities.element import Element
from instagram.entities.media import Media


class Comment(Element):
    primary_key = "id"

    def __init__(
        self,
        comment_id: Union[Comment, str],
        media: Media,
        owner: Account,
        text: str,
        created_at: int,
    ):
        self.id = comment_id
        self.media = media
        self.owner = owner
        self.text = text
        self.created_at = created_at
