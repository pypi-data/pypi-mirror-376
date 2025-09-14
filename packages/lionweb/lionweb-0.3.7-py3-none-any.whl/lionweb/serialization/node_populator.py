from typing import TYPE_CHECKING, cast

from lionweb.api.classifier_instance_resolver import ClassifierInstanceResolver
from lionweb.language.lioncore_builtins import LionCoreBuiltins
from lionweb.lionweb_version import LionWebVersion
from lionweb.model import ClassifierInstance, Node
from lionweb.model.reference_value import ReferenceValue
from lionweb.self.lioncore import LionCore
from lionweb.serialization.data.serialized_classifier_instance import \
    SerializedClassifierInstance
from lionweb.serialization.deserialization_exception import \
    DeserializationException
from lionweb.serialization.deserialization_status import DeserializationStatus
from lionweb.serialization.unavailable_node_policy import UnavailableNodePolicy
from lionweb.utils.autoresolve import (LIONCORE_AUTORESOLVE_PREFIX,
                                       LIONCOREBUILTINS_AUTORESOLVE_PREFIX)


class NodePopulator:
    if TYPE_CHECKING:
        from lionweb.serialization.abstract_serialization import \
            AbstractSerialization

    def __init__(
        self,
        serialization: "AbstractSerialization",
        classifier_instance_resolver: ClassifierInstanceResolver,
        deserialization_status: DeserializationStatus,
        auto_resolve_version: LionWebVersion = LionWebVersion.current_version(),
    ):
        from lionweb.serialization.abstract_serialization import \
            AbstractSerialization

        self.serialization: AbstractSerialization = serialization
        self.classifier_instance_resolver = classifier_instance_resolver
        self.deserialization_status = deserialization_status
        self.auto_resolve_map = {}

        lion_core_builtins = LionCoreBuiltins.get_instance(auto_resolve_version)
        for element in lion_core_builtins.get_elements():
            self.auto_resolve_map[
                f"{LIONCOREBUILTINS_AUTORESOLVE_PREFIX}{element.get_name()}"
            ] = element

        lion_core = LionCore.get_instance(auto_resolve_version)
        for element in lion_core.get_elements():
            self.auto_resolve_map[
                f"{LIONCORE_AUTORESOLVE_PREFIX}{element.get_name()}"
            ] = element

    def populate_classifier_instance(
        self,
        node: ClassifierInstance,
        serialized_classifier_instance: SerializedClassifierInstance,
    ) -> None:
        self.populate_containments(node, serialized_classifier_instance)
        self.populate_node_references(node, serialized_classifier_instance)

    def populate_containments(
        self,
        node: ClassifierInstance,
        serialized_classifier_instance: SerializedClassifierInstance,
    ) -> None:
        concept = node.get_classifier()
        for (
            serialized_containment_value
        ) in serialized_classifier_instance.get_containments():
            containment = concept.get_containment_by_meta_pointer(
                serialized_containment_value.meta_pointer
            )
            if containment is None:
                raise ValueError(
                    f"Unable to resolve containment {serialized_containment_value.meta_pointer} in concept {concept}"
                )

            if serialized_containment_value.children_ids is None:
                raise ValueError("The containment value should not be null")

            deserialized_value = []
            for child_node_id in serialized_containment_value.children_ids:
                if (
                    self.serialization.unavailable_children_policy
                    == UnavailableNodePolicy.PROXY_NODES
                ):
                    deserialized_value.append(
                        self.classifier_instance_resolver.resolve_or_proxy(
                            child_node_id
                        )
                    )
                else:
                    deserialized_value.append(
                        self.classifier_instance_resolver.strictly_resolve(
                            child_node_id
                        )
                    )

            if deserialized_value != node.get_children(containment):
                for child in deserialized_value:
                    node.add_child(containment, cast(Node, child))

    def populate_node_references(
        self,
        node: ClassifierInstance,
        serialized_classifier_instance: SerializedClassifierInstance,
    ) -> None:
        concept = node.get_classifier()
        for serialized_reference_value in serialized_classifier_instance.references:
            reference = concept.get_reference_by_meta_pointer(
                serialized_reference_value.meta_pointer
            )
            if reference is None:
                raise ValueError(
                    f"Unable to resolve reference {serialized_reference_value.meta_pointer}. Concept {concept}. SerializedNode {serialized_classifier_instance}"
                )

            for entry in serialized_reference_value.value:
                referred = (
                    self.classifier_instance_resolver.resolve(entry.reference)
                    if entry.reference
                    else None
                )

                if referred is None and entry.reference:
                    if (
                        self.serialization.unavailable_reference_target_policy
                        == UnavailableNodePolicy.NULL_REFERENCES
                    ):
                        referred = None
                    elif (
                        self.serialization.unavailable_reference_target_policy
                        == UnavailableNodePolicy.PROXY_NODES
                    ):
                        referred = self.deserialization_status.resolve(entry.reference)
                    elif (
                        self.serialization.unavailable_reference_target_policy
                        == UnavailableNodePolicy.THROW_ERROR
                    ):
                        raise DeserializationException(
                            f"Unable to resolve reference to {entry.reference} for feature {serialized_reference_value.meta_pointer}"
                        )

                if referred is None and entry.resolve_info:
                    referred = self.auto_resolve_map.get(entry.resolve_info)

                reference_value = ReferenceValue(
                    referred=cast(ClassifierInstance, referred),
                    resolve_info=entry.resolve_info,
                )
                node.add_reference_value(reference, reference_value)
