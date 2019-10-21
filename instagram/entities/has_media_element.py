from instagram_api.entities.updatable_element import UpdatableElement


class HasMediaElement(UpdatableElement):
    @property
    def primary_key(self):
        raise NotImplementedError

    def set_data(self, data: dict):
        raise NotImplementedError

    @property
    def entry_data_path(self):
        raise NotImplementedError

    @property
    def base_url(self):
        raise NotImplementedError

    @property
    def media_path(self):
        raise NotImplementedError

    @property
    def media_query_hash(self):
        raise NotImplementedError
