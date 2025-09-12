from openapi_client import PermissionResourceTypes


class BaseType:
    def __init__(self, metadata=None):
        self.type = "base"
        if metadata:
            metadata._add_object(self)

    def id(self):
        raise Exception("Must be implemented in subclasses")

    def __eq__(self, other) -> bool:
        return self.type  == other.type

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)


class People(BaseType):

    def __init__(self, metadata, first_name, last_name):
        super().__init__(metadata)
        self.first_name = first_name
        self.last_name = last_name
        self.type = PermissionResourceTypes.PEOPLE


    def id(self):
        return "{} {}".format(self.first_name, self.last_name)

    def __eq__(self, other) -> bool:
        return self.first_name == other.first_name and \
            self.last_name == other.last_name and \
            self.type == other.type

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        return hash(("People", self.first_name +" " + self.last_name))


class Project(BaseType):

    def __init__(self, metadata, title):
        super().__init__(metadata)
        self.title = title
        self.type = PermissionResourceTypes.PROJECTS

    def id(self):
        return "{}".format(self.title)

    def __eq__(self, other) -> bool:
        return self.title == other.title and \
            self.type == other.type

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        return hash(("Project", self.title))


class Institution(BaseType):

    def __init__(self, metadata, title):
        super().__init__(metadata)
        self.title = title
        self.type = PermissionResourceTypes.INSTITUTIONS

    def id(self):
        return "{}".format(self.title)

    def __eq__(self, other) -> bool:
        return self.title == other.title and \
            self.type == other.type

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self):
        return hash(("Institution", self.title))


class Public(BaseType):

    def __init__(self, metadata):
        super().__init__(metadata)
        self.type = "public"

    def id(self):
        return "public"

    def __hash__(self):
        return hash(("Public", ""))

