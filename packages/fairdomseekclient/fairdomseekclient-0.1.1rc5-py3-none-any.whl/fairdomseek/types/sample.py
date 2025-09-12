import logging
from typing import List, Tuple

from fairdomseek.types.access.policy import Policy
from fairdomseek.types.attribute import AttrType
from fairdomseek.types.base_types import BaseType
from fairdomseek.types.data import DataFile
from fairdomseek.types.sample_type import SampleType

LOGGER = logging.getLogger(__name__)

class UndefinedTitle(Exception):
    pass

class Sample(BaseType):

    # sample_title is used here to reference a sample uniquely based on the "title" parameter set
    # on one of the attribute of the sample types
    # The server side code doesn't enforce the unicity of the "title" parameter among the samples,
    # so the user have to take care of this. Side effect of not doing this might lead to reference
    # the wrong sample elsewhere (like in an other sample, or in an assay)
    def __init__(self, sample_type_name: str,
                 sample_title = None,
                 tags: List[str]=None,
                 policies: List[Policy]=None,
                 **kwargs):
        super().__init__()
        self.sample_type_name= sample_type_name
        self.tags = tags
        self.policies = policies
        self.attributes = kwargs
        self.sample_type_id = None
        self.sample_title = sample_title
        self.external_id = None

    def is_instance(self, sample_type: SampleType) -> Tuple[List[str], List[str]]:
        # go over attributes of sample, check againt sample type attributes;
        # no attributes in this sample not belonging to sample type attribute is allowed
        # required attributes MUST be set
        unexisting_attr = []
        missing_attr = []
        st_names = [st_attr.title for st_attr in sample_type.attributes]
        st_required_names = [st_attr.title for st_attr in sample_type.attributes if st_attr.required is True]
        for attr in self.attributes:
            if attr not in st_names:
                unexisting_attr.append(attr)
        for attr in st_required_names:
            if attr not in self.attributes:
                missing_attr.append(attr)

        return unexisting_attr, missing_attr

    def get_title(self, st: SampleType) -> Tuple[str, str]:
        if self.attributes and st and st.attributes:
            for attr in st.attributes:
                if attr.is_title:
                    title_key = attr.title
                    if title_key in self.attributes:
                        return title_key, self.attributes[title_key]
        raise UndefinedTitle()


    def is_valid(self, sample_type: SampleType) -> bool:
        # Sample type attributes preprocessing: for each attribute, check against the sample type reference
        # what is the expected type. If type is Sample or Data file, ensure either a proper Sample or Data object is provided
        # Other types are not supported for now
        st_attributes_types = {st_attr.title: st_attr.type for st_attr in sample_type.attributes}
        is_valid = True
        for attr in self.attributes:
            match st_attributes_types[attr]:
                case AttrType.DateTime| AttrType.Date| AttrType.Text| AttrType.String| AttrType.EmailAddress| \
                    AttrType.WebLink| AttrType.URI:
                    if not isinstance(self.attributes[attr], str):
                        LOGGER.error("{} attribute has not the expected type (string)".format(attr))
                        is_valid = False
                case AttrType.RealNumber| AttrType.Integer:
                    if not isinstance(self.attributes[attr], (int, float)):
                        LOGGER.error("{} attribute has not the expected type (float/int)".format(attr))
                        is_valid = False
                case AttrType.Boolean:
                    if not isinstance(self.attributes[attr], bool):
                        LOGGER.error("{} attribute has not the expected type (boolean)".format(attr))
                        is_valid = False
                case AttrType.RegisteredSample:
                    if not isinstance(self.attributes[attr], Sample):
                        LOGGER.error("{} attribute has not the expected type (Sample)".format(attr))
                        is_valid = False
                case AttrType.RegisteredDataFile:
                    if not isinstance(self.attributes[attr], DataFile):
                        LOGGER.error("{} attribute has not the expected type (DataFile)".format(attr))
                        is_valid = False
                case AttrType.CV| AttrType.CVList| \
            AttrType.SeekDataFile| AttrType.LinkedExtendedMetadata| AttrType.LinkedExtendedMetadataMulti| \
                     AttrType.RegisteredSampleList:
                    LOGGER.error("{} is an unsupported type for attribute {} for a sample".format(st_attributes_types[attr],
                                                                                                  attr))
                    is_valid = False

        return is_valid


class SampleRef:

    def __init__(self, sample_type_name, title):
        self.sample_type_name = sample_type_name
        self.sample_title = title
        self.external_id = None