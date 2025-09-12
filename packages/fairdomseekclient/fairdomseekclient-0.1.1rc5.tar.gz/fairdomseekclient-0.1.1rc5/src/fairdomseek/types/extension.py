class Extension:

    def __init__(self, title, metadata, my_type, args):
        self.title = title
        self.type = my_type
        self.attributes = args
        metadata._add_object(self)


class AssayExtension(Extension):

    def __init__(self, title, metadata, *args):
        super().__init__(title, metadata, "Assay", args)


class InvestigationExtension:

    def __init__(self, title, metadata, *args):
        super().__init__(title, metadata, "Investigation", args)


class StudyExtension:

    def __init__(self, title, metadata, *args):
        super().__init__(title, metadata, "Study", args)
