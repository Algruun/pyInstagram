class ElementConstructor(type):
    def __new__(mcs, name, classes, fields):
        def delete(self):
            key = self.__getattribute__(self.primary_key)
            if key in self.cache:
                del self.cache[key]

        @classmethod
        def clear_cache(cls):
            cls.cache.clear()

        fields["__del__"] = delete
        fields["clear_cache"] = clear_cache
        fields["__str__"] = lambda self: str(self.__getattribute__(self.primary_key))
        fields["__repr__"] = lambda self: str(self.__getattribute__(self.primary_key))
        fields["cache"] = dict()

        return super().__new__(mcs, name, classes, fields)

    def __call__(cls, key, *args, **kwargs):
        if not str(key) in cls.cache:
            cls.cache[str(key)] = super().__call__(str(key), *args, **kwargs)

        return cls.cache[str(key)]
