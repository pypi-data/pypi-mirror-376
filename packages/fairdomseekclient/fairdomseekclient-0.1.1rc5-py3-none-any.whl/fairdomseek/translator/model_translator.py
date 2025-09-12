from typing import Dict

import openapi_client
from fairdomseek.translator.translator import Translator
from fairdomseek.types.model import Model, ModelType, ModelFormat, SoftwareTool
from fairdomseek.util.content_type import infer_content_type
from openapi_client import ItemReference, MultipleReferences, ContentBlobSlot, \
     ContentBlobPlaceholder, Policy, ModelPost, ModelPostData, \
    ModelPostDataRelationships, ModelPostDataAttributes, ModelPatch, ModelPatchData, ModelPatchDataAttributes, \
    ModelPatchDataRelationships


class ModelTranslater(Translator):
    def __init__(self, policy_mapper):
        super().__init__(policy_mapper)

    def to_dto(self, model: Model, project_id: str, policy_dto=None) -> ModelPost:

        if model.file_path is None:
            raise Exception("Can't create Model \"{}\": associated model file is not specified".format(model.title))
        if not model.file_path.exists():
            raise Exception("Can't create Model \"{}\": {} doesn't exist".format(model.title, model.file_path))

        return ModelPost(data=ModelPostData(type=openapi_client.models.ModelType.MODELS,
                             attributes=ModelPostDataAttributes(
                                 tags=model.tags,
                                 title=model.title,
                                 description=model.description,
                                 content_blobs=[ContentBlobSlot(
                                     ContentBlobPlaceholder(
                                         original_filename=model.file_path.name,
                                         content_type=infer_content_type(model.file_path))),
                                 ],
                                 policy=policy_dto,
                                 model_type=model.model_type.value if model.model_type is not None else None,
                                 model_format=model.model_format.value if model.model_format is not None else None,
                                 environment=model.environment.value if model.environment is not None else None
                             ),
                             relationships=ModelPostDataRelationships(
                                 projects= MultipleReferences(data=[ItemReference(id=project_id, type="projects")]),
                             ))
                           )

    def to_dto_patch(
            self,
            model: Model,
            project_id: str,
            policies_dto,
    ) -> ModelPatch:

        # Build and return the patch
        dfp = ModelPatch(
            data=ModelPatchData(
                id=str(model.external_id),
                type=openapi_client.models.ModelType.MODELS,
                attributes=ModelPatchDataAttributes(
                    tags=model.tags,
                    title=model.title,
                    description=model.description,
                    policy=policies_dto,
                    model_type=model.model_type.value if model.model_type is not None else None,
                    model_format=model.model_format.value if model.model_format is not None else None,
                    environment=model.environment.value if model.environment is not None else None
                ),
                relationships=ModelPatchDataRelationships(
                    projects= MultipleReferences(data=[ItemReference(id=project_id, type="projects")]),
                ),
            )
        )

        return dfp

    def to_domain(self, dto: dict, actor_idx: Dict,  metadata=None) -> Model:

        policies = self.policy_mapper.to_domain(Policy.from_dict(dto['attributes']['policy']), actor_idx, metadata)

        model = Model(
            dto['attributes']['title'],
            dto['attributes']['description'],
            dto['attributes']['tags'],
            policies,
            ModelType.from_str(dto['attributes']['model_type']),
            ModelFormat.from_str(dto['attributes']['model_format']),
            SoftwareTool.from_str(dto['attributes']['environment'])

        )
        model.external_id = int(dto['id'])
        if len(dto['attributes']['content_blobs']) > 0:
            model.set_blob_link(dto['attributes']['content_blobs'][-1]['link'],
                                    dto['attributes']['content_blobs'][-1]['content_type'])
            model.set_checksum(dto['attributes']['content_blobs'][-1]['sha1sum'])

        return model

