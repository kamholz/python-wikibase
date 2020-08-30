from python_wikibase.data_types.data_type import DataType


class GeoShape(DataType):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.geo_shape = None

    def __str__(self):
        return self.geo_shape

    def unmarshal(self, data_value):
        self.geo_shape = data_value["value"]
        return self

    def marshal(self):
        return self.geo_shape

    def create(self, time):
        self.geo_shape = geo_shape
        return self
