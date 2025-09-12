from typing import List, Dict, Union

from fairdomseek.mapper.actor_mapper import PeopleMapper, InstitutionMapper, ProjectMapper
from fairdomseek.service.base_service import BaseService
from fairdomseek.types.base_types import Public, People, Institution, Project, BaseType
from openapi_client import ProjectsApi, InstitutionsApi, PeopleApi

class UnexistingActor(Exception):

    def __init__(self, msg):
        super().__init__(msg)


class ActorsService(BaseService):


    def __init__(self, client=None):
        super().__init__(client)
        self.project_api = ProjectsApi(client)
        self.institution_api = InstitutionsApi(client)
        self.people_api = PeopleApi(client)
        self._actor_map_cache = {}

    def set_client(self, client):
        super().set_client(client)
        self.project_api = ProjectsApi(client)
        self.institution_api = InstitutionsApi(client)
        self.people_api = PeopleApi(client)

    def get_actors_idx_by_id(self) -> Dict[str, Dict[str, BaseType]]:
        if self._actor_map_cache != {}:
            return self._actor_map_cache
        a  = self.people_api.list_people().data
        self._actor_map_cache = {"projects":
                          {p.id: ProjectMapper.to_domain(p) for p in self.project_api.list_projects().data},
                      "institutions":
                          {i.id: InstitutionMapper.to_domain(i) for i in self.institution_api.list_institutions().data},
                      "people":
                          {d.id: PeopleMapper.to_domain(self.people_api.read_person(int(d.id)).data) for d in
                                 self.people_api.list_people().data}
                      }

        return self._actor_map_cache

    def get_actors_id(self, actors: List[Union[People, Institution, Project, Public]]) -> Dict[BaseType, Union[str, None]]:
        requested_actors = {a: None for a in actors if not isinstance(a, Public)}
        known_actors = self.get_actors_idx_by_id()
        
        # Fetch projects, institutions, people
        for p in requested_actors:
            if isinstance(p, People):
                for p_id, person in known_actors["people"].items():
                    if person.first_name == p.first_name and person.last_name == p.last_name:
                        requested_actors[p] = p_id
                        break
            elif isinstance(p, Institution):
                for inst_id, inst in known_actors["institutions"].items():
                    if p.title == inst.title:
                        requested_actors[p] = inst_id
                        break
            elif isinstance(p, Project):
                for proj_id, project in known_actors["projects"].items():
                    if p.title == project.title:
                        requested_actors[p] = proj_id
                        break

        # Check that everything has been resolved
        error_found = False
        error_msg= "Following actors ids related to policy management has not been found: "
        for ra in requested_actors:
            if requested_actors[ra] is None:
                error_msg+=ra.id() + ', '
                error_found = True
        if error_found:
            error_msg = error_msg[:-2]
            raise UnexistingActor(error_msg)

        return requested_actors

