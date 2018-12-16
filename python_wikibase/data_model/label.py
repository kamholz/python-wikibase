from ..base import Base
from ..utils.exceptions import EditError


class Label(Base):
    def parse(self, entity_id, labels):
        self.entity_id = entity_id
        self.labels = {}
        for lang, lang_value in labels.items():
            self.labels[lang] = lang_value["value"]
        return self

    def get(self, language=None):
        """Get the entity's label in the specified language (or use the entity's default)

        :param language: Language to get the label in
        :type language: str
        :return: Label
        :rtype: str
        """
        if not language:
            language = self.language
        return self.labels[language]

    def set(self, new_label, language=None):
        """Update the entity's label in the specified language (or the entity's default)

        :param new_label: New label to use
        :type new_label: str
        :param language: Language to update the label for
        :type language: str
        """
        if not language:
            language = self.language
        r = self.api.label.set(self.entity_id, new_label, language)
        if (
            "success" not in r
            or "error" in r
            or r["entity"]["labels"][language]["value"] != new_label
        ):
            raise EditError("Could not update label: " + r)
        self.labels[language] = r["entity"]["labels"][language]["value"]