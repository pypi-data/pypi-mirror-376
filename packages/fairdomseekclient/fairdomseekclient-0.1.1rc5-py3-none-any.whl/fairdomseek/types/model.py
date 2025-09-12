from pathlib import Path
from typing import List, Union, Optional

from fairdomseek.types.base_types import BaseType
from openapi_client import Policy

from enum import Enum

class ModelType(Enum):
    Agent_Based_Modelling = "Agent based modelling"
    Algebraic_Equations = "Algebraic equations"
    Bayesian = "Bayesian network"
    Boolean = "Boolean network"
    Graphical = "Graphical model"
    Linear_Equations = "Linear equations"
    Metabolic_Network = "Metabolic network"
    ODE = "Ordinary differential equations (ODE)"
    PDE = "Partial differential equations (PDE)"
    Petri = "Petri net"
    Stoichiometric = "Stoichiometric model"

    @classmethod
    def from_str(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        return None


class ModelFormat(Enum):
    BioPAX = "BioPAX"
    CellML = "CellML"
    Copasi = "Copasi"
    FieldML = "FieldML"
    GraphML = "GraphML"
    Image = "Image"
    KGML = "KGML"
    Mathematica = "Mathematica"
    MathML = "MathML"
    Matlab = "Matlab package"
    MFAML = "MFAML"
    PDF = "PDF (Model description)"
    Python = "Python code"
    R = "R package"
    SBGN_ML_PD = "SBGN-ML PD"
    SBML = "SBML"
    SciLab = "SciLab"
    Simile = "Simile XML v3"
    SVG = "SVG"
    SXML = "SXML"
    VCML = "Virtual Cell Markup Language (VCML)"
    XGMML = "XGMML"
    XPP = "XPP"

    @classmethod
    def from_str(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        return None


class SoftwareTool(Enum):
    AUTO2000 = "AUTO2000"
    CellDesigner = "CellDesigner (SBML ODE Solver)"
    CellNetAnalyzer = "CellNetAnalyzer"
    CellSys = "CellSys"
    Copasi = "Copasi"
    CPLEX = "CPLEX Interactive Optimizer"
    FLAME = "FLAME"
    Gromacs = "Gromacs"
    Insilico_Discovery = "Insilico Discovery"
    JADE = "JADE"
    Jarnac = "Jarnac (Systems Biology Workbench)"
    JWS_Online = "JWS Online"
    Mathematica = "Mathematica"
    Matlab = "Matlab"
    MeVisLab = "MeVisLab"
    MoBi = "MoBi"
    PathwayLab = "PathwayLab"
    PKSim = "PK-Sim"
    PottersWheel = "PottersWheel"
    PySCeS = "Python Simulator for Cellular Systems (PySCeS)"
    Roadrunner = "roadrunner (Systems Biology Workbench)"
    SBTOOLBOX2 = "Systems Biology Toolbox 2"
    VCELL = "Virtual Cell"
    XPPAUT = "XPP-Aut"

    @classmethod
    def from_str(cls, value: str):
        for member in cls:
            if member.value == value:
                return member
        return None



class Model(BaseType):

    def __init__(self, title: str, description:str, tags: List[str],
                 policies: List[Policy], mdl_type: Optional[ModelType] ,
                 mdl_format: Optional[ModelFormat], environment: Optional[SoftwareTool]):
        super().__init__(None)
        self.title = title
        self.description = description
        self.tags= tags
        self.policies = policies
        self.model_type = mdl_type
        self.model_format = mdl_format
        self.environment = environment
        self.external_id = None
        self.__blob_link = None
        self.__blob_content_type = None
        self.file_path = None
        self.__blob_sha1sum = None

    def set_blob_link(self, link, content_type):
        self.__blob_link = link
        self.__blob_content_type = content_type

    def set_model_path(self, file_path: Union[Path, str]):
        if isinstance(file_path, str):
            self.file_path = Path(file_path)
        else:
            self.file_path = file_path

    def has_blob_link(self):
        return self.__blob_link is not None

    def get_blob_link(self):
        return self.__blob_link

    def set_checksum(self, checksum):
        self.__blob_sha1sum = checksum

    def get_checksum(self):
        return self.__blob_sha1sum


class ModelRef:

    def __init__(self, title):
        self.title = title
        self.external_id = None