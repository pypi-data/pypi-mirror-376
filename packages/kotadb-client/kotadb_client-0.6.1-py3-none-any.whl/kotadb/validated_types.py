"""
Validated types for KotaDB Python client.

These types mirror the Rust validated types and provide compile-time
safety guarantees by ensuring they cannot be constructed with invalid data.
"""

import time
import uuid
from typing import Union

from .validation import (
    validate_directory_path,
    validate_document_id,
    validate_file_path,
    validate_size,
    validate_timestamp,
    validate_title,
)


class ValidatedPath:
    """
    A path that has been validated and is guaranteed to be safe.

    Invariants:
    - Path is non-empty
    - No directory traversal (..)
    - No null bytes
    - Valid UTF-8
    - Not a reserved name (Windows compatibility)
    """

    def __init__(self, path: str):
        """
        Create a new validated path.

        Args:
            path: Path to validate

        Raises:
            ValidationError: If path is invalid
        """
        validate_file_path(path)
        self._path = path

    @classmethod
    def new(cls, path: str) -> "ValidatedPath":
        """
        Alternative constructor for consistency with Rust API.

        Args:
            path: Path to validate

        Returns:
            ValidatedPath instance

        Raises:
            ValidationError: If path is invalid
        """
        return cls(path)

    def as_str(self) -> str:
        """Get the path as a string."""
        return self._path

    def __str__(self) -> str:
        return self._path

    def __repr__(self) -> str:
        return f"ValidatedPath({self._path!r})"

    def __eq__(self, other) -> bool:
        if isinstance(other, ValidatedPath):
            return self._path == other._path
        elif isinstance(other, str):
            return self._path == other
        return False

    def __hash__(self) -> int:
        return hash(self._path)


class ValidatedDirectoryPath(ValidatedPath):
    """
    A directory path that has been validated.

    Additional invariants:
    - Should not have file extension
    """

    def __init__(self, path: str):
        """
        Create a new validated directory path.

        Args:
            path: Directory path to validate

        Raises:
            ValidationError: If path is invalid
        """
        validate_directory_path(path)
        self._path = path


class ValidatedDocumentId:
    """
    A document ID that is guaranteed to be valid.

    Invariants:
    - Valid UUID format
    - Not nil UUID
    """

    def __init__(self, doc_id: Union[str, uuid.UUID]):
        """
        Create a new validated document ID.

        Args:
            doc_id: Document ID as string or UUID

        Raises:
            ValidationError: If ID is invalid
        """
        if isinstance(doc_id, uuid.UUID):
            doc_id = str(doc_id)

        validate_document_id(doc_id)
        self._id = doc_id
        self._uuid = uuid.UUID(doc_id)

    @classmethod
    def new(cls) -> "ValidatedDocumentId":
        """
        Create a new random document ID.

        Returns:
            ValidatedDocumentId with random UUID
        """
        return cls(uuid.uuid4())

    @classmethod
    def from_uuid(cls, doc_uuid: uuid.UUID) -> "ValidatedDocumentId":
        """
        Create from existing UUID.

        Args:
            doc_uuid: UUID to validate

        Returns:
            ValidatedDocumentId instance

        Raises:
            ValidationError: If UUID is invalid
        """
        return cls(doc_uuid)

    @classmethod
    def parse(cls, s: str) -> "ValidatedDocumentId":
        """
        Parse from string.

        Args:
            s: String representation of UUID

        Returns:
            ValidatedDocumentId instance

        Raises:
            ValidationError: If string is invalid UUID
        """
        return cls(s)

    def as_uuid(self) -> uuid.UUID:
        """Get the UUID object."""
        return self._uuid

    def as_str(self) -> str:
        """Get the ID as a string."""
        return self._id

    def __str__(self) -> str:
        return self._id

    def __repr__(self) -> str:
        return f"ValidatedDocumentId({self._id!r})"

    def __eq__(self, other) -> bool:
        if isinstance(other, ValidatedDocumentId):
            return self._id == other._id
        elif isinstance(other, (str, uuid.UUID)):
            return self._id == str(other)
        return False

    def __hash__(self) -> int:
        return hash(self._id)


