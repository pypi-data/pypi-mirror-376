from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union

from fairdomseek.cache.cache import Cache
from openapi_client import AssaysApi


class AssaysCache(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = AssaysApi(client)
        self._actor_service = actor_service
        self._translator = translator

        self._assays_by_id = {}
        self._assays_by_title = {}
        self._external_assays = []

    def refresh(self):
        if len(self._external_assays) == 0 and len(self._external_assays) == 0 and len(self._assays_by_id) == 0:
            # Fresh cache
            self.__fetch_assays(self._project_id)
            return

        all_ass_ids = [int(d.id)  for d in self.api.list_assays().data]
        to_evaluate = []
        for ass_id in all_ass_ids:
            if ass_id in self._assays_by_id.keys() or ass_id in self._external_assays:
                continue
            else:
                to_evaluate.append(ass_id)

        if len(to_evaluate) != 0:
            self.__fetch_assays(self._project_id, to_evaluate)

    def list_assays_by_id(self):
        return self._assays_by_id

    def list_assays_by_title(self):
        return self._assays_by_title

    def get_assay(self, assay: Union[int, str]):
        if isinstance(assay, int):
            return self._assays_by_id.get(assay, None)
        if isinstance(assay, str):
            return self._assays_by_title.get(assay, None)
        return None

    def __fetch_assays(self, project_id: str, assays_ids: List[int] = []):

        if len(assays_ids) == 0:
            # evaluate everything
            iv_ids_to_cache = [int(d.id)  for d in self.api.list_assays().data]
        else:
            iv_ids_to_cache = assays_ids

        def read_assay(st_id):
            return self.api.read_assay(st_id)

        with ThreadPoolExecutor(max_workers=8) as executor:
            #We fetch everything we can read here, not everything belong to us
            future_to_id = {executor.submit(read_assay, sid): sid for sid in iv_ids_to_cache}

            for future in as_completed(future_to_id):
                resp = future.result()
                if project_id in [project.id for project in resp.data.relationships.projects.data]:
                    domain_investigation = self._translator.to_domain(resp, self._actor_service.get_actors_idx_by_id())
                    self._assays_by_id[int(resp.data.id)]  = domain_investigation
                    self._assays_by_title[resp.data.attributes.title] = domain_investigation
                else:
                    self._external_assays.append(resp.data.id)

    def set_client(self, client):
        self.api = AssaysApi(client)
        super().set_client(client)
