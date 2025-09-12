from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union

from fairdomseek.cache.cache import Cache
from openapi_client import StudiesApi


class StudiesCache(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = StudiesApi(client)
        self._actor_service = actor_service
        self._translator = translator

        self._studies_by_id = {}
        self._studies_by_title = {}
        self._external_studies = []


    def refresh(self):
        if len(self._external_studies) == 0 and len(self._studies_by_title) == 0 and len(self._studies_by_id) == 0:
            # Fresh cache
            self.__fetch_studies(self._project_id)
            return

        all_st_ids = [int(d.id)  for d in self.api.list_studies().data]
        to_evaluate = []
        for st_id in all_st_ids:
            if st_id in self._studies_by_id.keys() or st_id in self._external_studies:
                continue
            else:
                to_evaluate.append(st_id)

        if len(to_evaluate) != 0:
            self.__fetch_studies(self._project_id, to_evaluate)

    def list_studies_by_id(self):
        return self._studies_by_id

    def list_studies_by_title(self):
        return self._studies_by_title

    def get_study(self, study: Union[int, str]):
        if isinstance(study, int):
            return self._studies_by_id.get(study, None)
        if isinstance(study, str):
            return self._studies_by_title.get(study, None)
        return None

    def __fetch_studies(self, project_id: str, s_ids: List[int] = []):

        if len(s_ids) == 0:
            # evaluate everything
            st_ids_to_cache = [int(d.id)  for d in self.api.list_studies().data]
        else:
            st_ids_to_cache = s_ids

        def read_study(st_id):
            return self.api.read_study(st_id)

        with ThreadPoolExecutor(max_workers=8) as executor:
            #We fetch everything we can read here, not everything belong to us
            future_to_id = {executor.submit(read_study, sid): sid for sid in st_ids_to_cache}

            for future in as_completed(future_to_id):
                resp = future.result()
                if project_id in [project.id for project in resp.data.relationships.projects.data]:
                    domain_st = self._translator.to_domain(resp, self._actor_service.get_actors_idx_by_id())
                    self._studies_by_id[int(resp.data.id)]  = domain_st
                    self._studies_by_title[resp.data.attributes.title] = domain_st
                else:
                    self._external_studies.append(resp.data.id)

    def set_client(self, client):
        super().set_client(client)
        self.api = StudiesApi(client)
