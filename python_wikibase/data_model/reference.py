from wikibase_api import ApiError

from python_wikibase.base import Base
from python_wikibase.data_model.entity import check_prop_param
from python_wikibase.data_types.data_type import check_data_type, unmarshal_data_value, marshal_data_type
from python_wikibase.utils.data_types import class_to_data_type, class_to_type
from python_wikibase.utils.exceptions import EditError


class References(Base):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.claim_id = None
        self.references = {}

    def __getitem__(self, index):
        return self.to_list()[index]

    def __iter__(self):
        return iter(self.to_list())

    def __len__(self):
        return len(self.to_list())

    def _add_locally(self, reference):
        """Save a newly created reference in the local collection

        :param reference: Reference to add locally
        :type reference: Reference
        """
        prop_id = reference.main_property.entity_id
        if prop_id in self.references:
            self.references[prop_id].append(reference)
        else:
            self.references[prop_id] = [reference]

    def _create(self, prop, value, snak_type):
        """Create the reference using the Wikibase API and save it in the local collection

        :param prop: Property of the new reference
        :type prop: Property
        :param value: Value of the new reference
        :type value: Value
        :param snak_type: Value type (one of ``["value", "novalue", "somevalue"]``)
        :type snak_type: str
        :return: New reference
        :rtype: Reference
        """
        # Create reference using API
        try:
            r = self.api.reference.add(self.claim_id, prop.entity_id, marshal_reference_value(value), marshal_data_type(value), snak_type=snak_type)
        except ApiError as e:
            raise EditError(f"Could not create reference: {e}") from None

        # Save reference in local collection
        new_reference = self.py_wb.Reference().unmarshal(self.claim_id, r["reference"])
        self._add_locally(new_reference)
        return new_reference

    def unmarshal(self, claim_id, references):
        """Parse API response and fill object with the provided information

        :param claim_id: ID of the claim holding the references
        :type claim_id: str
        :param references: Dict of references provided by the Wikibase API
        :type references: dict
        :return self
        :rtype References
        """
        # Save claim ID for API calls
        self.claim_id = claim_id

        # Wikibase API returns references as list
        # Loop over the references add create a Reference object for each of them, then add them to
        # the local collection
        for reference_dict in references:
            reference = self.py_wb.Reference().unmarshal(self.claim_id, reference_dict)
            self._add_locally(reference)
        return self

    def add(self, prop, value):
        """Create a new reference with the specified prop and value

        :param prop: Property of the new reference
        :type prop: Property
        :param value: Value of the new reference
        :type value: Value
        :return: New reference
        :rtype: Reference
        """
        check_prop_param(prop)
        check_data_type(value, prop)
        return self._create(prop, value, "value")

    def add_no_value(self, prop):
        """Create a new reference with the specified prop and no value

        :param prop: Property of the new reference
        :type prop: Property
        :return: New reference
        :rtype: Reference
        """
        check_prop_param(prop)
        return self._create(prop, None, "novalue")

    def add_some_value(self, prop):
        """Create a new reference with the specified prop and an unspecified value

        :param prop: Property of the new reference
        :type prop: Property
        :return: New reference
        :rtype: Reference
        """
        check_prop_param(prop)
        return self._create(prop, None, "somevalue")

    def remove(self, reference):
        """Delete the provided reference

        :param reference: Reference to delete
        :type reference: Reference
        :return: self
        :rtype: References
        """
        check_reference_param(reference)

        # Delete reference using API
        try:
            self.api.reference.remove(reference.claim_id, reference.reference_id)
        except ApiError as e:
            raise EditError(f"Could not remove reference: {e}") from None

        # Remove reference from local collection
        prop_id = reference.main_property.entity_id
        self.references[prop_id] = [
            c for c in self.references[prop_id] if not c.reference_id == reference.reference_id
        ]
        if len(self.references[prop_id]) == 0:
            del self.references[prop_id]

        return self

    def to_dict(self):
        """Return the collection of references as a dict

        :return: Dict of references
        :rtype: dict
        """
        return self.references

    def to_list(self):
        """Return the collection of references as a list

        :return: List of references
        :rtype: list
        """
        reference_list = []
        [reference_list.extend(references) for prop, references in self.references.items()]
        return reference_list


