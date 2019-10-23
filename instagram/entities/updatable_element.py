from instagram.entities.element import Element


class UpdatableElement(Element):
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
