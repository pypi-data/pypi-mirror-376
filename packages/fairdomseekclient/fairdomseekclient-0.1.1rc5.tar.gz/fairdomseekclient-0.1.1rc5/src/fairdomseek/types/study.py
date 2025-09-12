from typing import List, Dict, Set

from fairdomseek.types.access.policy import Policy
from fairdomseek.types.base_types import BaseType, People, Institution, Project, Public
from fairdomseek.types.investigation import Investigation


class Study(BaseType):

    def __init__(self, title, metadata, description, policies, investigation=None):
        super().__init__(metadata)
        self.title = title
        self.description = description
        self.policies = policies
        self.investigation = investigation
        self.external_id = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Study):
            return False

        a = (self.title == other.title and
            self.description == other.description and
            len(self.policies) == len(other.policies))

        # Policy wise
        plcy_cmp = Study.compare_policies(self.policies, other.policies)
        a &= (len(plcy_cmp["only_self"]) == 0 and len(plcy_cmp["only_other"]) == 0 and len(plcy_cmp["diff"]) == 0)

        # Investigation wise
        if self.investigation is not None and other.investigation is not None:
            a &= (self.investigation.title == other.investigation.title)

        if (self.investigation is None) != (other.investigation is None):
            return False

        return a

    def __ne__(self, other):
        return not self.__eq__(other)

    def set_investigation(self, iv: Investigation):
        self.investigation = iv

    @staticmethod
    def compare_policies(p1: List[Policy], p2: List[Policy]) -> Dict[str, Set]:
        res = {"identity": set(), "only_self": set(), "only_other": set(), "diff": set()}

        def index(policies: List[Policy]) -> Dict[str, Dict]:
            idx = {"people": {}, "institutions": {}, "projects": {}, "public": {}}
            for p in policies:
                match p.target:
                    case People():
                        idx["people"][p.target] = p
                    case Institution():
                        idx["institutions"][p.target] = p
                    case Project():
                        idx["projects"][p.target] = p
                    case Public():
                        idx["public"][p.target] = p
            return idx

        p1_idx = index(p1)
        p2_idx = index(p2)

        for category in p1_idx.keys():
            targets1 = p1_idx[category]
            targets2 = p2_idx[category]

            all_targets = set(targets1.keys()) | set(targets2.keys())

            for target in all_targets:
                policy1 = targets1.get(target)
                policy2 = targets2.get(target)

                if policy1 and policy2:
                    if policy1.type == policy2.type:
                        res["identity"].add(target)
                    else:
                        res["diff"].add(target)
                elif policy1:
                    res["only_self"].add(target)
                elif policy2:
                    res["only_other"].add(target)

        return res
