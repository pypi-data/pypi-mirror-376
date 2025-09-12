import json
import logging
from multiprocessing.dummy import Pool
from typing import Optional, List, Iterable

from tenacity import retry_if_exception_type, wait_exponential_jitter, stop_after_attempt, retry

from fairdomseek.cache.cash_sample import SampleCache
from fairdomseek.extension.SamplesApiExtension import SamplesApiExtension
from fairdomseek.mapper.policy_mapper import PolicyMapper
from fairdomseek.service.actor_service import ActorsService
from fairdomseek.service.base_service import BaseService
from fairdomseek.service.data_file_service import DataFileService, DataFileAlreadyExistException
from fairdomseek.service.sample_types_service import SampleTypeService
from fairdomseek.translator.sample_translator import SampleTranslator
from fairdomseek.types.data import DataFile
from fairdomseek.types.sample import Sample, UndefinedTitle, SampleRef
from fairdomseek.types.sample_type import SampleType
from openapi_client import SamplesApi, ApiClient

LOGGER = logging.getLogger(__name__)

class SamplesService(BaseService):

    def __init__(self,
                 actors_service: ActorsService,
                 sample_type_service: SampleTypeService,
                 data_file_service: DataFileService,
                 cache: SampleCache,
                 translator: SampleTranslator,
                 client: ApiClient=None):
        super().__init__(client)
        self._translator = translator
        self._actors_service = actors_service
        self._sample_type_service = sample_type_service
        self._data_file_service = data_file_service
        self._cache = cache
        self.api = SamplesApiExtension(client)

    def create_sample_batch(self, samples: List[Sample], workers: int = 8):
        if not samples:
            LOGGER.warning("No samples provided for batch creation")
            return

        def worker(sample):
            try:
                self.create_sample(sample)
                return sample
            except Exception as e:
                LOGGER.error(f"Failed to create sample {getattr(sample, 'sample_title', None)}: {e}")
                return None

        with Pool(workers) as pool:
            results = pool.map(worker, samples)

        created = [s for s in results if s is not None]
        failed = len(samples) - len(created)

        LOGGER.info(f"Batch creation complete: {len(created)} succeeded, {failed} failed")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_sample_retry(self, dto):
        return self.api.create_sample_without_preload_content(dto)

    def create_sample(self, sample: Sample):

        # Resolving sample type first
        st = None
        if sample.sample_type_id is None:
            if sample.sample_type_name is None:
                raise Exception("No sample type declared for sample")
            st = self.__lookup_sample_type(sample.sample_type_name)
            if st is None:
                raise Exception("Can't fine sample type \"{}\"".format(sample.sample_type_name))
            sample.sample_type_id = st.external_id

        # If "sample.sample_title" is specified, the sample MUST exists server side, and no attr should be
        # defined. Just fetch the id (we are referencing a sample dependency, defined elsewhere, in a recursive creation approach here)
        if sample.sample_title is not None:
            remote_sample = self._cache.get_sample(sample.sample_type_name, sample.sample_type_id, sample.sample_title, lazy_loading=False)
            if remote_sample is None:
                raise Exception("Can't find sample \"{}\" with type \"{}\"".format(sample.sample_title, sample.sample_type_name))
            sample.external_id = remote_sample.external_id
            return

        # If not, creation is expected, so one of the attr MUST be set as title, and sample MUST not exist server side
        # Otherwise, update should be done, and not creation
        try:
            sample_title_key, sample_title_value = sample.get_title(st)
            LOGGER.info("Starting creation of sample {}:{}".format(sample_title_key, sample_title_value))
            remote_sample = self._cache.get_sample(sample.sample_type_name, sample.sample_type_id, sample_title_value, lazy_loading=False)
            if remote_sample is not None:
                LOGGER.warning("Sample \"{}\" with type \"{}\" already exists, will not create".format(sample_title_value, st.title))
                sample.external_id = remote_sample.external_id
                return
        except UndefinedTitle as e:
            raise Exception("No title defined for a sample with sample type \"{}\"".format(st.title))

        # Time to create the stuff now
        # Check st attributes against sample attributes
        unexisting_attr, missing_attr = sample.is_instance(st)
        if len(unexisting_attr) > 0:
            for attr in unexisting_attr:
                LOGGER.error("{} doesn't exist in sample type {}".format(attr, sample.sample_type_name))
        if len(missing_attr) > 0:
            for attr in missing_attr:
                LOGGER.error("{} is required by sample type {}, and not provided".format(attr, sample.sample_type_name))

        # Check attributes validity
        if sample.is_valid(st) is False:
            raise Exception("Too many errors, can't create sample")

        # Creates DataFile and Sample, eventually
        for attr in sample.attributes.values():
            if isinstance(attr, DataFile):
                try:
                    self._data_file_service.create_datafile(attr)
                except DataFileAlreadyExistException as e:
                    LOGGER.warning(str(e))
            if isinstance(attr, Sample):
                self.create_sample(attr)

        # Finally dto the shit out the sample, and creates it
        actors_internal_id = self._actors_service.get_actors_id(self._translator.get_actors_from_policies(sample.policies))
        policy_dto = PolicyMapper().to_dto(sample.policies, actors_internal_id)
        dto = self._translator.to_dto(sample,
                                     self._project_id,
                                     policy_dto)
        LOGGER.info("Creating sample {}".format(sample.get_title(st)))
        response =self.__create_sample_retry(dto)
        if response is None or response.status != 200:
            raise Exception("{} sample creation failed")
        sample.external_id = int(json.loads(response.data.decode('utf-8'))['data']['id'])

    def get_sample(self, sample_id: int) -> Optional[Sample]:
        resp  = self.api.read_sample_without_preload_content(sample_id)
        if resp is not None:
            my_resp = json.loads(resp.data.decode('utf-8'))
            if 'errors' in my_resp:
                for err in my_resp['errors']:
                    LOGGER.error("{}".format(err['detail']))
                raise Exception("Can't get sample with id {}".format(sample_id))
            my_resp = my_resp['data']
            sample_type_id = int(my_resp['relationships']['sample_type']['data']['id'])
            #Looking up sample type id to get sample type name
            sample_type = self._sample_type_service.list_sample_types_by_id().get(sample_type_id, None)
            if sample_type is None:
                LOGGER.warning("Cant find sample type with id {}".format(sample_type_id))
            return self._translator.to_domain(my_resp, sample_type.title, self._actors_service.get_actors_idx_by_id())
        return None

    def delete_sample_by_id(self, sample_id):
            self.api.delete_sample(sample_id)

    def delete_sample_batch(self, sample_ids: Iterable[int], workers: int = 8):
        ids = list(sample_ids)
        if not ids:
            LOGGER.warning("No sample IDs provided for batch deletion")
            return

        def worker(sample_id):
            try:
                self.delete_sample_by_id(sample_id)
                return sample_id
            except Exception as e:
                LOGGER.error(f"Failed to delete sample {sample_id}: {e}")
                return None

        with Pool(workers) as pool:
            results = pool.map(worker, ids)

        deleted = [sid for sid in results if sid is not None]
        failed = len(ids) - len(deleted)

        LOGGER.info(f"Batch deletion complete: {len(deleted)} succeeded, {failed} failed")


    def delete_sample(self, sample_type_name: str, sample_title: str):
        sample_type = self.__lookup_sample_type(sample_type_name)
        if not sample_type:
            raise Exception("Cant found sample type \"{}\" for \"{}\" deletion".format(sample_type_name, sample_type))
        sample  = self._cache.get_sample(sample_type_name, sample_type.external_id, sample_title)
        if not sample:
            raise Exception("Cant found sample \"{}\" of type \"{}\"; can't perfom deletion".format(sample_type_name, sample_type))

        self.api.delete_sample(sample.external_id)

    def update_sample(self, sample_type_name: str, sample_title: str, new_sample_definition: Sample):
        msg = "Update operation not supported for \"{}\"/\"{}\" please delete and recreate the sample".format(sample_type_name,                                                                                                             sample_title)
        LOGGER.error(msg)
        raise Exception(msg)

    def __lookup_sample_type(self, sample_type_name: str) -> SampleType:
        return self._sample_type_service.list_sample_types_by_title().get(sample_type_name, None)


    def get_from_ref(self, sampleRef: SampleRef) -> Sample:
        sample_type = self.__lookup_sample_type(sampleRef.sample_type_name)
        if not sample_type:
            raise Exception("Can't find sample type for sample reference {}/{}".format(sampleRef.sample_type_name,
                                                                                       sampleRef.sample_title))
        return self._cache.get_sample(sampleRef.sample_type_name, sample_type.external_id, sampleRef.sample_title,
                                               lazy_loading=True)


    def set_client(self, client):
        super().set_client(client)
        self.api = SamplesApiExtension(client)