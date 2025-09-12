from typing import Dict

from fairdomseek.translator.translator import Translator
from fairdomseek.types.data import DataFile
from fairdomseek.types.sample import Sample
from openapi_client import SingleReference, \
    ItemReference, MultipleReferences, SamplePost, \
    SamplePostData, SampleType, SamplePostDataAttributes, SamplePostDataRelationships, SamplePatch, SamplePatchData, \
    SamplePatchDataRelationships, SamplePatchDataAttributes, Policy, SampleResponseData


class SampleTranslator(Translator):
    def __init__(self, policy_mapper):
        super().__init__(policy_mapper)


    def to_dto(self, sample: Sample, project_id: str, policies_dto=None) -> SamplePost:
        attribute_map = {}
        for attr in sample.attributes:
            if isinstance(sample.attributes[attr], (DataFile, Sample)):
                attribute_map[attr] = sample.attributes[attr].external_id
                continue
            #other cases not referencing other objects
            attribute_map[attr] = sample.attributes[attr]

        return SamplePost(data=SamplePostData(
             type=SampleType.SAMPLES,
             attributes=SamplePostDataAttributes(
                 tags=sample.tags,
                 policy=policies_dto,
                 attribute_map=attribute_map
             ),
             relationships=SamplePostDataRelationships(
                 sample_type=SingleReference(data=ItemReference(id=str(sample.sample_type_id),
                                                     type="sample_type")),
                 projects=MultipleReferences(data=[ItemReference(id=str(project_id),
                                                     type="projects")]),
                 data_files = MultipleReferences(data=[])
             )
        ))

    def to_dto_patch(
            self,
            sample: Sample,
            project_id: str,
            policies_dto,
    ) -> SamplePatch:
        attribute_map = {}

        # Build and return the patch
        return SamplePatch(
            data=SamplePatchData(
                id=str(sample.external_id),
                type=SampleType.SAMPLES,
                attributes=SamplePatchDataAttributes(
                    tags=sample.tags,
                    policy=policies_dto,
                    attribute_map=attribute_map
                ),
                relationships=SamplePatchDataRelationships(
                    sample_type=SingleReference(data=ItemReference(id=str(sample.sample_type_id),
                                                                   type="sample_type")),
                    projects=MultipleReferences(data=[ItemReference(id=str(project_id),
                                                                    type="projects")]),
                ),
            )
        )

    def to_domain(self, dto: SampleResponseData, sample_type_name: str, sample_title, actor_idx: Dict,  metadata=None) -> Sample:
        policies = self.policy_mapper.to_domain(Policy.from_dict(dto.attributes.policy), actor_idx, metadata)

        sample = Sample(
            sample_type_name,
            sample_title,
            dto.attributes.tags,
            policies,
            **dto.attributes.attribute_map
        )

        sample.external_id = int(dto.id)
        sample.sample_type_id = int(dto.relationships.sample_type.data.id)

        return sample

