from typing import List, Optional

from lionweb.api.classifier_instance_resolver import ClassifierInstanceResolver
from lionweb.model import ClassifierInstance


class CompositeClassifierInstanceResolver(ClassifierInstanceResolver):
    def __init__(self, *classifier_instance_resolvers: ClassifierInstanceResolver):
        self.classifier_instance_resolvers: List[ClassifierInstanceResolver] = list(
            classifier_instance_resolvers
        )

    def add(
        self, classifier_instance_resolver: ClassifierInstanceResolver
    ) -> "CompositeClassifierInstanceResolver":
        self.classifier_instance_resolvers.append(classifier_instance_resolver)
        return self

    def resolve(self, instance_id: str) -> Optional[ClassifierInstance]:
        for resolver in self.classifier_instance_resolvers:
            instance = resolver.resolve(instance_id)
            if instance is not None:
                return instance
        return None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.classifier_instance_resolvers!r})"

    __str__ = __repr__
