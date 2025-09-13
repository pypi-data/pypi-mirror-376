from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping  # noqa: TC003
from typing import TYPE_CHECKING, Any, NoReturn, Protocol, Self, runtime_checkable

from bear_dereth.config._settings_manager._common import OpType, ValueType  # noqa: TC001
from bear_dereth.tools.general.freezing import BaseHashValue, BaseNotCacheable

if TYPE_CHECKING:
    from types import NoneType

    from bear_dereth.config._settings_manager._common import QueryCheck


class Document(dict):
    """A document stored in the database.

    This class provides a way to access both a document's content and
    its ID using ``doc.id``.
    """

    def __init__(self, value: Mapping[str, ValueType], doc_id: int) -> NoneType:
        """Initialize the Document with its content and ID.

        Args:
            value: The content of the document as a dictionary.
            doc_id: The unique identifier for the document.
        """
        super().__init__(value)
        self.id: int = doc_id


class HashValue(BaseHashValue):
    """A simple frozen model to hold a hash value for query caching."""

    op: OpType | None

    def combine(self, other: BaseHashValue, **kwargs) -> HashValue:
        """Combine multiple hash values into one."""
        return HashValue(value=[self, other], **kwargs)

    def __hash__(self) -> int:
        if not self.cacheable:
            raise TypeError("This HashValue is not cacheable")
        return super().__hash__()


class NotCacheable(HashValue, BaseNotCacheable):
    """A singleton representing a non-cacheable hash value, contains a frozen cacheable=False flag."""

    def __init__(self) -> None: ...

    def __hash__(self) -> int:
        raise TypeError("This HashValue is not cacheable")

    def combine(self, other: BaseHashValue, **kwargs) -> NoReturn:  # noqa: ARG002
        raise TypeError("This object is not cacheable")


class QueryInstance:
    """A manifestation of a query operation."""

    def __init__(self, test: QueryCheck, hash_val: HashValue | None) -> None:
        self._test = test
        self._hash: HashValue = hash_val if hash_val is not None else NotCacheable()

    def is_cacheable(self) -> bool:
        """Check if this object is cacheable."""
        return self._hash.cacheable

    def combine(self, op: OpType, other: QueryInstance) -> HashValue:
        """Combine multiple hash values into one."""
        if not other.is_cacheable() or not self.is_cacheable():
            return NotCacheable()
        return self._hash.combine(op=op, other=other._hash)

    def __call__(self, value: Mapping) -> bool:
        return self._test(value)

    def __hash__(self) -> int:
        return hash(self._hash)

    def __repr__(self) -> str:
        return f"QueryImpl{self._hash}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, QueryInstance):
            return self._hash == other._hash

        return False

    def __and__(self, other: QueryInstance) -> QueryInstance:
        return QueryInstance(lambda value: self(value) and other(value), self.combine("and", other))

    def __or__(self, other: QueryInstance) -> QueryInstance:
        return QueryInstance(lambda value: self(value) or other(value), self.combine("or", other))

    def __invert__(self) -> QueryInstance:
        return QueryInstance(lambda value: not self(value), HashValue(op="not", value=[self._hash]))


class QueryLike(Protocol):
    def __call__(self, value: Mapping) -> bool: ...
    def __getattr__(self, key: str) -> Self: ...
    def __getitem__(self, key: str) -> Self: ...
    def __eq__(self, value: object) -> QueryInstance: ...  # type: ignore[override]
    def __ne__(self, value: object) -> QueryInstance: ...  # type: ignore[override]
    def __hash__(self) -> int: ...
    def __gt__(self, value: Any) -> QueryInstance: ...
    def __lt__(self, value: Any) -> QueryInstance: ...
    def __and__(self, other: Self) -> QueryInstance: ...
    def __or__(self, other: Self) -> QueryInstance: ...
    def matches(self, regex: str, flags: int = 0) -> QueryInstance: ...
    def search(self, regex: str, flags: int = 0) -> QueryInstance: ...
    def exists(self) -> QueryInstance: ...


@runtime_checkable
class Table(Protocol):
    def __call__(self, *args: Any, **kwargs: Any) -> Self: ...
    def get(self, key: str) -> Any: ...
    def set(self, key: str, value: Any) -> None: ...
    def search(self, query: Any) -> list[Document]: ...
    def all(self) -> list[Document]: ...
    def upsert(self, record: dict[str, Any], query: Any) -> None: ...
    def contains(self, query: Any) -> bool: ...
    def close(self) -> None: ...


class Storage(ABC):
    """The abstract base class for all Storages.

    A Storage (de)serializes the current state of the database and stores it in
    some place (memory, file on disk, ...).
    """

    @abstractmethod
    def read(self) -> dict[str, dict[str, Any]] | None:
        """Read the current state.

        Any kind of deserialization should go here.

        Return ``None`` here to indicate that the storage is empty.
        """
        raise NotImplementedError("To be overridden!")

    @abstractmethod
    def write(self, data: dict[str, dict[str, Any]]) -> None:
        """Write the current state of the database to the storage.

        Any kind of serialization should go here.

        Args:
            data: The current state of the database.
        """
        raise NotImplementedError("To be overridden!")

    @abstractmethod
    def close(self) -> None:
        """Optional: Close open file handles, etc."""
