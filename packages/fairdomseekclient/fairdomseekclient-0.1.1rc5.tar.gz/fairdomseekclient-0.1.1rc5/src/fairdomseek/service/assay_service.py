import logging
from typing import Dict

from tenacity import stop_after_attempt, wait_exponential_jitter, retry_if_exception_type, retry

from fairdomseek.cache.cache import refresh_cache
from fairdomseek.cache.cash_assay import AssaysCache
from fairdomseek.mapper.policy_mapper import PolicyMapper
from fairdomseek.service.actor_service import ActorsService
from fairdomseek.service.base_service import BaseService
from fairdomseek.service.data_file_service import DataFileService
from fairdomseek.service.models_service import ModelsService
from fairdomseek.service.sample_service import SamplesService
from fairdomseek.service.sop_service import SopService
from fairdomseek.service.studies_service import StudiesService
from fairdomseek.translator.assay_translator import AssayTranslator
from fairdomseek.types.assay import Assay
from fairdomseek.types.data import DataFileRef
from fairdomseek.types.model import ModelRef
from fairdomseek.types.sample import SampleRef
from fairdomseek.util.project_checker import has_project
from openapi_client import AssaysApi, ApiClient

LOGGER = logging.getLogger(__name__)


class AssayService(BaseService):

    def __init__(self, actors_service: ActorsService,
                 studies_service: StudiesService,
                 samples_service: SamplesService,
                 model_service: ModelsService,
                 datafile_service: DataFileService,
                 sop_service: SopService,
                 cache: AssaysCache,
                 translator: AssayTranslator, client: ApiClient=None):
        super().__init__(client)
        self._translator = translator
        self._actors_service = actors_service
        self._studies_service = studies_service
        self._samples_service = samples_service
        self._model_service = model_service
        self._datafiles_service = datafile_service
        self._sop_service = sop_service
        self.cache = cache
        self.api = AssaysApi(client)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_assay_retry(self, assay, policy_dto):
        return self.api.create_assay(assay_post=self._translator.to_dto(assay, policy_dto))


    @has_project
    @refresh_cache()
    def create_assay(self, assay: Assay):
        if assay.title in self.cache.list_assays_by_title():
            LOGGER.error("Can't create \"{}\": already exists".format(assay.title))
            return

        #Looking up actors
        actors_internal_id = self._actors_service.get_actors_id(
            self._translator.get_actors_from_policies(assay.policies)
        )

        # Looking up studies
        self.__study_lookup(assay)

        # Looking up for model to get external id; must exist beforehand
        for mdl in assay.ref_models:
            self.__model_lookup(mdl)

        # Looking up for sample; must exist beforehand
        for sp in assay.ref_samples:
            self.__sample_lookup(sp)

        # Looking up for datafiles; must exist beforehand
        for df in assay.ref_datafiles:
            self.__datafiles_lookup(df)

        policy_dto = PolicyMapper().to_dto(assay.policies, actors_internal_id)
        return self.__create_assay_retry(assay, policy_dto)

    def __model_lookup(self, model_ref: ModelRef):
        mdl = self._model_service.get_from_ref(model_ref)
        # Model already exists server side
        if not mdl:
            raise Exception("Can't find model \"{}\"".format(model_ref.title))
        model_ref.external_id = mdl.external_id

    def __datafiles_lookup(self, datafile_ref: DataFileRef):
        df = self._datafiles_service.get_from_ref(datafile_ref)
        if not df:
            raise Exception("Can't find datafile \"{}\"".format(datafile_ref.title))
        datafile_ref.external_id = df.external_id

    def __sample_lookup(self, sampleRef: SampleRef):
        smp = self._samples_service.get_from_ref(sampleRef)
        if not smp:
            raise Exception("Can't find sample \"{}/{}\"".format(sampleRef.sample_type_name,
                                                                 sampleRef.sample_title))
        sampleRef.external_id = smp.external_id

    def __study_lookup(self, assay: Assay):
        # Looking up studies, eventually
        if assay.study_id is None:
            associated_study = self._studies_service.list_studies_by_title().get(assay.study_name, None)
            if associated_study is None:
                raise Exception("Cant create assay \"{}\": associated study \"{}\" doesn't exist".format(assay.title,
                                                                                                         assay.study_name))
            assay.study_id = associated_study.external_id


    @has_project
    @refresh_cache()
    def update_assay(self, assay: Assay):
        # Looking up actors
        actors_internal_id = self._actors_service.get_actors_id(
            self._translator.get_actors_from_policies(assay.policies)
        )

        #lookup studies, if new name is provided
        if assay.study_name is not None:
            self.__study_lookup(assay)

        #lookup assay based on title
        if assay.external_id is None:
            remote_assay = self.cache.list_assays_by_title().get(assay.title, None)
            if remote_assay is None:
                raise Exception("Cant update assay \"{}\": Not found".format(assay.title))
            assay.external_id = remote_assay.external_id

        # Looking up for model to get external id; must exist beforehand
        for mdl in assay.ref_models:
            self.__model_lookup(mdl)

        # Looking up for sample; must exist beforehand
        for sp in assay.ref_samples:
            self.__sample_lookup(sp)

        # Looking up for datafiles; must exist beforehand
        for df in assay.ref_datafiles:
            self.__datafiles_lookup(df)

        policy_dto = PolicyMapper().to_dto(assay.policies, actors_internal_id)
        self.api.update_assay(id=assay.external_id,
                             assay_patch=self._translator.to_dto_patch(assay, policy_dto))

    @has_project
    @refresh_cache()
    def delete_assay(self, assay_name: str):
        #lookup assay based on title
        assay = self.cache.list_assays_by_title().get(assay_name, None)
        if assay is None:
            raise Exception("Cant delete assay \"{}\": Not found".format(assay_name))

        self.api.delete_assay(assay.external_id)

    @has_project
    @refresh_cache()
    def list_assays(self):
        return list(self.cache.list_assays_by_title().keys())

    @has_project
    @refresh_cache()
    def get_assay(self, assay_title: str) -> Dict[str, int]:
        return self.cache.get_assay(assay_title)

    def set_client(self, client):
        super().set_client(client)
        self.api = AssaysApi(client)
