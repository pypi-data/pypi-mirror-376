from typing import Dict
from fairdomseek.translator.translator import Translator
from fairdomseek.types.data import DataFile
from fairdomseek.util.content_type import infer_content_type
from openapi_client import ItemReference, MultipleReferences, \
    DataFilePost, DataFileType, DataFilePostData, DataFilePostDataAttributes, ContentBlobSlot, \
    DataFilePostDataRelationships, ContentBlobPlaceholder, DataFilePatch, DataFilePatchData, \
    DataFilePatchDataAttributes, DataFilePatchDataRelationships, Policy


class DataFileTranslator(Translator):
    def __init__(self, policy_mapper):
        super().__init__(policy_mapper)

    def to_dto(self, datafile: DataFile, project_id: str, policy_dto=None) -> DataFilePost:

        if datafile.file_path is None:
            raise Exception("Can't create DataFile \"{}\": associated data file is not specified".format(datafile.title))
        if not datafile.file_path.exists():
            raise Exception("Can't create DataFile \"{}\": {} doesn't exist".format(datafile.title, datafile.file_path))

        return DataFilePost(data=DataFilePostData(type=DataFileType.DATA_FILES,
                             attributes=DataFilePostDataAttributes(
                                 tags=datafile.tags,
                                 title=datafile.title,
                                 description=datafile.description,
                                 content_blobs=[ContentBlobSlot(
                                     ContentBlobPlaceholder(
                                         original_filename=datafile.file_path.name,
                                         content_type=infer_content_type(datafile.file_path)))
                                 ],
                                 policy=policy_dto
                             ),
                             relationships=DataFilePostDataRelationships(
                                 projects= MultipleReferences(data=[ItemReference(id=project_id, type="projects")]),
                             ))
                           )

    def to_dto_patch(
            self,
            datafile: DataFile,
            project_id: str,
            policies_dto,
    ) -> DataFilePatch:

        # Build and return the patch
        dfp = DataFilePatch(
            data=DataFilePatchData(
                id=str(datafile.external_id),
                type=DataFileType.DATA_FILES,
                attributes=DataFilePatchDataAttributes(
                    tags=datafile.tags,
                    title=datafile.title,
                    description=datafile.description,
                    policy=policies_dto
                ),
                relationships=DataFilePatchDataRelationships(
                    projects= MultipleReferences(data=[ItemReference(id=project_id, type="projects")]),
                ),
            )
        )

        return dfp

    def to_domain(self, dto: dict, actor_idx: Dict,  metadata=None) -> DataFile:

        policies = self.policy_mapper.to_domain(Policy.from_dict(dto['attributes']['policy']), actor_idx, metadata)

        data_file = DataFile(
            dto['attributes']['title'],
            dto['attributes']['description'],
            dto['attributes']['tags'],
            policies,

        )
        data_file.external_id = int(dto['id'])
        if len(dto['attributes']['content_blobs']) > 0:
            data_file.set_blob_link(dto['attributes']['content_blobs'][-1]['link'],
                                    dto['attributes']['content_blobs'][-1]['content_type'])
            data_file.set_checksum(dto['attributes']['content_blobs'][-1]['sha1sum'])

        return data_file

