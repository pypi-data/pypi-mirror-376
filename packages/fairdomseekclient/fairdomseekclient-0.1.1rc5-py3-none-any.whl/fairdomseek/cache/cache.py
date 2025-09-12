from functools import wraps

from fairdomseek.service.actor_service import ActorsService


class Cache(object):

    def __init__(self, client, project_name):
        self._client = client
        self._project_id = None
        self.project_name = project_name
        if client is not None:
            self.set_project_name(project_name)

    def set_client(self, client):
        self._client = client

    def set_project_name(self, project_name):
        if project_name is None:
            return
        if self._client is None:
            raise Exception("APIClient must be set before setting project name")
        self._project_id = ActorsService.get_project_id(self._client, project_name)
        self.project_name = project_name
        if self._project_id is None:
            raise Exception("Project \"{}\" doesn't exists; please create it before using AssayService".format(project_name))

    def refresh(self):
        raise Exception("Must be implemented in subclasses")


def refresh_cache(attr_name="cache"):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            attr = getattr(self, attr_name, None)
            if attr is not None and hasattr(attr, 'refresh') and callable(attr.refresh):
                attr.refresh()
            else:
                raise AttributeError(f"Object must have a '{attr_name}.refresh()' method")
            return func(self, *args, **kwargs)
        return wrapper
    return decorator