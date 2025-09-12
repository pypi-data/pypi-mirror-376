from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union

from fairdomseek.cache.cache import Cache
from openapi_client import InvestigationsApi


class CashInvestigation(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = InvestigationsApi(client)
        self._actor_service = actor_service
        self._translator = translator

        self._investigations_by_id = {}
        self._investigations_by_title = {}
        self._external_investigations = []

    def refresh(self):
        if len(self._external_investigations) == 0 and len(self._investigations_by_title) == 0 and len(self._investigations_by_id) == 0:
            # Fresh cache
            self.__fetch_investigations(self._project_id)
            return

        all_iv_ids = [int(d.id)  for d in self.api.list_investigations().data]
        to_evaluate = []
        for iv_id in all_iv_ids:
            if iv_id in self._investigations_by_id.keys() or iv_id in self._external_investigations:
                continue
            else:
                to_evaluate.append(iv_id)

        if len(to_evaluate) != 0:
            self.__fetch_investigations(self._project_id, to_evaluate)

    def list_investigations_by_id(self):
        return self._investigations_by_id

    def list_investigations_by_title(self):
        return self._investigations_by_title

    def get_investigation(self, investigation: Union[int, str]):
        if isinstance(investigation, int):
            return self._investigations_by_id.get(investigation, None)
        if isinstance(investigation, str):
            return self._investigations_by_title.get(investigation, None)
        return None

    def __fetch_investigations(self, project_id: str, investigation_ids: List[int] = []):

        if len(investigation_ids) == 0:
            # evaluate everything
            iv_ids_to_cache = [int(d.id)  for d in self.api.list_investigations().data]
        else:
            iv_ids_to_cache = investigation_ids

        def read_investigation(iv_id):
            return self.api.read_investigation(iv_id)

        with ThreadPoolExecutor(max_workers=8) as executor:
            #We fetch everything we can read here, not everything belong to us
            future_to_id = {executor.submit(read_investigation, sid): sid for sid in iv_ids_to_cache}

            for future in as_completed(future_to_id):
                resp = future.result()
                if project_id in [project.id for project in resp.data.relationships.projects.data]:
                    domain_investigation = self._translator.to_domain(resp, self._actor_service.get_actors_idx_by_id())
                    self._investigations_by_id[int(resp.data.id)]  = domain_investigation
                    self._investigations_by_title[resp.data.attributes.title] = domain_investigation
                else:
                    self._external_investigations.append(resp.data.id)

    def set_client(self, client):
        super().set_client(client)
        self.api = InvestigationsApi(client)

