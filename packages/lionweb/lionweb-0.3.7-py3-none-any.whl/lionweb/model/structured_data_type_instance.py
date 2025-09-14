from abc import ABC, abstractmethod
from typing import Any, Optional

from lionweb.language.field import Field
from lionweb.language.structured_data_type import StructuredDataType


class StructuredDataTypeInstance(ABC):
    """This represents an instance of Structured Data Type."""

    @abstractmethod
    def get_structured_data_type(self) -> StructuredDataType:
        """The StructuredDataType of which this StructuredDataTypeInstance is an instance."""
        ...

    @abstractmethod
    def get_field_value(self, field: Field) -> Optional[Any]:
        """Get the field value associated with the specified field."""
        ...

    @abstractmethod
    def set_field_value(self, field: Field, value: Optional[Any]) -> None:
        """Set the field value for the specified field.

        Raises:
            ValueError: If the value is not compatible with the field type.
        """
        ...
