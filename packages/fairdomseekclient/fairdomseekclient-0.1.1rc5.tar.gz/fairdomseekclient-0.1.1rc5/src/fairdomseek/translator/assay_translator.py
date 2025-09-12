from typing import Dict

from fairdomseek.translator.translator import Translator
from fairdomseek.types.assay import Assay, AssayClass
from openapi_client import AssayPatch, AssayPost, AssayPatchData, AssayType, AssayResponse, AssayPostDataAttributes, \
    AssayPostDataAttributesAssayClass, AssayPostDataAttributesAssayType, SingleReference, AssayPostDataRelationships, \
    ItemReference, MultipleReferences, AssayPostData, AssayPatchDataAttributes, AssayPatchDataRelationships


class AssayTranslator(Translator):
    def __init__(self, policy_mapper):
        super().__init__(policy_mapper)


    def to_dto(self, assay: Assay, policy_dto=None) -> AssayPost:

        samples = [ItemReference(id=str(sp.external_id), type="samples") for sp in assay.ref_samples] \
            if len(assay.ref_samples) > 0 else []
        data = [ItemReference(id=str(df.external_id), type="datafiles") for df in assay.ref_datafiles] \
            if len(assay.ref_datafiles) > 0 else []
        models = [ItemReference(id=str(md.external_id), type="models") for md in assay.ref_models] \
            if len(assay.ref_models) > 0 else []

        return AssayPost(data=AssayPostData(type=AssayType.ASSAYS,
                             attributes=AssayPostDataAttributes(
                                 tags=assay.tags,
                                 title=assay.title,
                                 description=assay.description,
                                 assay_class=AssayPostDataAttributesAssayClass(key=assay.assay_class.value[0]),
                                 assay_type=AssayPostDataAttributesAssayType(uri=assay.assay_class.value[1]),
                                 policy=policy_dto
                             ),
                             relationships=AssayPostDataRelationships(
                                 study=SingleReference(data=ItemReference(id=str(assay.study_id),
                                                                     type="studies")),
                                 samples= MultipleReferences(data=samples),
                                 models = MultipleReferences(data=models),
                                 sops = MultipleReferences(data=[]),
                                 data_files = MultipleReferences(data=data)
                             ))
                           )

    def to_dto_patch(
            self,
            assay: Assay,
            policies_dto,
    ) -> AssayPatch:

        samples = [ItemReference(id=str(sp.external_id), type="samples") for sp in assay.ref_samples] \
            if len(assay.ref_samples) > 0 else []
        data = [ItemReference(id=str(df.external_id), type="datafiles") for df in assay.ref_datafiles] \
            if len(assay.ref_datafiles) > 0 else []
        models = [ItemReference(id=str(md.external_id), type="models") for md in assay.ref_models] \
            if len(assay.ref_models) > 0 else []


        # Build and return the patch
        return AssayPatch(
            data=AssayPatchData(
                id=str(assay.external_id),
                type=AssayType.ASSAYS,
                attributes=AssayPatchDataAttributes(
                    tags=assay.tags,
                    title=assay.title,
                    description=assay.description,
                    assay_class=AssayPostDataAttributesAssayClass(key=assay.assay_class.value[0])
                    if assay.assay_class is not None else None,
                    assay_type=AssayPostDataAttributesAssayType(uri=assay.assay_class.value[1])
                    if assay.assay_class is not None else None,
                    policy=policies_dto
                ),
                relationships=AssayPatchDataRelationships(
                    study=SingleReference(data=ItemReference(id=str(assay.study_id), type="studies"))
                    if assay.study_id is not None else None,
                    samples=MultipleReferences(data=samples),
                    models=MultipleReferences(data=models),
                    sops=MultipleReferences(data=[]),
                    data_files=MultipleReferences(data=data)
                ),
            )
        )


    def to_domain(self, dto: AssayResponse, actor_idx: Dict,  metadata=None) -> Assay:

        policies = self.policy_mapper.to_domain(dto.data.attributes.policy, actor_idx, metadata)

        assay = Assay(
            dto.data.attributes.title,
            dto.data.attributes.description,
            dto.data.attributes.tags,
            AssayClass.from_str(dto.data.attributes.assay_class.title),
            policies,
            None
        )

        assay.study_id = int(dto.data.relationships.study.data.id)
        assay.external_id = int(dto.data.id)

        return assay
