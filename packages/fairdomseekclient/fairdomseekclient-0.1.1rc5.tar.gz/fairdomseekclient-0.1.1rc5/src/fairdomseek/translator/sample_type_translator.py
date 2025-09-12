from typing import Dict

from fairdomseek.translator.translator import Translator
from fairdomseek.types.base_types import BaseType
from fairdomseek.types.sample_type import SampleType
from openapi_client import SampleTypePost, SampleTypePostData, SampleTypeType, SampleTypePostDataAttributes, \
    SampleTypePostDataRelationships, MultipleReferences, ItemReference, SampleTypeResponse, SampleTypePatch, \
    SampleTypePatchData, SampleTypePatchDataAttributes, SampleTypePatchDataRelationships


class SampleTypeTranslator(Translator):
    def __init__(self, policy_mapper, attribute_mapper):
        super().__init__(policy_mapper)
        self.attribute_mapper = attribute_mapper

    def get_sample_type_actors(self, st: SampleType):
        return self.policy_mapper.get_actors_from_policies(st.policies)

    def to_dto(self, sample_type: SampleType, project_id: str, actors_internal_id: Dict[BaseType, int],
               existing_sample_type: Dict[str, int]) -> SampleTypePost:
        attributes_dto = [
            self.attribute_mapper.to_dto(attr, existing_sample_type, sample_type.title)
            for attr in sample_type.attributes
        ]

        # Ensure one attribute is marked as title
        if not any(getattr(attr, "is_title", False) for attr in attributes_dto) and attributes_dto:
            raise Exception(
                "At least one attribute must be flagged as title for sample type {}".format(sample_type.title))

        # Check for duplicates
        titles = [a.title for a in attributes_dto]
        if len(set(titles)) != len(titles):
            raise ValueError(f"Duplicate attribute titles in sample '{sample_type.title}'")

        # Generate proper policy according to dto
        policy_dto = self.policy_mapper.to_dto(sample_type.policies, actors_internal_id)

        return SampleTypePost(
            data=SampleTypePostData(
                type=SampleTypeType.SAMPLE_TYPES,
                attributes=SampleTypePostDataAttributes(
                    title=sample_type.title,
                    description=sample_type.description,
                    tags=sample_type.tags or None,
                    policy=policy_dto,
                    sample_attributes=attributes_dto
                ),
                relationships=SampleTypePostDataRelationships(
                    projects=MultipleReferences(data=[ItemReference(id=project_id, type="projects")])
                )
            )
        )

    def to_dto_patch(
            self,
            orig_sample_type: SampleType,
            new_sample_type: SampleType,
            project_id: str,
            actors_internal_id: Dict[BaseType, int],
            existing_sample_type: Dict[str, int]
    ) -> SampleTypePatch:

        # Index attributes by title
        orig_attrs = {attr.title: attr for attr in orig_sample_type.attributes}
        new_attrs = {attr.title: attr for attr in new_sample_type.attributes}

        # Classify attributes
        both_titles = orig_attrs.keys() & new_attrs.keys()
        orig_only_titles = orig_attrs.keys() - new_attrs.keys()
        new_only_titles = new_attrs.keys() - orig_attrs.keys()

        attributes_dto = []

        # Attributes present in both original and new sample types
        for title in both_titles:
            orig_attr = orig_attrs[title]
            new_attr = new_attrs[title]
            attributes_dto.append(
                self.attribute_mapper.to_dto_patch(orig_attr, new_attr, existing_sample_type, title)
            )

        # Attributes removed in new sample type
        for title in orig_only_titles:
            orig_attr = orig_attrs[title]
            attributes_dto.append(
                self.attribute_mapper.to_dto_patch(orig_attr, None, existing_sample_type, title)
            )

        # New attributes added
        for title in new_only_titles:
            new_attr = new_attrs[title]
            attributes_dto.append(
                self.attribute_mapper.to_dto_patch(None, new_attr, existing_sample_type, title)
            )

        # Ensure at least one attribute is flagged as title
        if not any(getattr(attr, "is_title", False) for attr in attributes_dto) and attributes_dto:
            raise Exception(
                f"At least one attribute must be flagged as title for sample type '{new_sample_type.title}'")

        # Check for duplicate attribute titles
        titles = [attr.title for attr in attributes_dto]
        if len(titles) != len(set(titles)):
            raise ValueError(f"Duplicate attribute titles in sample type '{new_sample_type.title}'")

        # Generate policy DTO
        policy_dto = self.policy_mapper.to_dto(new_sample_type.policies, actors_internal_id)

        # Build and return the patch
        return SampleTypePatch(
            data=SampleTypePatchData(
                # id=str(orig_sample_type.external_id),
                type=SampleTypeType.SAMPLE_TYPES,
                attributes=SampleTypePatchDataAttributes(
                    title=new_sample_type.title,
                    description=new_sample_type.description,
                    tags=new_sample_type.tags or None,
                    policy=policy_dto,
                    sample_attributes=attributes_dto
                ),
                relationships=SampleTypePatchDataRelationships(
                    projects=MultipleReferences(
                        data=[ItemReference(id=project_id, type="projects")]
                    )
                )
            )
        )

    def to_domain(self, dto: SampleTypeResponse, sample_types_idx: Dict[int, str], actor_idx: Dict,
                  metadata=None) -> SampleType:
        attributes = [
            self.attribute_mapper.to_domain(attr, sample_types_idx)
            for attr in dto.data.attributes.sample_attributes
        ]

        policies = self.policy_mapper.to_domain(dto.data.attributes.policy, actor_idx, metadata)

        st = SampleType(
            dto.data.attributes.title,
            None,
            dto.data.attributes.description,
            list(set(dto.data.attributes.tags)) or [],
            policies,
            *attributes,
        )

        st.external_id = int(dto.data.id)
        return st
