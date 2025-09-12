from typing import Dict

from fairdomseek.translator.translator import Translator
from fairdomseek.types.base_types import BaseType
from fairdomseek.types.investigation import Investigation
from openapi_client import MultipleReferences, ItemReference, \
    InvestigationPostDataAttributes, InvestigationPostDataRelationships, InvestigationPost, InvestigationPostData, \
    InvestigationPatch, InvestigationPatchData, InvestigationPatchDataAttributes, InvestigationType, \
    InvestigationPatchDataRelationships, InvestigationResponse


class InvestigationTranslator(Translator):

    def __init__(self, policy_mapper):
        super().__init__(policy_mapper)

    def to_dto(self, investigation: Investigation, project_id: str, actors_internal_id: Dict[BaseType, int]) -> InvestigationPost:

        # Generate proper policy according to dto
        policy_dto = self.policy_mapper.to_dto(investigation.policies, actors_internal_id)

        return InvestigationPost(data=InvestigationPostData(
            type=InvestigationType.INVESTIGATIONS,
            attributes = InvestigationPostDataAttributes(
                title=investigation.title,
                description=investigation.description,
                policy=policy_dto
            ),
            relationships = InvestigationPostDataRelationships(
                projects= MultipleReferences(data=[ItemReference(id=project_id, type="projects")])
            )
        ))

    def to_dto_patch(
            self,
            orig_iv: Investigation,
            new_iv: Investigation,
            project_id: str,
            actors_internal_id: Dict[BaseType, int],
    ) -> InvestigationPatch:

        # Generate policy DTO
        policy_dto = self.policy_mapper.to_dto(new_iv.policies, actors_internal_id)

        # Build and return the patch
        return InvestigationPatch(
            data=InvestigationPatchData(
                id = str(orig_iv.external_id),
                type=InvestigationType.INVESTIGATIONS,
                attributes=InvestigationPatchDataAttributes(
                    title=new_iv.title,
                    description=new_iv.description,
                    policy=policy_dto,
                ),
                relationships=InvestigationPatchDataRelationships(
                    projects=MultipleReferences(
                        data=[ItemReference(id=project_id, type="projects")]
                    )
                )
            )
        )

    def to_domain(self, dto: InvestigationResponse, actor_idx: Dict,  metadata=None) -> Investigation:

        policies = self.policy_mapper.to_domain(dto.data.attributes.policy, actor_idx, metadata)

        iv = Investigation(
            dto.data.attributes.title,
            None,
            dto.data.attributes.description,
            policies,
        )

        iv.external_id = int(dto.data.id)
        return iv