import logging
from abc import ABC
from typing import Any

from orcapod import DEFAULT_CONFIG, contexts
from orcapod.config import Config
from orcapod.protocols import hashing_protocols as hp

logger = logging.getLogger(__name__)


class LablableBase:
    def __init__(self, label: str | None = None, **kwargs):
        self._label = label
        super().__init__(**kwargs)

    @property
    def has_assigned_label(self) -> bool:
        """
        Check if the label is explicitly set for this object.

        Returns:
            bool: True if the label is explicitly set, False otherwise.
        """
        return self._label is not None

    @property
    def label(self) -> str:
        """
        Get the label of this object.

        Returns:
            str | None: The label of the object, or None if not set.
        """
        return self._label or self.computed_label() or self.__class__.__name__

    @label.setter
    def label(self, label: str | None) -> None:
        """
        Set the label of this object.

        Args:
            label (str | None): The label to set for this object.
        """
        self._label = label

    def computed_label(self) -> str | None:
        """
        Compute a label for this object based on its content. If label is not explicitly set for this object
        and computed_label returns a valid value, it will be used as label of this object.
        """
        return None


class ContextAwareConfigurableBase(ABC):
    def __init__(
        self,
        data_context: str | contexts.DataContext | None = None,
        orcapod_config: Config | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        if orcapod_config is None:
            orcapod_config = DEFAULT_CONFIG
        self._orcapod_config = orcapod_config
        self._data_context = contexts.resolve_context(data_context)

    @property
    def orcapod_config(self) -> Config:
        return self._orcapod_config

    @property
    def data_context(self) -> contexts.DataContext:
        return self._data_context

    @property
    def data_context_key(self) -> str:
        """Return the data context key."""
        return self._data_context.context_key


class ContentIdentifiableBase(ContextAwareConfigurableBase):
    """
    Base class for content-identifiable objects.
    This class provides a way to define objects that can be uniquely identified
    based on their content rather than their identity in memory. Specifically, the identity of the
    object is determined by the structure returned by the `identity_structure` method.
    The hash of the object is computed based on the `identity_structure` using the provided `ObjectHasher`,
    which defaults to the one returned by `get_default_object_hasher`.
    Two content-identifiable objects are considered equal if their `identity_structure` returns the same value.
    """

    def __init__(self, **kwargs) -> None:
        """
        Initialize the ContentHashable with an optional ObjectHasher.

        Args:
            identity_structure_hasher (ObjectHasher | None): An instance of ObjectHasher to use for hashing.
        """
        super().__init__(**kwargs)
        self._cached_content_hash: hp.ContentHash | None = None
        self._cached_int_hash: int | None = None

    def identity_structure(self) -> Any:
        """
        Return a structure that represents the identity of this object.

        Override this method in your subclass to provide a stable representation
        of your object's content. The structure should contain all fields that
        determine the object's identity.

        Returns:
            Any: A structure representing this object's content, or None to use default hash
        """
        raise NotImplementedError("Subclasses must implement identity_structure")

    def content_hash(self) -> hp.ContentHash:
        """
        Compute a hash based on the content of this object.

        Returns:
            bytes: A byte representation of the hash based on the content.
                   If no identity structure is provided, return None.
        """
        if self._cached_content_hash is None:
            structure = self.identity_structure()
            # processed_structure = process_structure(structure)
            self._cached_content_hash = self.data_context.object_hasher.hash_object(
                structure
            )
        return self._cached_content_hash

    def __hash__(self) -> int:
        """
        Hash implementation that uses the identity structure if provided,
        otherwise falls back to the superclass's hash method.

        Returns:
            int: A hash value based on either content or identity
        """
        # Get the identity structure
        return self.content_hash().to_int()

    def __eq__(self, other: object) -> bool:
        """
        Equality check that compares the identity structures of two objects.

        Args:
            other (object): The object to compare against.

        Returns:
            bool: True if both objects have the same identity structure, False otherwise.
        """
        if not isinstance(other, ContentIdentifiableBase):
            return NotImplemented

        return self.identity_structure() == other.identity_structure()


class LabeledContentIdentifiableBase(ContentIdentifiableBase, LablableBase):
    pass
