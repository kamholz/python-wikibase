import json

from wikibase_api import ApiError
from python_wikibase.data_types.data_type import DataType
from python_wikibase.utils.exceptions import ParseError


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
        if isinstance(time, str):
            return self.create_from_string(time)
        else:
            self.time = time
        return self

    def create_from_string(self, timestring, options={}):
        if "lang" not in options:
            options["lang"] = self.language
        params = {
            "action": "wbparsevalue",
            "datatype": "time",
            "values": timestring,
            "options": json.dumps(options)
        }
        try:
            results = self.api.api.get(params)["results"]
        except ApiError as e:
            raise ParseError(f"Could not parse string: {e}") from None
        if len(results) != 1:
            raise ParseError("Parser returned more than one time value")
        self.time = results[0]["value"]
        return self

    def format(self):
        params = {"action": "wbformatvalue", "datavalue": json.dumps({"value": self.time, "type": "time"})}
        return self.api.api.get(params)["result"]

