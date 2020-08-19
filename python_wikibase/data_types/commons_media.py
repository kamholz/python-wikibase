from python_wikibase.data_types.data_type import DataType


class CommonsMedia(DataType):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.commons_media = None

    def __str__(self):
        return self.commons_media

    def unmarshal(self, data_value):
        self.commons_media = data_value["value"]
        return self

    def marshal(self):
        return self.commons_media

    def create(self, commons_media):
        self.commons_media = commons_media
        return self
