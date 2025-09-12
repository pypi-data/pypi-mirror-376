from typing import List, Dict, Set
from collections import Counter

from fairdomseek.types.access.policy import Policy
from fairdomseek.types.attribute import SampleTypeAttribute
from fairdomseek.types.base_types import BaseType, People, Project, Institution, Public


class SampleType(BaseType):

    def __init__(self, title, metadata, description, tags, policies, *args):
        super().__init__(metadata)
        self.title = title
        self.description = description
        self.tags = [tag.strip() for tag in tags]
        self.policies = policies
        self.external_id = None

        if not all(isinstance(attr, SampleTypeAttribute) for attr in args):
            raise TypeError("All positional arguments must be instances of SampleTypeAttribute")

        self.attributes = list(args)


    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SampleType):
            return False

        a = (self.title == other.title and
            self.description == other.description and
            Counter(self.tags) == Counter(other.tags) and
            len(self.attributes) == len(other.attributes) and
            len(self.policies) == len(other.policies))

        # Attribute wise
        attr_cmp = SampleType.compare_attributes(self.attributes, other.attributes)
        a &= (len(attr_cmp["only_self"]) == 0 and len(attr_cmp["only_other"]) == 0 and len(attr_cmp["diff"]) == 0)

        # Policy wise
        plcy_cmp = SampleType.compare_policies(self.policies, other.policies)
        a &= (len(plcy_cmp["only_self"]) == 0 and len(plcy_cmp["only_other"]) == 0 and len(plcy_cmp["diff"]) == 0)

        return a

    def __ne__(self, other):
        return not self.__eq__(other)

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

    @staticmethod
    def compare_attributes(st1: List[SampleTypeAttribute], st2: List[SampleTypeAttribute]) -> Dict[str, Set]:
        # indexing by title
        self_idx = {attr.title: attr for attr in st1}
        other_idx = {attr.title: attr for attr in st2}
        res = {"identity":set(), "only_self": set(), "only_other": set(), "diff": set()}

        # Pick attr one by one from self_idx and ventilate in res
        for k in self_idx:
            if k not in other_idx:
                res["only_self"].add(self_idx[k])
                continue
            if self_idx[k] == other_idx[k]:
                res["identity"].add(self_idx[k])
                del other_idx[k]
                continue
            res["diff"].add(self_idx[k])
            del other_idx[k]

        # remaining key in other only exists in other
        res["only_other"] = set(other_idx.values())

        return res
