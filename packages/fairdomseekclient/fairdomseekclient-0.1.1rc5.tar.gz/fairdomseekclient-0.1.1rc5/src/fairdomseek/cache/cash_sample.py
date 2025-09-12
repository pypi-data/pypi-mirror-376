from typing import Optional

from fairdomseek.cache.cache import Cache
from fairdomseek.extension.SamplesApiExtension import SamplesApiExtension
from fairdomseek.types.sample import Sample


class SampleCache(Cache):

    def __init__(self, actor_service, translator, client, project_name=None):
        super().__init__(client, project_name)
        self.api = SamplesApiExtension(client)
        self._actor_service = actor_service
        self._translator = translator

    def get_sample(self, sample_type_name, sample_type_id, sample_title, lazy_loading=False) -> Optional[Sample]:
        sample_list = self.api.list_sample_by_type(sample_type_id)
        for sp in sample_list:
            sp_name, sp_id =next(iter(sp.items()))
            if sample_title == sp_name:
                return self.__read_sample(sample_type_name, sample_title, sp_id, lazy_loading)

        return None

    def __read_sample(self, sample_type_name, sample_title, sample_id, lazy_loading):
        sample = self._translator.to_domain(
            self.api.read_sample(sample_id).data,
            sample_type_name,
            sample_title,
            self._actor_service.get_actors_idx_by_id())

        if lazy_loading is True:
            return sample

        # Post processing sample to resolve
        for attr in sample.attributes:
            if isinstance(sample.attributes[attr], dict) and 'type' in sample.attributes[attr].keys():
                if sample.attributes[attr]['type'] == 'Sample':
                    sample.attributes[attr] =  self.__read_sample(None, sample.attributes[attr]['title'],
                                                                  int(sample.attributes[attr]['id']), lazy_loading)

        return sample

    def set_client(self, client):
        self.api = SamplesApiExtension(client)
        super().set_client(client)
