class Policy:

    MANAGE = "manage"
    EDIT = "edit"
    DOWNLOAD = "download"
    VIEW = "view"
    NO_ACCESS = "no_access"

    def __init__(self, my_type, target):
        self.type = my_type
        self.target = target

    def __eq__(self, other: object) -> bool:
        return self.type == other.type and self.target == other.target

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)
