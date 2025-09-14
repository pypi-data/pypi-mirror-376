from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass, field
from re import Pattern, compile as regex, Match, MULTILINE
from typing import Self, Iterable, Literal, cast
from ast import get_docstring

from toolz import assoc, valfilter

from bauklotz.business.filter import FilterConfig, Filter, ConfigurationError
from bauklotz.business.filter.python.file import DOCSTRING_LABEL
from bauklotz.reporting.item.graph import Graph, GraphNode
from bauklotz.reporting.item.python.definition import PythonClass, DefinitionTracer
from bauklotz.reporting.types import JSONType
from bauklotz.reporting.item.generic.group import Module, Component
from bauklotz.reporting.item.python.project import PythonSourceFile


@dataclass(frozen=True)
class PythonModuleConfig(FilterConfig):
    pass



class PythonModuleFilter(Filter[PythonSourceFile, Module, PythonModuleConfig]):
    def __init__(self, name: str, config: PythonModuleConfig):
        super().__init__(name, config)

    def process(self, item: PythonSourceFile) -> Iterable[Module]:
        item.facts.set('part_of_module', item.canonical_id)
        yield Module(item.canonical_id, (item, ))


class ComponentExtractor(ABC):
    @abstractmethod
    def get_components(self, item: Module[PythonSourceFile]) -> Iterable[Component]:
        """
        Abstract method to retrieve components associated with a given module. This method
        must be implemented in any subclass and its purpose is to extract or define a
        list of components related to the provided module input.

        Args:
            item (Module): The module instance for which the components need to be
                retrieved.

        Returns:
            Iterable[Component]: An iterable object containing components derived
                from the provided module.
        """

class DocstringExtractor(ComponentExtractor):
    def __init__(self, pattern: str, flags: int = MULTILINE):
        self._pattern: Pattern = regex(pattern, flags)

    def get_components(self, item: Module[PythonSourceFile]) -> Iterable[Component]:
        for file in item:
            docstring: JSONType = file.facts.get(DOCSTRING_LABEL) or get_docstring(file.get_ast())
            if isinstance(docstring, str):
                yield from self._extract(docstring)

    def _extract(self, docstring: str | None) -> Iterable[Component]:
        if docstring:
            for match in self._pattern.finditer(docstring):
                yield self._build_component(match)

    @staticmethod
    def _build_component(match: Match) -> Component:
        groups: dict[str, str | None] = valfilter(bool, match.groupdict())
        name: str = cast(str, groups.get('name', '')).strip()
        if not name:
            raise AttributeError("Missing component name.")
        else:
            return Component(cast(str, groups.get('type', 'component')), name)

@dataclass(frozen=True)
class PythonComponentConfig(FilterConfig, ABC):
    """
    Configuration data for a Python component.

    This class is used to define and manage the configuration for a Python component,
    ensuring that it adheres to specific requirements and constraints. The class extends
    `FilterConfig` and `ABC`, making it an abstract base class for defining further
    component configurations.

    Attributes:
        extractor (ComponentExtractor): Defines the extractor associated with the
        configuration. This is an abstract property that must be implemented by
        subclasses to provide the necessary extraction logic.
    """
    @property
    @abstractmethod
    def extractor(self) -> ComponentExtractor:
        """

        Returns:

        """


@dataclass(frozen=True)
class PythonDocstringComponentConfig(PythonComponentConfig):
    """
    Represents configuration for a Python component that uses docstring-based
    component extraction.

    This class defines and stores configuration details specific to a Python
    component that extracts information using docstring patterns. It specifies
    the method of extraction, the regex pattern to be used, and associated
    flags for pattern matching. The configuration is immutable due to the
    use of `frozen=True`.

    Attributes:
        method (Literal['docstring']): The method of component extraction, fixed
            as 'docstring' for this configuration type.
        pattern (str): The regex pattern used for identifying components
            defined in the docstring of a Python codebase.
        flags (int): Flags associated with the regex pattern that can be
            used to modify pattern matching behavior.
    """
    method: Literal['docstring'] = 'docstring'
    pattern: str = r"@Component(\[(?P<type>.+)\])?\s+(?P<name>.+?)$"
    flags: int = MULTILINE

    @property
    def extractor(self) -> ComponentExtractor:
        return DocstringExtractor(self.pattern, self.flags)

