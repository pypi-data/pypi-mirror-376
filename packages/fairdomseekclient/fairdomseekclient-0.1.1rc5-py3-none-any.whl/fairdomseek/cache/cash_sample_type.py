from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union

from fairdomseek.cache.cache import Cache
from fairdomseek.service.actor_service import ActorsService
from openapi_client import SampleTypesApi


class SampleTypeCache(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = SampleTypesApi(client)
        self._actor_service = actor_service
        self._translator = translator

        self._st_by_id = {}
        self._st_by_title = {}
        self._external_st = []

    def refresh(self):
        if len(self._external_st) == 0 and len(self._st_by_title) == 0 and len(self._st_by_id) == 0:
            # Fresh cache
            self.__fetch_sample_types(self._project_id)
            return

        all_st_ids = [int(d.id)  for d in self.api.list_sample_types().data]
        to_evaluate = []
        for st_id in all_st_ids:
            if st_id in self._st_by_id.keys() or st_id in self._external_st:
                continue
            else:
                to_evaluate.append(st_id)

        if len(to_evaluate) != 0:
            self.__fetch_sample_types(self._project_id, to_evaluate)

    def list_st_by_id(self):
        return self._st_by_id

    def list_st_by_title(self):
        return self._st_by_title

    def get_sample_type(self, st: Union[int, str]):
        if isinstance(st, int):
            return self._st_by_id.get(st, None)
        if isinstance(st, str):
            return self._st_by_title.get(st, None)
        return None

    def __fetch_sample_types(self, project_id: str, investigation_ids: List[int] = []):

        st_to_process = []
        id_title_index = {}
        if len(investigation_ids) == 0:
            # evaluate everything
            iv_ids_to_cache = [int(d.id)  for d in self.api.list_sample_types().data]
        else:
            iv_ids_to_cache = investigation_ids

        def read_study(st_id):
            return self.api.read_sample_type(st_id)

        with ThreadPoolExecutor(max_workers=8) as executor:
            #We fetch everything we can read here, not everything belong to us
            future_to_id = {executor.submit(read_study, sid): sid for sid in iv_ids_to_cache}

            for future in as_completed(future_to_id):
                resp = future.result()
                if project_id in [project.id for project in resp.data.relationships.projects.data]:
                    st_to_process.append(resp)
                    id_title_index[int(resp.data.id)] = resp.data.attributes.title
                else:
                    self._external_st.append(resp.data.id)

        for st in st_to_process:
            domain_investigation = self._translator.to_domain(st,
                                                              id_title_index,
                                                              self._actor_service.get_actors_idx_by_id())
            self._st_by_id[int(st.data.id)] = domain_investigation
            self._st_by_title[st.data.attributes.title] = domain_investigation

    def set_client(self, client):
        super().set_client(client)
        self.api = SampleTypesApi(client)

