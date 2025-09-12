def has_project(method):
    def wrapper(self, *args, **kwargs):
        if self._project_id is None:
            raise Exception("Targeted project has not be set, please proceed before execution")
        return method(self, *args, **kwargs)
    return wrapper
