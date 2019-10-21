class ExceptionManager:
    def __init__(self, repeats=1):
        self.tree = {
            "action": lambda exception, *args, **kwargs: (args, kwargs),
            "branch": {},
        }
        self.repeats = repeats

    def __getitem__(self, key):
        if not issubclass(key, Exception):
            raise TypeError("Key must be Exception type")
        return self.search(key)[0]["action"]

    def search(self, exception):
        if not issubclass(exception, Exception):
            raise TypeError("'exception' must be Exception type")

        current = self.tree
        while True:
            for key, value in current["branch"].items():
                if key == exception:
                    return value, True
                elif issubclass(exception, key):
                    current = value
                    break
            else:
                return current, False
            continue

    def __setitem__(self, key, value):
        if not issubclass(key, Exception):
            raise TypeError("Key must be Exception type")
        if not callable(value):
            raise TypeError("Value must be function")

        item, exists = self.search(key)
        if exists:
            item["action"] = value
        else:
            item["branch"][key] = {"branch": {}, "action": value}

    def decorator(self, func):
        def wrapper(obj, *args, **kwargs):
            for _ in range(self.repeats):
                try:
                    return func(obj, *args, **kwargs)
                except Exception as e:
                    exception = e
                    args, kwargs = self[exception.__class__](exception, *args, **kwargs)
            else:
                raise exception

        return wrapper
