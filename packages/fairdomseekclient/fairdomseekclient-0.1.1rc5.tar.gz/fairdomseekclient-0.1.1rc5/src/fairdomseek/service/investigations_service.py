import logging

from tenacity import stop_after_attempt, retry, wait_exponential_jitter, retry_if_exception_type

from fairdomseek.cache.cache import refresh_cache
from fairdomseek.service.base_service import BaseService
from fairdomseek.types.investigation import Investigation
from openapi_client import InvestigationsApi

LOGGER = logging.getLogger(__name__)

class InvestigationService(BaseService):

    def __init__(self, actors_service, cache, translator, client=None):
        super().__init__(client)
        self.translator = translator
        self.actors_service = actors_service
        self.api = InvestigationsApi(client)
        self.cache = cache

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_investigation_retry(self, dto):
        return self.api.create_investigation(dto)

    @refresh_cache()
    def create_investigation(self, investigation: Investigation) -> str:
        if investigation.title in self.cache.list_investigations_by_title():
            raise Exception("Can't create \"{}\": already exists".format(investigation.title))
        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(investigation.policies))
        dto = self.translator.to_dto(investigation,
                                     self._project_id,
                                     actors_internal_id)
        response = self.__create_investigation_retry(dto)
        return response.data.id

    @refresh_cache()
    def patch_investigation(self, orig_investigation: Investigation, new_investigation: Investigation) -> str:
        if orig_investigation.external_id is None:
            raise Exception("Cant reconciliate local and remote investigation: no id given for {}".format(orig_investigation.title))
        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(new_investigation.policies))
        dto = self.translator.to_dto_patch(orig_investigation,
                                           new_investigation,
                                           self._project_id,
                                           actors_internal_id)
        response = self.api.update_investigation(orig_investigation.external_id, dto)
        return response.data.id

    @refresh_cache()
    def delete_investigation(self, investigation_id: int):
        if investigation_id not in self.cache.list_investigations_by_id():
            raise Exception("Can't delete investigation with id \"{}\": it doesn't exist".format(investigation_id))

        if self.api.delete_investigation(id=investigation_id).status != "ok":
            raise Exception("Can't delete investigation")

    def set_client(self, client):
        super().set_client(client)
        self.api = InvestigationsApi(client)

    @refresh_cache()
    def list_investigations_by_id(self):
        return self.cache.list_investigations_by_id()

    @refresh_cache()
    def list_investigations_by_title(self):
        return self.cache.list_investigations_by_title()

    @refresh_cache()
    def get_investigation_by_id(self, iv_id):
        return self.cache.get_investigation(iv_id)


