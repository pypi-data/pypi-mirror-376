from abc import ABC, abstractmethod
from typing import Optional

from lionweb.model.classifier_instance import ClassifierInstance


class HasSettableParent(ABC):
    @abstractmethod
    def set_parent(self, parent: Optional[ClassifierInstance]) -> None: ...
