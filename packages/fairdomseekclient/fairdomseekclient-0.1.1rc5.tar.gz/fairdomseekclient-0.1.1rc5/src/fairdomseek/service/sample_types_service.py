import logging

from tenacity import stop_after_attempt, wait_exponential_jitter, retry_if_exception_type, retry

from fairdomseek.cache.cache import refresh_cache
from fairdomseek.service.base_service import BaseService
from openapi_client import SampleTypesApi
from fairdomseek.types.sample_type import SampleType

LOGGER = logging.getLogger(__name__)

class SampleTypeService(BaseService):
    def __init__(self, actors_service, cache, translator, client=None):
        super().__init__(client)
        self.translator = translator
        self.actors_service = actors_service
        self.cache = cache
        self.api = SampleTypesApi(client)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_sample_type_retry(self, dto):
        return self.api.create_sample_type(dto)


    @refresh_cache()
    def create_sample_type(self, sample_type: SampleType) -> str:
        if sample_type.title in self.cache.list_st_by_title():
            raise Exception("Can't create \"{}\": already exists".format(sample_type.title))

        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(sample_type.policies))

        dto = self.translator.to_dto(sample_type,
                                     self._project_id,
                                     actors_internal_id,
                                     self.cache.list_st_by_title())
        response = self.__create_sample_type_retry(dto)
        return response.data.id

    def patch_sample_type(self, orig_sample_type: SampleType, new_sample_type: SampleType) -> str:
        if orig_sample_type.external_id is None:
            raise Exception("Cant reconciliate local and remote sample type: no id given for {}".format(orig_sample_type.title))
        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(new_sample_type.policies))
        dto = self.translator.to_dto_patch(orig_sample_type,
                                           new_sample_type,
                                           self._project_id,
                                           actors_internal_id,
                                           self.cache.list_st_by_title())
        response = self.api.update_sample_type(orig_sample_type.external_id, dto)
        return response.data.id

    @refresh_cache()
    def delete_sample_type(self, sample_type_id: int):
        if sample_type_id not in self.cache.list_st_by_id():
            raise Exception("Can't delete sample type with id  \"{}\": doesn't exists".format(sample_type_id))

        if self.api.delete_sample_type(id=sample_type_id).status != "ok":
            raise Exception("Can't delete sample type")

    def set_client(self, client):
        super().set_client(client)
        self.api = SampleTypesApi(client)

    @refresh_cache()
    def list_sample_types_by_id(self):
        return self.cache.list_st_by_id()

    @refresh_cache()
    def list_sample_types_by_title(self):
        return self.cache.list_st_by_title()
