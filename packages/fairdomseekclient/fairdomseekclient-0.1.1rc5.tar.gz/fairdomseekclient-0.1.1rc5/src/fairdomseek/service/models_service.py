import json
import logging
from urllib.parse import urlparse, urlunparse

import requests
from tenacity import stop_after_attempt, wait_exponential_jitter, retry_if_exception_type, retry

from fairdomseek.cache.cache import refresh_cache
from fairdomseek.mapper.policy_mapper import PolicyMapper
from fairdomseek.service.base_service import BaseService
from fairdomseek.types.model import Model, ModelRef
from fairdomseek.util.sha1sum import sha1sum
from openapi_client import ModelsApi

LOGGER = logging.getLogger(__name__)


class ModelsService(BaseService):

    def __init__(self, actors_service, cache, translator, client=None):
        super().__init__(client)
        self.translator = translator
        self.actors_service = actors_service
        self.api = ModelsApi(client)
        self.cache = cache

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_model_retry(self, dto):
        return self.api.create_model_without_preload_content(dto)

    @refresh_cache()
    def create_model(self, model: Model):
        if model.title in self.cache.list_model_by_title():
            raise Exception("Can't create \"{}\": already exists".format(model.title))
        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(model.policies))
        policy_dto = PolicyMapper().to_dto(model.policies, actors_internal_id)
        dto = self.translator.to_dto(model,
                                     self._project_id,
                                     policy_dto)
        response = self.__create_model_retry(dto)
        if response is None:
            raise Exception("{} model creation failed".format(model.title))
        my_resp = json.loads(response.data.decode('utf-8'))

        # Time to upload the file
        def replace_host(url: str, new_base: str) -> str:
            old_parts = urlparse(url)
            new_parts = urlparse(new_base)

            replaced = old_parts._replace(scheme=new_parts.scheme,
                                          netloc=new_parts.netloc)
            return str(urlunparse(replaced))

        # Link might be wrong if server hostname is not the exposed service name; replace with the
        # one provided by the user during the configuration
        upload_link = replace_host(my_resp['data']['attributes']['content_blobs'][0]['link'],
                                   self.client.configuration.host)

        with open(model.file_path, "rb") as f:
            upload_response = requests.put(
                upload_link,
                auth=(self.client.configuration.username, self.client.configuration.password),
                files={
                    "file": (model.file_path.name, f, "application/octet-stream")
                },
                data={
                    "content_blob[original_filename]": model.file_path.name,
                    "content_blob[content_type]": "application/octet-stream",
                },
            )

            if not upload_response.ok:
                raise Exception("{} model file upload failed".format(model.title))


    @refresh_cache()
    def update_model(self, model: Model):
        #lookup model based on title
        remote_model = self.cache.list_model_by_title().get(model.title, None)
        if model.external_id is None and remote_model is None:
            raise Exception("Cant update assay \"{}\": Not found".format(model.title))
        model.external_id = remote_model.external_id

        #Compute current sha1sum, eventually
        new_file = False
        if model.file_path.exists():
            new_sha1sum = sha1sum(model.file_path)
            if new_sha1sum != remote_model.get_checksum():
                new_file = True

        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(model.policies))
        policy_dto = PolicyMapper().to_dto(model.policies, actors_internal_id)
        dto = self.translator.to_dto_patch(model,
                                           self._project_id,
                                           policy_dto)

        response = self.api.update_model_without_preload_content(model.external_id, dto)
        if response is None:
            raise Exception("{} model file upload failed".format(model.title))
        if new_file:
            LOGGER.warning("Fairdom seek API doesn't support model file version, so new version of a given file can't be "
                           "created. Create a new Model, or update the version via web browser client")


    @refresh_cache()
    def delete_model(self, model_name: str):
        model = self.cache.list_model_by_title().get(model_name, None)
        if not model:
            raise Exception("Can't delete model with name \"{}\": it doesn't exist".format(model_name))

        if self.api.delete_model(id=model.external_id).status != "ok":
            raise Exception("Can't delete datafile")

    def set_client(self, client):
        super().set_client(client)
        self.api = ModelsApi(client)

    @refresh_cache()
    def list_model_by_id(self):
        return self.cache.list_model_by_id()

    @refresh_cache()
    def list_model_by_title(self):
        return self.cache.list_model_by_title()

    @refresh_cache()
    def get_model_by_id(self, model_id):
        return self.cache.get_model(model_id)

    def get_from_ref(self, model_ref: ModelRef) -> Model:
        return self.list_model_by_title().get(model_ref.title, None)