class Reference(Base):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.reference_id = None
        self.claim_id = None
        self.main_property = None
        self.reference_claims = []

    def _create_claim(self, reference_claim, index):
        if not index:
            index = len(self.reference_claims)
        self.reference_claims.insert(index, reference_claim)
        self._update()

    def _update(self, index=None):
        snaks = []
        for reference_claim in self.reference_claims:
            snak = {
                "property": reference_claim.property.entity_id,
                "datavalue": marshal_reference_value(reference_claim.value),
                "snaktype": reference_claim.snak_type
            }
            data_type = marshal_data_type(reference_claim.value)
            if data_type:
                snak["datatype"] = data_type
            snaks.append(snak)

        self.api.reference.update(
            self.claim_id,
            self.reference_id,
            snaks,
            index
        )

    def unmarshal(self, claim_id, reference_data):
        """Parse API response and fill object with the provided information

        :param claim_id: ID of the claim holding the reference
        :type claim_id: str
        :param reference_data: Data about the reference provided by the Wikibase API
        :type reference_data: dict
        """
        self.reference_id = reference_data["hash"]
        self.claim_id = claim_id
        self.main_property = self.py_wb.Property()
        self.main_property.entity_id = reference_data["snaks-order"][0]

        for prop_id in reference_data["snaks-order"]:
            for snak in reference_data["snaks"][prop_id]:
                reference_claim = self.py_wb.ReferenceClaim().unmarshal(snak)
                self.reference_claims.append(reference_claim)
        return self

    def add(self, prop, value, index=None):
        check_prop_param(prop)
        check_data_type(value, prop)
        reference_claim = self.py_wb.ReferenceClaim()
        reference_claim.property = prop
        reference_claim.value = value
        reference_claim.snak_type = "value"
        self._create_claim(reference_claim, index)

    def add_no_value(self, prop, index=None):
        check_prop_param(prop)
        reference_claim = self.py_wb.ReferenceClaim()
        reference_claim.property = prop
        reference_claim.snak_type = "novalue"
        self._create_claim(reference_claim, index)

    def add_some_value(self, prop, index=None):
        check_prop_param(prop)
        reference_claim = self.py_wb.ReferenceClaim()
        reference_claim.property = prop
        reference_claim.snak_type = "somevalue"
        self._create_claim(reference_claim, index)

    def remove(self, reference_claim):
        self.reference_claims = [x for x in self.reference_claims if x != reference_claim]
        self._update()

    def set_value(self, reference_claim, value):
        check_data_type(value, reference_claim.property)
        try:
            reference_claim._update_locally(value, "value")
            self._update()
        except ApiError as e:
            raise EditError(f"Could not update reference value: {e}") from None

    def set_no_value(self, reference_claim):
        try:
            reference_claim._update_locally(None, "novalue")
            self._update()
        except ApiError as e:
            raise EditError(f"Could not update reference value: {e}") from None

    def set_some_value(self, reference_claim):
        try:
            reference_claim._update_locally(None, "somevalue")
            self._update()
        except ApiError as e:
            raise EditError(f"Could not update reference value: {e}") from None


class ReferenceClaim(Base):
    def __init__(self, py_wb, api, language):
        super().__init__(py_wb, api, language)
        self.property = None
        self.snak_type = None
        self.value = None

    def _update_locally(self, value, snak_type):
        self.value = value
        self.snak_type = snak_type

    def unmarshal(self, snak):
        """Parse API response and fill object with the provided information

        :param snak: Data about the reference provided by the Wikibase API
        :type snak: dict
        """
        self.property = self.py_wb.Property()
        self.property.entity_id = snak["property"]

        # Parse snak type and value (if snak type is "value")
        self.snak_type = snak["snaktype"]
        if self.snak_type == "value":
            self.value = unmarshal_data_value(self.py_wb, snak)
            self.property.data_type = self.value.__class__.__name__
        return self


def check_reference_param(prop, param_name="reference"):
    if not isinstance(prop, Reference):
        raise ValueError(f"{param_name} parameter must be instance of Reference class")


def marshal_reference_value(value):
    if value:
        value_class = value.__class__.__name__
        if value_class in {"Item", "Property"}:
            return {
                "type": class_to_type[value_class],
                "value": {"id": value.entity_id}
            }
        else:
            return {
                "type": class_to_type[value_class],
                "value": value.marshal(),
            }
    else:
        return None
