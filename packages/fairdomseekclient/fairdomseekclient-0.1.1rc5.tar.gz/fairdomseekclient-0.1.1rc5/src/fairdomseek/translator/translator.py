from typing import List

from fairdomseek.types.access.policy import Policy


class Translator:

    def __init__(self, policy_mapper):
        self.policy_mapper = policy_mapper

    def get_actors_from_policies(self, policies: List[Policy]):
        return self.policy_mapper.get_actors_from_policies(policies) if policies is not None else []
