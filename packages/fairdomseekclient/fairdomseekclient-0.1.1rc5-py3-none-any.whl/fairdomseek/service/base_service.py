from typing import Optional

from openapi_client import ProjectsApi


class BaseService:

    def __init__(self, client=None):
        self.client = client
        self._project_id = None
        self.project_name = None

    def set_client(self, client):
        self.client = client

    def set_project_name(self, project_name):
        if project_name == self.project_name and self._project_id is not None:
            return
        self._project_id = BaseService.get_project_id(self.client, project_name)
        self.project_name = project_name
        if self._project_id is None:
            raise Exception("Project \"{}\" doesn't exists; please create it before using services".format(project_name))

    @staticmethod
    def get_project_id(client, project_name) -> Optional[str]:
        api  = ProjectsApi(client)
        api_response = api.list_projects()
        for datum in api_response.data:
            if datum.attributes.title == project_name:
                return datum.id
        return None
