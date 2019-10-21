from __future__ import annotations

from typing import Union

from instagram_api.entities.element import Element


class Story(Element):
    primary_key = "id"

    def __init__(self, story_id: Union[Story, str]):
        self.id = story_id
