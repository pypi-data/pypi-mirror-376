from collections.abc import Iterable
from typing import overload

from bauklotz.reporting.types import JSONType


class ItemFactStore:
    """A storage class for managing key-value pairs where keys are item
    identifiers and values are JSON-compatible data.

    Provides methods for setting, getting, and checking items in an internal
    dictionary-based storage. This class can be used as a lightweight data
    store for JSON-like data structures.

    Attributes:
        _facts (dict[str, JSONType]): Internal dictionary storing item
           keys and their associated JSON-compatible values.
    """
    def __init__(self) -> None:
        self._facts: dict[str, JSONType] = {}

    @overload
    def get_collection(self, item: str, default: None = None) -> Iterable[JSONType] | None:
        """

        Args:
            item:

        Returns:

        """

    @overload
    def get_collection(self, item: str, default: Iterable[JSONType]) -> Iterable[JSONType]:
        """

        Args:
            item:
            default:

        Returns:

        """

    def get_collection(self, item: str, default: Iterable[JSONType] | None = None) -> Iterable[JSONType] | None:
        """
        Retrieves a collection of items for a given key while optionally specifying
        a default value. Validates that the retrieved value is iterable and raises
        a TypeError if it is not.

        Args:
            item (str): The key used to look up the collection in the internal dictionary.
            default (Iterable[JSONType] | None, optional): The default value to return
                if the key is not found in the dictionary. Defaults to None.

        Returns:
            Iterable[JSONType] | None: The collection associated with the given key
            or the default value if the key is not found.

        Raises:
            TypeError: If the value retrieved for the given key (or the default value)
            is not an iterable.
        """
        if isinstance(possible_collection := self._facts.get(item, default), Iterable):
            return possible_collection
        else:
            raise TypeError(f'Expected iterable, got {type(possible_collection)}')


    def get(self, item: str, default: JSONType = None) -> JSONType:
        """
        Retrieves the value associated with the specified key from the internal
        data storage.

        If the key exists, its associated value is returned. If the key does not
        exist, the default value is returned instead.

        Args:
            item (str): The key whose value needs to be retrieved from the
                internal data storage.
            default (JSONType, optional): The value to return if the specified
                key does not exist in the internal data storage.

        Returns:
            JSONType: The value associated with the specified key if it exists,
            otherwise the provided default value.
        """
        return self._facts.get(item, default)

    def set(self, item: str, value: JSONType):
        """
        Sets a specific item in the facts dictionary with the provided value.

        This method allows assigning or updating a value associated with a given
        item key within the facts dictionary.

        Args:
            item (str): The key in the facts dictionary to update.
            value (JSONType): The value to associate with the given item key,
                which can be any valid JSON-compatible type.
        """
        self._facts[item] = value

    def extend(self, item: str, value: JSONType):
        match self.get(item, []):
            case list(values): self.set(item, values + [value])
            case other: self.set(item, [other, value])

    def items(self) -> Iterable[tuple[str, JSONType]]:
        """
        Retrieves an iterator over the items of the `_facts` dictionary.

        The method provides access to the underlying key-value pairs stored in the
        `_facts` dictionary as tuples. It allows iterating over the keys and their
        associated values.

        Returns:
            Iterable[tuple[str, JSONType]]: An iterator over the key-value pairs
            of the `_facts` dictionary, where each pair is represented as a tuple.
        """
        return self._facts.items()

    def __contains__(self, item: str) -> bool:
        return item in self._facts

    def __str__(self) -> str:
        return repr(dict(self.items()))