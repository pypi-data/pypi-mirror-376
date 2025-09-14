from typing import Optional, TypeVar, cast

from lionweb.language.debug_utils import DebugUtils
from lionweb.language.ikeyed import IKeyed
from lionweb.language.language import Language
from lionweb.language.namespace_provider import NamespaceProvider
from lionweb.language.namespaced_entity import NamespacedEntity
from lionweb.lionweb_version import LionWebVersion
from lionweb.model.impl.m3node import M3Node

T = TypeVar("T", bound=M3Node)


class LanguageEntity(M3Node[T], NamespacedEntity, IKeyed[T]):
    def __init__(
        self,
        lion_web_version: Optional["LionWebVersion"] = None,
        language: Optional[Language] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ):
        if language and not isinstance(language, Language):
            raise ValueError()
        super().__init__(lion_web_version or LionWebVersion.current_version())
        self.set_name(name)

        if id:
            self.set_id(id)

        if language:
            if (
                lion_web_version or LionWebVersion.current_version()
            ) != language.get_lionweb_version():
                raise ValueError(
                    "The specified lionWebVersion is not the same as the LionWebVersion of the language"
                )
            language.add_element(self)
        else:
            self.set_parent(None)

    @property
    def language(self) -> Optional[Language]:
        parent = self.get_parent()
        if parent is None:
            return None
        if isinstance(parent, Language):
            return parent
        raise ValueError("The parent of this LanguageEntity is not a Language")

    def get_name(self) -> Optional[str]:
        return cast(Optional[str], self.get_property_value(property="name"))

    def set_name(self, name: Optional[str]) -> T:
        self.set_property_value(property="name", value=name)
        return cast(T, self)

    @property
    def name(self) -> Optional[str]:
        return self.get_name()

    @name.setter
    def name(self, new_value):
        self.set_name(new_value)

    def get_container(self) -> Optional[NamespaceProvider]:
        parent = self.get_parent()
        if parent is None:
            return None
        if isinstance(parent, NamespaceProvider):
            return parent
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

    def __str__(self) -> str:
        return f"{super().__str__()}{{qualifiedName={DebugUtils.qualified_name(self)}}}"
