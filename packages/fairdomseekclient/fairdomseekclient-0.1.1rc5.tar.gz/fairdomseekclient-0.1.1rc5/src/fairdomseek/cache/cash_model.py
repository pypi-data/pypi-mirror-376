import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Union

from fairdomseek.cache.cache import Cache
from openapi_client import ModelsApi


class ModelCache(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = ModelsApi(client)
        self._actor_service = actor_service
        self._translator = translator

        self._md_by_id = {}
        self._md_by_title = {}
        self._external_md = []

    def refresh(self):
        if len(self._external_md) == 0 and len(self._md_by_title) == 0 and len(self._md_by_id) == 0:
            # Fresh cache
            self.__fetch_models(self._project_id)
            return

        all_md_ids = [int(d.id)  for d in self.api.list_models().data]
        to_evaluate = []
        for md_id in all_md_ids:
            if md_id in self._md_by_id.keys() or md_id in self._external_md:
                continue
            else:
                to_evaluate.append(md_id)

        if len(to_evaluate) != 0:
            self.__fetch_models(self._project_id, to_evaluate)

    def list_model_by_id(self):
        return self._md_by_id

    def list_model_by_title(self):
        return self._md_by_title

    def get_model(self, model: Union[int, str]):
        if isinstance(model, int):
            return self._md_by_id.get(model, None)
        if isinstance(model, str):
            return self._md_by_id.get(model, None)
        return None

    def __fetch_models(self, project_id: str, md_ids: List[int] = []):

        if len(md_ids) == 0:
            # evaluate everything
            md_ids_to_cache = [int(d.id)  for d in self.api.list_models().data]
        else:
            md_ids_to_cache = md_ids

        def read_md(md_id):
            resp =  self.api.read_model_without_preload_content(1, md_id)
            if resp is None:
                raise Exception("Data file with id {} read failed".format(md_id))
            my_resp = json.loads(resp.data.decode('utf-8'))
            # Refetch with latest
            my_resp =  self.api.read_model_without_preload_content(my_resp['data']['attributes']['latest_version'], md_id)
            if my_resp is None:
                raise Exception("Data file with id {} read failed".format(md_id))
            return json.loads(resp.data.decode('utf-8'))['data']

        with ThreadPoolExecutor(max_workers=8) as executor:
            #We fetch everything we can read here, not everything belong to us
            future_to_id = {executor.submit(read_md, sid): sid for sid in md_ids_to_cache}

            for future in as_completed(future_to_id):
                resp = future.result()
                if project_id in [project['id'] for project in resp['relationships']['projects']['data']]:
                    domain_model = self._translator.to_domain(resp, self._actor_service.get_actors_idx_by_id())
                    self._md_by_id[domain_model.external_id]  = domain_model
                    self._md_by_title[domain_model.title] = domain_model
                else:
                    self._external_md.append(resp.data.id)

    def set_client(self, client):
        self.api = ModelsApi(client)
        super().set_client(client)

