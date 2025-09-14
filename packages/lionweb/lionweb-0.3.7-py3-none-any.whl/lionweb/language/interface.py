import itertools
from typing import TYPE_CHECKING, List, Optional, Set

from lionweb.language.classifier import Classifier


class Interface(Classifier["Interface"]):
    if TYPE_CHECKING:
        from lionweb.language.concept import Concept
        from lionweb.language.feature import Feature
        from lionweb.language.language import Language
        from lionweb.lionweb_version import LionWebVersion
        from lionweb.self.lioncore import LionCore

    def __init__(
        self,
        lion_web_version: Optional["LionWebVersion"] = None,
        language: Optional["Language"] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
        key: Optional[str] = None,
    ):
        from lionweb.lionweb_version import LionWebVersion

        super().__init__(
            lion_web_version=lion_web_version or LionWebVersion.current_version(),
            language=language,
            name=name,
        )
        if id:
            self.set_id(id)
        if key:
            self.set_key(key)

    def get_extended_interfaces(self) -> List["Interface"]:
        return self.get_reference_multiple_value("extends")

    @property
    def extended_interfaces(self) -> List["Interface"]:
        return self.get_extended_interfaces()

    def add_extended_interface(self, extended_interface: "Interface"):
        if not extended_interface:
            raise ValueError("extended_interface should not be null")

        from lionweb.model.classifier_instance_utils import reference_to

        self.add_reference_multiple_value("extends", reference_to(extended_interface))

    def inherited_features(self) -> List["Feature"]:
        from lionweb.language.feature import Feature

        result: List[Feature] = []
        for super_interface in self.all_ancestors():
            self.combine_features(result, super_interface.all_features())
        return result

    def get_classifier(self) -> "Concept":
        from lionweb.self.lioncore import LionCore

        return LionCore.get_interface(self.get_lionweb_version())

    def direct_ancestors(self) -> List[Classifier]:
        return list(itertools.chain(self.get_extended_interfaces()))

    def all_extended_interfaces(self) -> Set["Interface"]:
        to_avoid = {self}
        return self._all_extended_interfaces_helper(to_avoid)

    def _all_extended_interfaces_helper(
        self, to_avoid: Set["Interface"]
    ) -> Set["Interface"]:
        interfaces = set()
        to_avoid.add(self)
        for ei in self.get_extended_interfaces():
            if ei not in interfaces:
                interfaces.add(ei)
            if ei not in to_avoid:
                interfaces.update(ei._all_extended_interfaces_helper(to_avoid))
        return interfaces

    def __repr__(self) -> str:
        return f"Interface({self.get_name()})"
