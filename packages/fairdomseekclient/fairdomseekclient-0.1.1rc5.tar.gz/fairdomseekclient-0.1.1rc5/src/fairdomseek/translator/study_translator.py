from typing import Dict

from fairdomseek.translator.translator import Translator
from fairdomseek.types.base_types import BaseType
from fairdomseek.types.investigation import Investigation
from fairdomseek.types.study import Study
from openapi_client import StudyPost, StudyPatch, StudyPostData, StudyType, StudyPostDataAttributes, \
    StudyPostDataRelationships, SingleReference, ItemReference, StudyResponse, StudyPatchData, StudyPatchDataAttributes, \
    StudyPatchDataRelationships


class StudyTranslator(Translator):

    def __init__(self, policy_mapper):
        super().__init__(policy_mapper)

    def to_dto(self, study: Study, actors_internal_id: Dict[BaseType, int]) -> StudyPost:

        # Generate proper policy according to dto
        policy_dto = self.policy_mapper.to_dto(study.policies, actors_internal_id)
        return StudyPost(data=StudyPostData(type=StudyType.STUDIES,
                                            attributes=StudyPostDataAttributes(
                                                title=study.title,
                                                description=study.description,
                                                policy=policy_dto
                                            ),
                                            relationships=StudyPostDataRelationships(
                                                investigation=SingleReference(data=ItemReference(id=str(study.investigation.external_id),
                                                                                                 type="investigation"))
                                            )))

    def to_dto_patch(
            self,
            orig_st: Study,
            new_st: Study,
            actors_internal_id: Dict[BaseType, int],
    ) -> StudyPatch:

        # Generate policy DTO
        policy_dto = self.policy_mapper.to_dto(new_st.policies, actors_internal_id)

        # Build and return the patch
        return StudyPatch(
            data=StudyPatchData(
                id=orig_st.external_id,
                type=StudyType.STUDIES,
                attributes=StudyPatchDataAttributes(
                    title=new_st.title,
                    description=new_st.description,
                    policy=policy_dto
                ),
                relationships=StudyPatchDataRelationships(
                    investigation=SingleReference(data=ItemReference(id=str(new_st.investigation.external_id),
                                                                     type="investigation"))

                ),
            )
        )

    def to_domain(self, dto: StudyResponse, actor_idx: Dict,  metadata=None) -> Study:

        policies = self.policy_mapper.to_domain(dto.data.attributes.policy, actor_idx, metadata)
        st = Study(
            dto.data.attributes.title,
            None,
            dto.data.attributes.description,
            policies,
            Investigation(None, None, None,None), # Must be resolved later
        )
        st.external_id = dto.data.id
        st.investigation.external_id = dto.data.relationships.investigation.data.id
        return st