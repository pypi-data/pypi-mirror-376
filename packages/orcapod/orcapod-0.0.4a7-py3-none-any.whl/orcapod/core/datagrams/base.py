"""
Data structures and utilities for working with datagrams in OrcaPod.

This module provides classes and functions for handling packet-like data structures
that can represent data in various formats (Python dicts, Arrow tables, etc.) while
maintaining type information, source metadata, and semantic type conversion capability.

Key classes:
- SemanticConverter: Converts between different data representations. Intended for internal use.
- DictDatagram: Immutable dict-based data structure
- PythonDictPacket: Python dict-based packet with source info
- ArrowPacket: Arrow table-based packet implementation
- PythonDictTag/ArrowTag: Tag implementations for data identification

The module also provides utilities for schema validation, table operations,
and type conversions between semantic stores, Python stores, and Arrow tables.
"""

import logging
from abc import abstractmethod
from collections.abc import Collection, Iterator, Mapping
from typing import Self, TypeAlias, TYPE_CHECKING
from orcapod import contexts
from orcapod.core.base import ContentIdentifiableBase
from orcapod.protocols.hashing_protocols import ContentHash

from orcapod.utils.lazy_module import LazyModule
from orcapod.types import DataValue, PythonSchema

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import pyarrow as pa
else:
    pa = LazyModule("pyarrow")

# A conveniece packet-like type that defines a value that can be
# converted to a packet. It's broader than Packet and a simple mapping
# from string keys to DataValue (e.g., int, float, str) can be regarded
# as PacketLike, allowing for more flexible interfaces.
# Anything that requires Packet-like data but without the strict features
# of a Packet should accept PacketLike.
# One should be careful when using PacketLike as a return type as it does not
# enforce the typespec or source_info, which are important for packet integrity.
PacketLike: TypeAlias = Mapping[str, DataValue]

PythonStore: TypeAlias = Mapping[str, DataValue]


class ImmutableDict(Mapping[str, DataValue]):
    """
    An immutable dictionary-like container for DataValues.

    Provides a read-only view of a dictionary mapping strings to DataValues,
    implementing the Mapping protocol for compatibility with dict-like operations.

    Initialize with data from a mapping.
    Args:
        data: Source mapping to copy data from
    """

    def __init__(self, data: Mapping[str, DataValue]):
        self._data = dict(data)

    def __getitem__(self, key: str) -> DataValue:
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return self._data.__repr__()

    def __str__(self) -> str:
        return self._data.__str__()

    def __or__(self, other: Mapping[str, DataValue]) -> Self:
        """
        Create a new ImmutableDict by merging with another mapping.

        Args:
            other: Another mapping to merge with

        Returns:
            A new ImmutableDict containing the combined data
        """
        return self.__class__(self._data | dict(other))


def contains_prefix_from(column: str, prefixes: Collection[str]) -> bool:
    """
    Check if a column name matches any of the given prefixes.

    Args:
        column: Column name to check
        prefixes: Collection of prefixes to match against

    Returns:
        True if the column starts with any of the prefixes, False otherwise
    """
    for prefix in prefixes:
        if column.startswith(prefix):
            return True
    return False


