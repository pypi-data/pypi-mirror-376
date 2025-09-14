from dataclasses import dataclass
from typing import Self, Iterable

from bauklotz.business.filter import Filter, FilterConfig
from bauklotz.reporting.types import JSONType
from bauklotz.reporting.item.python.project import PythonProjectLocation, PythonSourceFile, PythonProjectGraph


@dataclass(frozen=True)
class PythonProjectConfig(FilterConfig):
    """
    Represents the configuration settings for a Python project.

    This class defines a configuration structure for filtering Python project
    files, inheriting settings from the base `FilterConfig` class. It allows
    specifying whether special files (such as hidden files) should be ignored
    while processing the project. Instances of this class are immutable due to
    the `@dataclass(frozen=True)` decorator.

    Attributes:
        ignore_special_files (bool): Determines whether to exclude special files
            (e.g., files starting with a dot) from processing. Defaults to False.
    """
    ignore_special_files: bool = False


class PythonProjectFilter(Filter[PythonProjectLocation, PythonSourceFile, PythonProjectConfig]):
    """
    Represents a filter for processing Python projects.

    This class filters Python source files within a project location based on
    specific criteria defined in the project configuration. Its primary purpose
    is to traverse a Python project, analyze its files, and yield only those
    files that meet the filter's conditions.

    Attributes:
        name (str): The name of the filter.
        config (PythonProjectConfig): Configuration settings for how the filter processes files, including any specific rules for ignoring certain files.
    """
    def __init__(self, name: str, config: PythonProjectConfig):
        """
        Represents a Python project configuration initializer.

        This class initializes a Python project configuration with a given name
        and configuration object. The configuration details are encapsulated within
        a PythonProjectConfig object, and the project name is associated with it.

        Args:
            name: The name of the Python project.
            config: The configuration details of the project encapsulated
                as a PythonProjectConfig object.
        """
        super().__init__(name, config)


    def process(self, item: PythonProjectLocation) -> Iterable[PythonSourceFile]:
        """
        Processes the given item, filtering and yielding Python source files based on specific
        conditions, such as the file name prefix and configuration settings.

        Args:
            item: The Python project location containing files to process.

        Yields:
            PythonSourceFile: Each eligible Python source file from the input item.
        """
        for file in item.files():
            if file.file_name.startswith('__') and self.config.ignore_special_files:
                continue
            yield file


@dataclass(frozen=True)
class PythonProjectGraphConfig(FilterConfig):
    """
    Represents the configuration for a Python project graph.

    This class provides the configuration details required for generating or
    managing a Python project graph. It includes attributes such as the project
    name to identify or label the graph. This configuration is immutable due to
    the use of a frozen dataclass, making it suitable for scenarios where
    unchangeable configuration objects are needed.

    Attributes:
        project_name (str): Represents the name of the Python project. Defaults
            to 'Project'.
    """
    project_name: str = 'Project'


class PythonProjectGraphFilter(Filter[PythonSourceFile, PythonProjectGraph, PythonProjectGraphConfig]):
    def __init__(self, name: str, config: PythonProjectGraphConfig):
        super().__init__(name, config)
        self._project_fileset: set[PythonSourceFile] = set()

    def process(self, item: PythonSourceFile) -> Iterable[PythonProjectGraph]:
        self._project_fileset.add(item)
        return ()

    def close(self) -> Iterable[PythonProjectGraph]:
        project_graph: PythonProjectGraph = PythonProjectGraph(self.config.project_name)
        for file in self._project_fileset:
            project_graph.add_file(file, 'Python File', dict(file.facts.items()))
        self._project_fileset.clear()
        yield project_graph