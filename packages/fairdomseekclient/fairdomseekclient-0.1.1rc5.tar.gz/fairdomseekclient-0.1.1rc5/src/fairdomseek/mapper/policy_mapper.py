from typing import Optional

import fairdomseek
from fairdomseek.mapper.actor_mapper import PeopleMapper, ProjectMapper, InstitutionMapper
from fairdomseek.types.base_types import Public, People, Project, Institution
from openapi_client import Policy, AccessTypes, PolicyPermissionsInner, PermissionResource, PermissionResourceTypes


class PolicyMapper:
    @staticmethod
    def to_dto(policies, actors) -> Optional[Policy]:
        if policies is None:
            return None
        dto = Policy(access=AccessTypes.NO_ACCESS, permissions=[])
        for my_policy in policies:
            if isinstance(my_policy.target, Public):
                dto.access = my_policy.type
            else:
                dto.permissions.append(
                    PolicyPermissionsInner(resource=PermissionResource(
                            type=my_policy.target.type,
                            id=actors[my_policy.target]),
                        access=my_policy.type
                    )
                )
        return dto

    @staticmethod
    def get_actors_from_policies(policies):
        return [p.target for p in policies]

    @staticmethod
    def to_domain(policy_dto: Policy, actors_idx, metadata: object):
        # Handle the public access
        policy_rules = [fairdomseek.types.access.policy.Policy(
            my_type=policy_dto.access.value,
            target=Public(metadata)
        )]
        # Handle permissions for specific actors
        for permission in policy_dto.permissions:
            actor = None
            if permission.resource.type == PermissionResourceTypes.PEOPLE:
                actor = PeopleMapper.to_domain_from_permission(permission, actors_idx)
            if permission.resource.type == PermissionResourceTypes.PROJECTS:
                actor = ProjectMapper.to_domain_from_permission(permission, actors_idx)
            if permission.resource.type == PermissionResourceTypes.INSTITUTIONS:
                actor = InstitutionMapper.to_domain_from_permission(permission, actors_idx)
            if actor:
                policy_rules.append(fairdomseek.types.access.policy.Policy(
                    my_type=getattr(fairdomseek.types.access.policy.Policy, permission.access.upper()) ,
                    target=actor))

        return policy_rules