class BaseDatagram(ContentIdentifiableBase):
    """
    Abstract base class for immutable datagram implementations.

    Provides shared functionality and enforces consistent interface across
    different storage backends (dict, Arrow table, etc.). Concrete subclasses
    must implement the abstract methods to handle their specific storage format.

    The base class only manages the data context key string - how that key
    is interpreted and used is left to concrete implementations.
    """

    def __init__(self, data_context: contexts.DataContext | str | None = None) -> None:
        """
        Initialize base datagram with data context.

        Args:
            data_context: Context for semantic interpretation. Can be a string key
                or a DataContext object, or None for default.
        """
        self._data_context = contexts.resolve_context(data_context)
        self._converter = self._data_context.type_converter

    # 1. Core Properties (Identity & Structure)
    @property
    def data_context_key(self) -> str:
        """Return the data context key."""
        return self._data_context.context_key

    @property
    @abstractmethod
    def meta_columns(self) -> tuple[str, ...]:
        """Return tuple of meta column names."""
        ...

    # TODO: add meta info

    # 2. Dict-like Interface (Data Access)
    @abstractmethod
    def __getitem__(self, key: str) -> DataValue:
        """Get data column value by key."""
        ...

    @abstractmethod
    def __contains__(self, key: str) -> bool:
        """Check if data column exists."""
        ...

    @abstractmethod
    def __iter__(self) -> Iterator[str]:
        """Iterate over data column names."""
        ...

    @abstractmethod
    def get(self, key: str, default: DataValue = None) -> DataValue:
        """Get data column value with default."""
        ...

    # 3. Structural Information
    @abstractmethod
    def keys(
        self,
        include_all_info: bool = False,
        include_meta_columns: bool | Collection[str] = False,
        include_context: bool = False,
    ) -> tuple[str, ...]:
        """Return tuple of column names."""
        ...

    @abstractmethod
    def types(
        self,
        include_all_info: bool = False,
        include_meta_columns: bool | Collection[str] = False,
        include_context: bool = False,
    ) -> PythonSchema:
        """Return type specification for the datagram."""
        ...

    @abstractmethod
    def arrow_schema(
        self,
        include_all_info: bool = False,
        include_meta_columns: bool | Collection[str] = False,
        include_context: bool = False,
    ) -> "pa.Schema":
        """Return the PyArrow schema for this datagram."""
        ...

    @abstractmethod
    def content_hash(self) -> ContentHash:
        """Calculate and return content hash of the datagram."""
        ...

    # 4. Format Conversions (Export)
    @abstractmethod
    def as_dict(
        self,
        include_all_info: bool = False,
        include_meta_columns: bool | Collection[str] = False,
        include_context: bool = False,
    ) -> dict[str, DataValue]:
        """Return dictionary representation of the datagram."""
        ...

    @abstractmethod
    def as_table(
        self,
        include_all_info: bool = False,
        include_meta_columns: bool | Collection[str] = False,
        include_context: bool = False,
    ) -> "pa.Table":
        """Convert the datagram to an Arrow table."""
        ...

    # 5. Meta Column Operations
    @abstractmethod
    def get_meta_value(self, key: str, default: DataValue = None) -> DataValue:
        """Get a meta column value."""
        ...

    @abstractmethod
    def with_meta_columns(self, **updates: DataValue) -> Self:
        """Create new datagram with updated meta columns."""
        ...

    @abstractmethod
    def drop_meta_columns(self, *keys: str) -> Self:
        """Create new datagram with specified meta columns removed."""
        ...

    # 6. Data Column Operations
    @abstractmethod
    def select(self, *column_names: str) -> Self:
        """Create new datagram with only specified data columns."""
        ...

    @abstractmethod
    def drop(self, *column_names: str) -> Self:
        """Create new datagram with specified data columns removed."""
        ...

    @abstractmethod
    def rename(self, column_mapping: Mapping[str, str]) -> Self:
        """Create new datagram with data columns renamed."""
        ...

    @abstractmethod
    def update(self, **updates: DataValue) -> Self:
        """Create new datagram with existing column values updated."""
        ...

    @abstractmethod
    def with_columns(
        self,
        column_types: Mapping[str, type] | None = None,
        **updates: DataValue,
    ) -> Self:
        """Create new datagram with additional data columns."""
        ...

    # 7. Context Operations
    def with_context_key(self, new_context_key: str) -> Self:
        """Create new datagram with different data context."""
        new_datagram = self.copy(include_cache=False)
        new_datagram._data_context = contexts.resolve_context(new_context_key)
        return new_datagram

    # 8. Utility Operations
    def copy(self, include_cache: bool = True) -> Self:
        """Create a shallow copy of the datagram."""
        new_datagram = object.__new__(self.__class__)
        new_datagram._data_context = self._data_context
        return new_datagram
