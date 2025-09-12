import json
import logging
from urllib.parse import urlparse, urlunparse

import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter, retry_if_exception_type

from fairdomseek.cache.cache import refresh_cache
from fairdomseek.mapper.policy_mapper import PolicyMapper
from fairdomseek.service.base_service import BaseService
from fairdomseek.types.data import DataFile, DataFileRef
from fairdomseek.util.content_type import infer_content_type
from fairdomseek.util.downloader import BlobStream
from fairdomseek.util.sha1sum import sha1sum
from openapi_client import DataFilesApi
from pathlib import Path

LOGGER = logging.getLogger(__name__)

class DataFileAlreadyExistException(Exception):
    pass

class DataFileService(BaseService):

    def __init__(self, actors_service, cache, translator, client=None):
        super().__init__(client)
        self.translator = translator
        self.actors_service = actors_service
        self.api = DataFilesApi(client)
        self.cache = cache

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=0.25, max=4.0),
        retry=retry_if_exception_type(Exception),
    )
    def __create_datafile_retry(self, dto):
        return self.api.create_data_file_without_preload_content(dto)

    @refresh_cache()
    def create_datafile(self, data: DataFile):
        if data.title in self.cache.list_datafile_by_title():
            # complete the external id, eventually (might return the cache value instead ?)
            if data.external_id is None:
                data.external_id = self.cache.list_datafile_by_title()[data.title].external_id
            raise DataFileAlreadyExistException("Can't create \"{}\": already exists".format(data.title))
        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(data.policies))
        policy_dto = PolicyMapper().to_dto(data.policies, actors_internal_id)
        dto = self.translator.to_dto(data,
                                     self._project_id,
                                     policy_dto)
        response = self.__create_datafile_retry(dto)
        if response is None:
            raise Exception("{} data file upload failed".format(data.title))
        my_resp = json.loads(response.data.decode('utf-8'))
        data.external_id = int(my_resp['data']['id'])

        def replace_host(url: str, new_base: str) -> str:
            old_parts = urlparse(url)
            new_parts = urlparse(new_base)

            replaced = old_parts._replace(scheme=new_parts.scheme,
                                          netloc=new_parts.netloc)
            return str(urlunparse(replaced))

        # Link might be wrong if server hostname is not the exposed service name; replace with the
        # one provided by the user during the configuration
        upload_link = replace_host(my_resp['data']['attributes']['content_blobs'][0]['link'], self.client.configuration.host)

        # Time to upload the file
        with open(data.file_path, "rb") as f:
            upload_response = requests.put(
                upload_link,
                auth=(self.client.configuration.username, self.client.configuration.password),
                files={
                    "file": (data.file_path.name, f, "application/octet-stream")
                },
                data={
                    "content_blob[original_filename]": data.file_path.name,
                    "content_blob[content_type]": "application/octet-stream",
                },
            )

            if not upload_response.ok:
                raise Exception("{} data file upload failed".format(data.title))

    @refresh_cache()
    def update_datafile(self, datafile: DataFile):
        #lookup datafile based on title
        remote_datafile = self.cache.list_datafile_by_title().get(datafile.title, None)
        if datafile.external_id is None and remote_datafile is None:
            raise Exception("Cant update assay \"{}\": Not found".format(datafile.title))
        datafile.external_id = remote_datafile.external_id

        #Compute current sha1sum, eventually
        new_file = False
        if datafile.file_path.exists():
            new_sha1sum = sha1sum(datafile.file_path)
            if new_sha1sum != remote_datafile.get_checksum():
                new_file = True

        actors_internal_id = self.actors_service.get_actors_id(self.translator.get_actors_from_policies(datafile.policies))
        policy_dto = PolicyMapper().to_dto(datafile.policies, actors_internal_id)
        dto = self.translator.to_dto_patch(datafile,
                                           self._project_id,
                                           policy_dto)

        response = self.api.update_data_file_without_preload_content(datafile.external_id, dto)
        if response is None:
            raise Exception("{} data file upload failed".format(datafile.title))
        if new_file:
            LOGGER.warning("Fairdom seek API doesn't support data file version, so new version of a given file can't be"
                           "created. Create a new DataFile or update the version via web browser client")

    @refresh_cache()
    def delete_datafile(self, datafile_name: str):
        datafile = self.cache.list_datafile_by_title().get(datafile_name, None)
        if not datafile:
            raise Exception("Can't delete datafile with id \"{}\": it doesn't exist".format(datafile_name))

        if self.api.delete_data_file(id=datafile.external_id).status != "ok":
            raise Exception("Can't delete datafile")

    def set_client(self, client):
        super().set_client(client)
        self.api = DataFilesApi(client)

    @refresh_cache()
    def list_datafile_by_id(self):
        return self.cache.list_datafile_by_id()

    @refresh_cache()
    def list_datafile_by_title(self):
        return self.cache.list_datafile_by_title()

    @refresh_cache()
    def get_datafile_by_id(self, data_id):
        return self.cache.get_datafile(data_id)

    def get_from_ref(self, datafileRef: DataFileRef) -> DataFile:
        return self.list_datafile_by_title().get(datafileRef.title, None)

    def download_data_file(self, data_file: DataFile, filename: str):
        if data_file is not None and data_file.has_blob_link():
            response = requests.get(data_file.get_blob_link(),
                                    auth=(self.client.configuration.username, self.client.configuration.password),
                                    stream=True)

            blob = BlobStream.from_http_response(response)

            def has_extension(fname: str) -> bool:
                return Path(fname).suffix != ''

            if not has_extension(filename):
                filename_with_extension = f"filename{blob.get_extension_hint()}"
            else:
                filename_with_extension = filename

            blob.serialize_to_file(filename_with_extension)
