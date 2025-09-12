class SampleTypeAttribute:
    def __init__(self, title, description, required, attr_type, is_title=False, unit=None, registered_sample_title=None):
        self.title = title
        self.description = description
        self.required = required
        self.type = attr_type
        self.unit = unit
        self.is_title = is_title
        self.registered_sample_title = registered_sample_title
        self.id = None

    def __eq__(self, other):
        if not isinstance(other, SampleTypeAttribute):
            return False
        return (
            self.title == other.title and
            self.description == other.description and
            self.required == other.required and
            self.type == other.type and
            self.unit == other.unit and
            self.is_title == other.is_title and
            self.registered_sample_title == other.registered_sample_title
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(("SampleTypeAttribute", self.title))


class ExtAttribute:
    def __init__(self, title, label, description, required, attr_type):
        self.title = title
        self.label = label
        self.required = required
        self.type = attr_type
        self.description = description


class AttrType:
    DateTime = "Date time"
    Date = "Date"
    RealNumber = "Real number"
    Integer = "Integer"
    Text = "Text"
    String = "String"
    Boolean = "Boolean"
    CV = "Controlled Vocabulary"
    CVList = "Controlled Vocabulary List"
    SeekDataFile = "Seek Data file"
    LinkedExtendedMetadata = "Linked Extended Metadata"
    LinkedExtendedMetadataMulti = "Linked Extended Metadata (multiple)"
    EmailAddress = "Email address"
    WebLink = "Web link"
    URI = "URI"
    RegisteredDataFile = "Registered Data file"
    RegisteredSample = "Registered Sample"
    RegisteredSampleList = "Registered Sample List"

