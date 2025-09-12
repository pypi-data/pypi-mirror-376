import logging

from tenacity import stop_after_attempt, wait_exponential_jitter, retry_if_exception_type, retry

from fairdomseek.cache.cache import refresh_cache
from fairdomseek.service.base_service import BaseService
from fairdomseek.types.study import Study
from openapi_client import StudiesApi

LOGGER = logging.getLogger(__name__)

class StudiesService(BaseService):

    def __init__(self, actors_service, investigation_service, cache, translator, client=None):
        super().__init__(client)
        self.translator = translator
        self.actors_service = actors_service
        self.investigation_service = investigation_service
        self.cache = cache
        self.api = StudiesApi(client)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_study_retry(self, dto):
        return self.api.create_study(dto)


    @refresh_cache()
    def create_study(self, study: Study):
        if study.title in self.cache.list_studies_by_title():
            raise Exception("Can't create \"{}\": already exists".format(study.title))
        if study.investigation is None:
            raise Exception("Study {} must specify a investigation ".format(study.title))
        if study.investigation.external_id is None:
            # Resolve ext id first
            associated_iv = self.investigation_service.list_investigations_by_title().get(study.investigation.title, None)
            if associated_iv is None:
                raise Exception("Investigation \"{}\" doesn't exist, can't proceed".format(study.investigation.title))
            study.investigation.external_id = associated_iv.external_id
        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(study.policies))
        dto = self.translator.to_dto(study,
                                     actors_internal_id)
        response = self.__create_study_retry(dto)
        return response.data.id


    def patch_study(self, orig_study: Study, new_study: Study) -> str:
        if orig_study.external_id is None:
            raise Exception("Cant reconciliate local and remote study: no id given for {}".format(orig_study.title))
        if new_study.investigation is None:
            raise Exception("Study {} must specify a investigation ".format(new_study.title))
        if new_study.investigation.external_id is None:
            # Resolve ext id first
            investigation = self.investigation_service.list_investigations_by_title().get(new_study.investigation.title, None)
            if investigation is None:
                raise Exception("Investigation {} doesn't exist, can't proceed".format(new_study.investigation.title))
            new_study.investigation.external_id = investigation.external_id

        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(new_study.policies))
        dto = self.translator.to_dto_patch(orig_study,
                                           new_study,
                                           actors_internal_id)
        response = self.api.update_study(int(orig_study.external_id), dto)
        # Update studies, eventually
        LOGGER.warning("WARNING study <-> assays should be checked and updated (by implementation), eventually")
        return response.data.id

    @refresh_cache()
    def delete_study(self, study_id: int):
        if study_id not in self.cache.list_studies_by_id():
            raise Exception("Can't delete study with id  \"{}\": doesn't exists".format(study_id))

        if self.api.delete_study(id=int(study_id)).status != "ok":
            raise Exception("Can't delete study")

    def set_client(self, client):
        super().set_client(client)
        self.api = StudiesApi(client)

    @refresh_cache()
    def list_studies_by_id(self):
        return self.cache.list_studies_by_id()

    @refresh_cache()
    def list_studies_by_title(self):
        return self.cache.list_studies_by_title()

