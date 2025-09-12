from fairdomseek.types.base_types import People
from fairdomseek.types.base_types import Project
from openapi_client import PermissionResource
from fairdomseek.types.base_types import Institution

class PeopleMapper:

    @staticmethod
    def to_domain(dto, metadata=None) -> People:
        return People(
            metadata=metadata,
            first_name=dto.attributes.first_name,
            last_name=dto.attributes.last_name
        )


    @staticmethod
    def to_domain_from_permission(permission: PermissionResource, actors_idx) -> People:
        return actors_idx["people"][permission.resource.id]

class ProjectMapper:

    @staticmethod
    def to_domain(dto, metadata=None) -> Project:
        return Project(
            metadata=metadata,
            title=dto.attributes.title
        )

    @staticmethod
    def to_domain_from_permission(permission: PermissionResource, actors_idx) -> Project:
        return actors_idx["projects"][permission.resource.id]

class InstitutionMapper:

    @staticmethod
    def to_domain(dto, metadata=None) -> Institution:
        return Institution(
            metadata=metadata,
            title=dto.attributes.title
        )

    @staticmethod
    def to_domain_from_permission(permission: PermissionResource, actors_idx) -> Institution:
        return actors_idx["institutions"][permission.resource.id]

