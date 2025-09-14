from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from inspect import signature
from typing import get_args, Self, ClassVar
from types import UnionType

from dacite import from_dict, DaciteError, DaciteFieldError

from bauklotz.reporting.item import Item
from bauklotz.reporting.logging import BauklotzLogger, NoopLogger
from bauklotz.reporting.types import JSONType


class ConfigurationError(TypeError):
    def __init__(self, config_type: type, path: str | None, reason: str):
        super().__init__(f'{config_type.__name__} configuration is invalid: {path or "root"}. {reason}')
        self.config_type: type = config_type


@dataclass(frozen=True)
class FilterConfig:

    @classmethod
    def deserialize(cls, data: Mapping[str, JSONType]) -> Self:
        try:
            return from_dict(cls, data)
        except DaciteFieldError as error:
            raise ConfigurationError(cls, error.field_path, str(error))



class Filter[I: Item, O: Item, C: FilterConfig](ABC):
    """
    Abstract base class for creating a filter that processes items.

    This class serves as a blueprint for creating filters that take in input items,
    process them, and return output items, while being configured using a specified
    filter configuration. The `Filter` class operates on generic types for input,
    output, and configuration.

    Attributes:
        _name (str): Name of the filter.
        _config (C): Configuration object for the filter.
    """

    provides_facts: ClassVar[frozenset[str]] = frozenset()
    requires_facts: ClassVar[frozenset[str]] = frozenset()

    def __init__(self, name: str, config: C):
        self._name: str = name
        self._config: C = config
        self._logger: BauklotzLogger = NoopLogger()

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger: BauklotzLogger):
        if not isinstance(logger, BauklotzLogger):
            raise TypeError("logger must be an instance of BauklotzLogger")
        else:
            self._logger = logger

    @property
    def config(self) -> C:
        """
            Returns the configuration object of the current instance.

            This property provides access to the private `_config` attribute, which holds the
            configuration settings for this instance.

            Returns:
                C: The configuration object associated with the current instance.
        """
        return self._config

    @property
    def name(self) -> str:
        """
        Gets the name attribute of the object.

        This method serves as a property getter for the name attribute, providing
        external access to the internal `_name` attribute. The property is read-only.

        Returns:
            str: The name associated with the object.
        """
        return self._name

    @abstractmethod
    def process(self, item: I) -> Iterable[O]:
        """
        Processes an item and applies relevant facts to generate an output sequence. This
        method must be implemented by sub-classes as it is specific to each implementation.

        Args:
            item: Input element to be processed.

        Returns:
            Iterable of processed output elements generated from the input item and its
            associated facts.
        """

    def close(self) -> Iterable[O]:
        """
        Closes the current context, releasing any resources or finalizing any processing,
        and returns an iterable of results.

        This is typically used in contexts where a close operation aggregates or prepares
        data for a final output. The method should be called to ensure proper handling and
        cleanup of resources.

        Returns:
            Iterable[O]: An iterable containing the results collected or prepared during
            the close operation.
        """
        return ()

    @classmethod
    def _extract_item_type[T: Item](cls, item_type: type[T]) -> set[type[T]]:
        if isinstance(item_type, UnionType):
            return set(get_args(item_type))
        else:
            return {item_type}


    @classmethod
    def input_type(cls) -> set[type[I]]:
        """
        Returns the set of input types compatible with the `process` method of the class.

        The method inspects the type annotations for the parameter `item` in the
        signature of the `process` method. It extracts and processes the input types
        to ensure compatibility with the expected types for the method's operation.

        Returns:
            set[type[I]]: A set containing the extracted types for the `item` parameter
            within the `process` method.

        Raises:
            AttributeError: If the `process` method or annotations for `item` are not
            found within the class.

        """
        if parameter := signature(cls.process).parameters.get('item'):
            return cls._extract_item_type(parameter.annotation)
        else:
            raise TypeError("Method 'process' does not have a 'item' parameter")


    @classmethod
    def output_type(cls) -> set[type[O]]:
        """
        Determines the output types of a subclass based on its `process` method's return annotation.

        This utility method analyzes the annotated return type of the `process` method
        to infer the types of outputs that the subclass is designed to produce. It is
        intended to facilitate type management and validation by extracting the return
        type from the function signature and provides this information in a standardized
        set format.

        Returns:
            set[type[O]]: A set containing the inferred output types from the annotated
            return type of the `process` method.
        """
        return cls._extract_item_type(signature(cls.process).return_annotation)

    @classmethod
    def config_type(cls) -> type[C]:
        """
        Returns the expected type of the 'config' parameter for the class.

        This method introspects the class's `__init__` method to retrieve the type
        annotation of the 'config' parameter. It can be used to enforce or verify
        type safety when instantiating objects of the class.

        Returns:
            type[C]: The annotated type of the 'config' parameter from the class's
                `__init__` method. If no annotation is provided for the 'config'
                parameter, this method will return `None`.
        """
        if parameter := signature(cls.__init__).parameters.get('config'):
            return parameter.annotation
        else:
            raise TypeError("Constructor does not have a 'config' parameter")