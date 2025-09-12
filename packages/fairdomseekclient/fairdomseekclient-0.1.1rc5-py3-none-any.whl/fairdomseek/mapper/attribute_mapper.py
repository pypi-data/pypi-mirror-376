from typing import Dict

from fairdomseek.types.attribute import AttrType, SampleTypeAttribute
from openapi_client import SampleTypeSampleAttributePost, SampleTypeSampleAttributePostSampleAttributeType, \
    SampleTypeSampleAttributePatch


class AttributeMapper:
    @staticmethod
    def to_dto(attr, existing_sample_type_titles, sample_type_title) -> SampleTypeSampleAttributePost:
        dto = SampleTypeSampleAttributePost(
            title=attr.title,
            description=attr.description,
            required=attr.required,
            sample_attribute_type=SampleTypeSampleAttributePostSampleAttributeType(title=attr.type),
            unit_symbol=attr.unit,
            is_title=attr.is_title
        )

        if attr.type == AttrType.RegisteredSample:
            if attr.registered_sample_title is None:
                raise ValueError(f"{sample_type_title}: {attr.title} is RegisteredSample but no title provided")
            if attr.registered_sample_title not in existing_sample_type_titles:
                raise ValueError(f"{sample_type_title}: {attr.title} refers to unknown sample type '{attr.registered_sample_title}'")
            dto.linked_sample_type_id = str(existing_sample_type_titles[attr.registered_sample_title].external_id)

        return dto

    @staticmethod
    def to_dto_patch(orig_attr, new_attr, existing_sample_type_titles, sample_type_title) -> SampleTypeSampleAttributePatch:

        # No new values ? Get out of my sight
        if new_attr is None:
            if orig_attr is not None:
                dto = SampleTypeSampleAttributePatch(title = orig_attr.title, _destroy = True, is_title = False)
                dto.id = str(orig_attr.id)
                return dto
            else:
                raise Exception("No legacy and new attribute definition provided")

        dto = SampleTypeSampleAttributePatch(
            title=new_attr.title,
            description=new_attr.description,
            required=new_attr.required,
            sample_attribute_type=SampleTypeSampleAttributePostSampleAttributeType(title=new_attr.type),
            unit_symbol=new_attr.unit,
            is_title=new_attr.is_title
        )

        # We are patching an already existing attribute
        if orig_attr is not None:
            dto.id = str(orig_attr.id)

        # Checking if referenced sample type is declared locally or remotely, or not
        if new_attr.type == AttrType.RegisteredSample:
            if new_attr.registered_sample_title is None:
                raise ValueError(f"{sample_type_title}: {new_attr.title} is RegisteredSample but no title provided")
            if new_attr.registered_sample_title not in existing_sample_type_titles:
                raise ValueError(f"{sample_type_title}: {new_attr.title} refers to unknown sample type '{new_attr.registered_sample_title}'")
            dto.linked_sample_type_id = str(existing_sample_type_titles[new_attr.registered_sample_title].external_id)
        return dto

    @staticmethod
    def to_domain(attr: SampleTypeSampleAttributePost, sample_types_idx: Dict[int, str]) -> SampleTypeAttribute:
        registered_sample_title_id = None

        # Lookup type string to constant name (reverse mapping)
        attr_type_value = attr.sample_attribute_type.title
        attr_type_key = next(
            (k for k, v in AttrType.__dict__.items() if not k.startswith('__') and v == attr_type_value), None)
        if not attr_type_key:
            raise ValueError(f"Unknown attribute type title: {attr_type_value}")

        # infer registered_sample_title if needed
        if attr_type_value in (AttrType.RegisteredSample, AttrType.RegisteredSampleList):
            registered_sample_title_id = getattr(attr, 'linked_sample_type_id', None)

        sta = SampleTypeAttribute(
            title=attr.title,
            description=attr.description,
            required=attr.required,
            attr_type=getattr(AttrType, attr_type_key),
            unit=attr.unit,
            is_title = attr.is_title,
        )

        sta.id = int(attr.id)

        if registered_sample_title_id is not None:
            sta.registered_sample_title  = sample_types_idx[int(registered_sample_title_id)]

        return sta
