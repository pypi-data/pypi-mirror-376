from enum import Enum
from typing import List, Union

from fairdomseek.types.access.policy import Policy
from fairdomseek.types.base_types import BaseType
from fairdomseek.types.data import DataFile, DataFileRef
from fairdomseek.types.model import Model, ModelRef
from fairdomseek.types.sample import Sample, SampleRef
from fairdomseek.types.sop import SOP


class AssayClass(Enum):
    MODEL = ("MODEL", "http://jermontology.org/ontology/JERMOntology#Model_analysis_type")
    EXPERIMENT = ("EXP", "http://jermontology.org/ontology/JERMOntology#Experimental_assay_type")

    @classmethod
    def from_str(cls, assay_name: str):
        match assay_name:
            case "Experimental assay":
                return AssayClass.EXPERIMENT
            case "Modelling assay":
                return AssayClass.MODEL
        # Default
        return AssayClass.MODEL


class Assay(BaseType):

    def __init__(self, title: str,
                 *args: Union[SampleRef, ModelRef, DataFileRef],
                 description: str = None,
                 tags: List[str] = None,
                 assay_class: AssayClass = None,
                 policies: List[Policy] = None,
                 study_name: str = None):

        super().__init__(None)
        self.title = title
        self.description = description
        self.tags = tags
        self.assay_class = assay_class
        self.policies = policies

        # Don't maintain full domain ref here, only name and id
        self.study_name = study_name
        self.study_id = None
        self.external_id = None

        # References hodler
        self.ref_samples = []
        self.ref_models = []
        self.ref_datafiles = []
        self.ref_sop = []

        for arg in list(args):
            if isinstance(arg, SampleRef):
                self.add_sample(arg)
            if isinstance(arg, ModelRef):
                self.add_model(arg)
            if isinstance(arg, DataFileRef):
                self.add_data_files(arg)

    def add_data_files(self, data: DataFileRef):
        self.ref_datafiles.append(data)

    def add_sample(self, sample: SampleRef):
        self.ref_samples.append(sample)

    def add_model(self, model: ModelRef):
        self.ref_models.append(model)

    def add_sop(self, sop: SOP):
        raise Exception("Must be implemented")
