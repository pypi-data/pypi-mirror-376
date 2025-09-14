from dataclasses import dataclass, field
from typing import List, Optional

from lionweb.serialization.data.metapointer import MetaPointer
from lionweb.serialization.data.serialized_containment_value import \
    SerializedContainmentValue
from lionweb.serialization.data.serialized_property_value import \
    SerializedPropertyValue
from lionweb.serialization.data.serialized_reference_value import (
    SerializedReferenceValue, SerializedReferenceValueEntry)


@dataclass
class SerializedClassifierInstance:
    id: Optional[str]
    classifier: MetaPointer
    properties: List[SerializedPropertyValue] = field(default_factory=list)
    containments: List[SerializedContainmentValue] = field(default_factory=list)
    references: List[SerializedReferenceValue] = field(default_factory=list)
    annotations: List[Optional[str]] = field(default_factory=list)
    parent_node_id: Optional[str] = None

    def get_parent_node_id(self):
        return self.parent_node_id

    def set_parent_node_id(self, parent_node_id: Optional[str]):
        self.parent_node_id = parent_node_id

    def get_containments(self):
        return list(self.containments)

    def get_children(self):
        children = []
        for containment in self.containments:
            children.extend(containment.get_children_ids())
        return list(children)

    def add_property_value(self, property_value: SerializedPropertyValue):
        self.properties.append(property_value)

    def add_containment_value(self, containment_value: SerializedContainmentValue):
        self.containments.append(containment_value)

    def add_reference_value(self, reference_value: SerializedReferenceValue):
        self.references.append(reference_value)

    def get_classifier(self) -> MetaPointer:
        return self.classifier

    def set_classifier(self, classifier: MetaPointer):
        self.classifier = classifier

    def set_property_value(self, property_meta_pointer, serialized_value):
        from .serialized_property_value import SerializedPropertyValue

        self.properties.append(
            SerializedPropertyValue(property_meta_pointer, serialized_value)
        )

    def add_children(
        self, containment_meta_pointer: MetaPointer, children_ids: List[Optional[str]]
    ):
        from .serialized_containment_value import SerializedContainmentValue

        self.containments.append(
            SerializedContainmentValue(containment_meta_pointer, children_ids)
        )

    def add_reference_value_entries(
        self, reference_meta_pointer, reference_values: List
    ):
        from .serialized_reference_value import SerializedReferenceValue

        self.references.append(
            SerializedReferenceValue(reference_meta_pointer, reference_values)
        )

    def get_property_value_by_key(self, property_key: str) -> Optional[str]:
        for pv in self.properties:
            mp = pv.get_meta_pointer()
            if mp:
                if mp.key == property_key:
                    return pv.get_value()
        return None

    def get_property_value(self, property_meta_pointer) -> Optional[str]:
        for pv in self.properties:
            if property_meta_pointer == pv.get_meta_pointer():
                return pv.get_value()
        return None

    def get_reference_values_by_key(
        self, reference_key: str
    ) -> Optional[List[SerializedReferenceValueEntry]]:
        for rv in self.references:
            if rv.get_meta_pointer().key == reference_key:
                return rv.get_value()
        return None

    def get_reference_values(self, reference_meta_pointer) -> List:
        for rv in self.references:
            if reference_meta_pointer == rv.get_meta_pointer():
                return rv.get_value()
        return []

    def get_containment_values_by_key(
        self, containment_key: str
    ) -> List[Optional[str]]:
        for rv in self.containments:
            if rv.get_meta_pointer().key == containment_key:
                return rv.get_children_ids()
        return []

    def get_containment_values(
        self, containment_meta_pointer: MetaPointer
    ) -> List[Optional[str]]:
        for cv in self.containments:
            if containment_meta_pointer == cv.get_meta_pointer():
                return cv.get_children_ids()
        return []

    def set_annotations(self, annotation_ids: List[Optional[str]]):
        self.annotations = annotation_ids[:]

    def add_annotation(self, annotation_id: Optional[str]):
        self.annotations.append(annotation_id)

    def __eq__(self, other):
        if not isinstance(other, SerializedClassifierInstance):
            return False
        return (
            self.id == other.id
            and self.classifier == other.classifier
            and self.parent_node_id == other.parent_node_id
            and self.properties == other.properties
            and self.containments == other.containments
            and self.references == other.references
            and self.annotations == other.annotations
        )

    def __hash__(self):
        return hash(
            (
                self.id,
                self.classifier,
                self.parent_node_id,
                tuple(self.properties),
                tuple(self.containments),
                tuple(self.references),
                tuple(self.annotations),
            )
        )

    def __str__(self):
        return (
            f"SerializedClassifierInstance{{id='{self.id}', classifier={self.classifier}, "
            f"parent_node_id='{self.parent_node_id}', properties={self.properties}, "
            f"containments={self.containments}, references={self.references}, "
            f"annotations={self.annotations}}}"
        )
