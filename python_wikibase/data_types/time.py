from python_wikibase.data_types.data_type import DataType


class Time(DataType):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.time = None

    def __str__(self):
        return self.time

    def unmarshal(self, data_value):
        self.time = data_value["value"]
        return self

    def marshal(self):
        return self.time

    def create(self, time):
        self.time = time
        return self
