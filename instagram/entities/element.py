from instagram_api.entities.element_constructor import ElementConstructor


class Element(metaclass=ElementConstructor):
    def primary_key(self):
        raise NotImplementedError
