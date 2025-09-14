from dataclasses import dataclass
from pathlib import Path

from bauklotz.reporting.item.python.definition import PythonClass
from bauklotz.reporting.report import ReportConfiguration
from bauklotz.reporting.report.buffered import BufferedReport


@dataclass(frozen=True)
class ClassDiagramConfiguration(ReportConfiguration):
    """
    Represents the configuration for generating a class diagram report.

    This class provides the necessary configuration settings for creating
    a class diagram, including file path and resolution (DPI). It is a
    frozen dataclass, immutably holding all the required attributes.

    Attributes:
        path (str): The file path where the class diagram will be saved.
        dpi (int): The resolution of the output diagram in dots per inch (DPI).
            Defaults to 500.
    """
    path: Path
    dpi: int = 500


class ClassDiagramWriter(BufferedReport[PythonClass, ClassDiagramConfiguration]):
    """
    Manages the generation and writing of class diagrams in the PlantUML format.

    This class is responsible for creating class diagrams based on the provided
    Python class data and configuration. It formats the syntax according to
    PlantUML standards and writes the output to a specified file.

    Attributes:
        _connections (list[str]): Stores connections (e.g., inheritance, associations)
            between classes in the diagram.
    """
    def __init__(self, name: str, config: ClassDiagramConfiguration):
        """
        Initializes a new instance of the class with specified name and configuration.

        Args:
            name: A string representing the name of the instance.
            config: An instance of ClassDiagramConfiguration providing the configuration
                for the class diagram.

        Attributes:
            _connections: A list of strings representing the connections associated
                with the instance.
        """
        super().__init__(name, config)
        self._connections: list[str] = []

    def close(self) -> None:
        """
        Closes and finalizes the writing operation by generating a PlantUML diagram file.

        The method processes a list of classes and their connections, converts them into a
        PlantUML-compatible format, and writes the resulting content into a file defined
        by the configuration. It ensures the proper structure and syntax of the PlantUML
        document.

        Args:
            None

        Returns:
            None
        """
        body: list[str] = ['@startuml', f'skinparam dpi {self.config.dpi}', 'top to bottom direction']
        body.extend(map(self._handle_class, self._get_entries()))
        body.extend(self._connections)
        body.append('@enduml')
        with open(self.config.path, 'w') as out:
            out.write('\n'.join(body))

    def _handle_class(self, item: PythonClass) -> str:
        class_type: str = 'class'
        if item.facts.get('abstract'):
            class_type = 'abstract'
        if item.facts.get('protocol'):
            class_type = 'protocol'
        body: list[str] = [f'{class_type} {item.module}.{item.name} {{']
        for method in item.methods:
            args = ', '.join(str(arg['name']) for arg in method.args)
            body.append(f'\t+{method.name}({args})')
        body.append('}')
        for superclass in item.facts.get_collection('superclass', []):
            self._connections.append(f'{superclass} <|-- {item.module}.{item.name}')
        return '\n'.join(body)