class PythonComponentFilter(Filter[Module, Component, PythonDocstringComponentConfig]):
    def __init__(self, name: str, config: PythonDocstringComponentConfig):
        super().__init__(name, config)
        self._components: dict[str, Component] = dict()

    def process(self, item: Module) -> Iterable[Component]:
        try:
            for component in self._config.extractor.get_components(item):
                self._components.setdefault(component.canonical_id, component).add_module(item)
                item.facts.set('part_of_component', component.canonical_id)
            return ()
        except AttributeError as error:
            self._logger.warning(f'Invalid component definition: {error}', module=item.canonical_id)
            return ()

    def close(self) -> Iterable[Component]:
        yield from self._components.values()


@dataclass(frozen=True)
class PythonClassHierarchyConfig(FilterConfig):
    """
    Represents the configuration for organizing and managing Python class hierarchies.

    This class provides mechanisms for handling explicit internal module definitions to
    support filtering Python class hierarchies. It also includes methods to deserialize
    configuration data and normalize the module definitions for internal processing. The
    configuration operates as part of the broader `FilterConfig` class.

    Attributes:
        explicit_internal_modules (set[str]): A set of explicitly defined internal module
            names, which are processed for filtering purposes.
    """
    explicit_internal_modules: set[str] = field(default_factory=set)

    @classmethod
    def deserialize(cls, data: Mapping[str, JSONType]) -> Self:
        """
        Deserializes a given mapping data into an instance of the class, applying
        normalization on specific fields and handling inherited deserialization
        logic.

        This method processes the 'explicit_internal_modules' field in the provided
        data, normalizing its structure using an internal helper method. Afterward,
        it passes the updated data to the parent class's deserialization mechanism
        to create the instance.

        Args:
            data (Mapping[str, JSONType]): The input mapping containing serialized
                data to transform into an instance of the class.

        Returns:
            Self: An instance of the class created based on the deserialized data.
        """
        explicit_internal_modules: JSONType = data.get('explicit_internal_modules')
        data = assoc(data, 'explicit_internal_modules', cls._normalize_module_definition(explicit_internal_modules))
        return super().deserialize(data)

    @classmethod
    def _normalize_module_definition(cls, definition: JSONType) -> set[str]:
        match definition:
            case str(value): return {value} if ',' not in value else set(map(str.strip, definition.split(',')))
            case None: return set()
            case _:
                raise ConfigurationError(
                    cls,
                    'explicit_internal_modules',
                    'must be a string or a list of strings'
                )





class PythonClassHierarchyFilter(Filter[PythonClass, Graph, PythonClassHierarchyConfig]):
    def __init__(self, name: str, config: PythonClassHierarchyConfig):
        super().__init__(name, config)
        self._items: list[PythonClass] = []
        self._graph: Graph = Graph()
        self._internal_modules: set[str] = set()

    def process(self, item: PythonClass) -> Iterable[Graph]:
        self._items.append(item)
        self._internal_modules.add(item.source.project)
        return ()


    def close(self) -> Iterable[Graph]:
        tracer: DefinitionTracer = DefinitionTracer(self._internal_modules)
        for item in self._items:
            origin, origin_type = item.trace_origin()
            self._graph.add_node(
                GraphNode(
                    origin,
                    origin,
                    'Python Class',
                    name=item.name,
                    origin=origin_type,
                    abstract=item.facts.get('abstract', False),
                    protocol=item.facts.get('protocol', False)
                )
            )
            for superclass in item.facts.get_collection('superclass', []):
                if not isinstance(superclass, str):
                    self.logger.warning(f'Invalid superclass type: {superclass}')
                    continue
                module, name = superclass.rsplit('.', 1)
                superclass = tracer.trace(module, name)
                superclass_origin = tracer.origin_type(superclass)
                self._graph.add_node(
                    GraphNode(
                        superclass,
                        superclass,
                        'Python Class',
                        name=superclass.rsplit('.', 1)[-1],
                        origin=superclass_origin,
                        abstract=False,
                        protocol=False
                    )
                )
                self._graph.connect_nodes(origin, superclass)
        yield self._graph
