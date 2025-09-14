from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from inspect import signature
from pathlib import Path
from typing import Self

from dacite import from_dict, Config, DaciteFieldError, MissingValueError

from bauklotz.reporting.item import Item
from bauklotz.reporting.types import JSONType


class ReportConfigurationError(TypeError):
    """
    Represents an error related to the configuration of a report.

    This exception is raised when there is an issue with the configuration
    of a report type. It provides details about the specific type of report,
    the problematic configuration entry, and the nature of the problem.

    Attributes:
        report_type (type): The type of the report where the configuration
            issue occurred.
        config_entry (str | None): The specific configuration entry related
            to the issue, or None if not applicable.
        problem (str): A description of the issue with the configuration.
    """
    def __init__(self, report_type: type, config_entry: str | None, problem: str):
        super().__init__(f'{report_type.__name__} configuration is invalid: {config_entry}. {problem}')


@dataclass(frozen=True)
class ReportConfiguration:
    """
    Represents configuration settings and parameters for a report.

    This class is designed to manage the configuration data associated with a
    report. It provides a structure for defining and interacting with the settings
    necessary for generating or describing a report. The `deserialize` method
    serves as a template for creating an instance of this class from serialized
    data (e.g., JSON).

    Classes inheriting from this abstract base class must implement the
    `deserialize` method to handle specific deserialization logic.

    Attributes:
        None
    """
    @classmethod
    def deserialize(cls, data: Mapping[str, JSONType]) -> Self:
        """
        Deserializes data into an instance of the class.

        This method is a class-level abstract method that parses the provided
        mapping structure (typically JSON) and converts it into an instance of
        the corresponding class. Implementations must handle the details of
        mapping the given data to class attributes.

        Args:
            data (Mapping[str, JSONType]): A mapping representing the serialized
                form of the object. The mapping keys correspond to the class
                attributes, and values hold the associated data.

        Returns:
            Self: An instance of the class containing the deserialized data.
        """
        try:
            return from_dict(cls, data, Config({Path: Path}, check_types=True, strict=True, strict_unions_match=True))
        except DaciteFieldError as error:
            raise ReportConfigurationError(cls, error.field_path, str(error)) from error
        except TypeError as error:
            raise ReportConfigurationError(cls, None, str(error)) from error

class Report[I: Item, C: ReportConfiguration](ABC):
    """
    Represents an abstract base class for creating reports with items.

    The `Report` class serves as a blueprint for report generation. It provides
    a common interface and enforces the implementation of the `write` method by
    subclasses. The class includes attributes and methods for managing the report
    name and defining behavior for writing and closing the report.

    Attributes:
        name (str): The name of the report.
    """
    def __init__(self, name: str, config: C):
        self._name: str = name
        self._config: C = config

    @property
    def config(self) -> C:
        """
        Returns the configuration object associated with the instance.

        The configuration object encapsulates the settings or parameters
        that define the behavior of the instance. Accessing this property
        provides a read-only view of the current configuration.

        Attributes:
            config: Represents the configuration object stored within
                the instance.

        Returns:
            C: The configuration object associated with the instance.
        """
        return self._config

    @classmethod
    def config_type(cls) -> type[ReportConfiguration]:
        """
            Determines and returns the type of the configuration object that should be used
            with the class. This method inspects the type hints of the `__init__` method
            for the `config` parameter to deduce the expected configuration type.

            Returns:
                type[ReportConfiguration]: The type of the expected configuration object.
        """
        if parameter := signature(cls.__init__).parameters.get('config'):
            return parameter.annotation
        else:
            raise TypeError("Constructor does not have a 'config' parameter")

    @property
    def name(self) -> str:
        """
        Gets the name attribute for the object.

        This property retrieves the private `_name` attribute and provides
        read-only access to its value. It is commonly used for getting the
        name identifier of an instance.

        Returns:
            str: The name associated with the object.
        """
        return self._name

    @abstractmethod
    def write(self, item: I) -> None:
        """
        Represents an abstract class for objects that implement a write operation.

        This class is intended to be subclassed to provide concrete implementations of
        a write operation, which takes in a single item and performs some action or
        operation with it.

        Methods:
            write: Abstract method that must be implemented in subclasses to define the
                behavior of the write operation.
        """


    def close(self) -> None:
        """
        Closes the current resource or connection.

        This method is responsible for ensuring that any open resources or connections
        associated with the object are properly closed and cleaned up. It should be
        called when the object is no longer needed to release any underlying system
        resources such as file handles, database connections, or network sockets.

        Raises:
            OSError: If an error occurs while closing the resource.
        """
        return None