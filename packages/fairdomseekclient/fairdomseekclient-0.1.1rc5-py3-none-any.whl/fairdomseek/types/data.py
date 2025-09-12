from pathlib import Path
from typing import List, Union

from fairdomseek.types.access.policy import Policy
from fairdomseek.types.base_types import BaseType


class DataFile(BaseType):

    def __init__(self,title: str, description:str, tags: List[str],  policies: List[Policy]):
        super().__init__(None)
        self.title = title
        self.description = description
        self.tags = tags
        self.policies = policies
        self.path = Path
        self.file_path = None
        self.parent = None
        self.__blob_link = None
        self.__blob_content_type = None
        self.__blob_sha1sum = None
        self.external_id = None

    def set_blob_link(self, link, content_type):
        self.__blob_link = link
        self.__blob_content_type = content_type

    def set_data_path(self, file_path: Union[Path, str]):
        if isinstance(file_path, str):
            self.file_path = Path(file_path)
        else:
            self.file_path = file_path

    def has_blob_link(self):
        return self.__blob_link is not None

    def get_blob_link(self):
        return self.__blob_link

    def set_checksum(self, checksum):
        self.__blob_sha1sum = checksum

    def get_checksum(self):
        return self.__blob_sha1sum


class DataFileRef:

    def __init__(self, title):
        self.title = title
        self.external_id = None
