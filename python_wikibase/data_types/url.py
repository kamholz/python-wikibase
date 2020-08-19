from python_wikibase.data_types.data_type import DataType


class Url(DataType):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.url = None

    def __str__(self):
        return self.url

    def unmarshal(self, data_value):
        self.url = data_value["value"]
        return self

    def marshal(self):
        return self.url

    def create(self, url):
        self.url = url
        return self
