from typing import TYPE_CHECKING, Generic, Optional, TypeVar, cast

from lionweb.language.ikeyed import IKeyed
from lionweb.language.namespace_provider import NamespaceProvider
from lionweb.language.namespaced_entity import NamespacedEntity
from lionweb.lionweb_version import LionWebVersion
from lionweb.model.impl.m3node import M3Node

T = TypeVar("T", bound="M3Node")


class Feature(M3Node[T], NamespacedEntity, IKeyed[T], Generic[T]):
    if TYPE_CHECKING:
        from lionweb.language.classifier import Classifier
        from lionweb.language.language import Language

    def __init__(
        self,
        lion_web_version: Optional[LionWebVersion] = None,
        name: Optional[str] = None,
        container: Optional["Classifier"] = None,
        id: Optional[str] = None,
    ):
        from lionweb.language.classifier import Classifier

        if container and not isinstance(container, Classifier):
            raise ValueError(f"Invalid parameter container received: {container}")
        if container and container.get_lionweb_version():
            lion_web_version = container.get_lionweb_version()
        else:
            lion_web_version = lion_web_version or LionWebVersion.current_version()

        super().__init__(lion_web_version)
        self.set_optional(False)

        self.set_id(id)
        # TODO enforce uniqueness of the name within the FeaturesContainer
        self.set_name(name)
        self.set_parent(container)

    def is_optional(self) -> bool:
        return cast(
            bool, self.get_property_value(property="optional", default_value=False)
        )

    def is_required(self) -> bool:
        return not self.is_optional()

    @property
    def optional(self) -> bool:
        return self.is_optional()

    @property
    def required(self) -> bool:
        return self.is_required()

    def set_optional(self, optional: bool) -> T:
        self.set_property_value(property="optional", value=optional)
        return cast(T, self)

    def get_name(self) -> Optional[str]:
        return cast(str, self.get_property_value(property="name"))

    def set_name(self, name: Optional[str]):
        self.set_property_value(property="name", value=name)

    @property
    def name(self) -> Optional[str]:
        return self.get_name()

    def get_container(self) -> Optional["Classifier"]:
        from lionweb.language.classifier import Classifier

        parent = self.get_parent()
        if parent is None:
            return None
        if isinstance(parent, NamespaceProvider):
            return cast(Classifier, parent)
        raise ValueError("The parent is not a NamespaceProvider")

    def get_key(self) -> str:
        return cast(str, self.get_property_value(property="key"))

    def set_key(self, key: str) -> T:
        self.set_property_value(property="key", value=key)
        return cast(T, self)

    @property
    def key(self):
        return cast(str, self.get_property_value(property="key"))

    @key.setter
    def key(self, new_value):
        self.set_property_value(property="key", value=new_value)

    def get_declaring_language(self) -> "Language":
        container = self.get_container()
        if container:
            from lionweb.language.language import Language

            return cast(Language, container.get_container())
        else:
            raise ValueError(
                f"Feature {self} is not a language. Its container is {container} and that is not in a language"
            )