class ValidatedTitle:
    """
    A non-empty title with enforced length limits.

    Invariants:
    - Non-empty after trimming
    - Length <= 1024 characters
    """

    MAX_LENGTH = 1024

    def __init__(self, title: str):
        """
        Create a new validated title.

        Args:
            title: Title to validate

        Raises:
            ValidationError: If title is invalid
        """
        validate_title(title)
        self._title = title.strip()

    @classmethod
    def new(cls, title: str) -> "ValidatedTitle":
        """
        Alternative constructor for consistency with Rust API.

        Args:
            title: Title to validate

        Returns:
            ValidatedTitle instance

        Raises:
            ValidationError: If title is invalid
        """
        return cls(title)

    def as_str(self) -> str:
        """Get the title as a string."""
        return self._title

    def __str__(self) -> str:
        return self._title

    def __repr__(self) -> str:
        return f"ValidatedTitle({self._title!r})"

    def __eq__(self, other) -> bool:
        if isinstance(other, ValidatedTitle):
            return self._title == other._title
        elif isinstance(other, str):
            return self._title == other
        return False

    def __hash__(self) -> int:
        return hash(self._title)


class NonZeroSize:
    """
    A non-zero size value.

    Invariants:
    - Must be greater than zero
    """

    def __init__(self, size: int):
        """
        Create a new non-zero size.

        Args:
            size: Size value

        Raises:
            ValidationError: If size is invalid
        """
        validate_size(size)
        self._size = size

    @classmethod
    def new(cls, size: int) -> "NonZeroSize":
        """
        Alternative constructor for consistency with Rust API.

        Args:
            size: Size value

        Returns:
            NonZeroSize instance

        Raises:
            ValidationError: If size is invalid
        """
        return cls(size)

    def get(self) -> int:
        """Get the size value."""
        return self._size

    def __int__(self) -> int:
        return self._size

    def __str__(self) -> str:
        return str(self._size)

    def __repr__(self) -> str:
        return f"NonZeroSize({self._size})"

    def __eq__(self, other) -> bool:
        if isinstance(other, NonZeroSize):
            return self._size == other._size
        elif isinstance(other, int):
            return self._size == other
        return False

    def __hash__(self) -> int:
        return hash(self._size)


class ValidatedTimestamp:
    """
    A timestamp with validation.

    Invariants:
    - Must be positive (after Unix epoch)
    - Must be reasonable (not in far future)
    """

    def __init__(self, timestamp: int):
        """
        Create a new validated timestamp.

        Args:
            timestamp: Unix timestamp

        Raises:
            ValidationError: If timestamp is invalid
        """
        validate_timestamp(timestamp)
        self._timestamp = timestamp

    @classmethod
    def new(cls, timestamp: int) -> "ValidatedTimestamp":
        """
        Alternative constructor for consistency with Rust API.

        Args:
            timestamp: Unix timestamp

        Returns:
            ValidatedTimestamp instance

        Raises:
            ValidationError: If timestamp is invalid
        """
        return cls(timestamp)

    @classmethod
    def now(cls) -> "ValidatedTimestamp":
        """
        Create a timestamp for the current time.

        Returns:
            ValidatedTimestamp with current time
        """
        return cls(int(time.time()))

    def as_secs(self) -> int:
        """Get the timestamp in seconds."""
        return self._timestamp

    def __int__(self) -> int:
        return self._timestamp

    def __str__(self) -> str:
        return str(self._timestamp)

    def __repr__(self) -> str:
        return f"ValidatedTimestamp({self._timestamp})"

    def __eq__(self, other) -> bool:
        if isinstance(other, ValidatedTimestamp):
            return self._timestamp == other._timestamp
        elif isinstance(other, int):
            return self._timestamp == other
        return False

    def __hash__(self) -> int:
        return hash(self._timestamp)
