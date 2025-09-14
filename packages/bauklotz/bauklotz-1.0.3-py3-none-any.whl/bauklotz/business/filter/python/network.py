from dataclasses import dataclass
from math import log
from typing import Self, Iterable

from toolz import first

from bauklotz.business.filter import Filter, FilterConfig
from bauklotz.reporting.item.graph import Graph, GraphNode
from bauklotz.reporting.item.python.dependency import PythonImport
from bauklotz.reporting.types import JSONType


@dataclass(frozen=True)
class DependencyNetworkConfig(FilterConfig):
    """
    Represents the configuration for a dependency network.

    This class defines the configuration settings required for a dependency
    network used in the application. It inherits from the FilterConfig class
    and introduces additional attributes to customize the network's behavior.
    The configuration is immutable due to the usage of the dataclass decorator
    with the frozen flag set to True.

    Attributes:
        log_weight (bool): Indicates whether to log the weights of the
            dependency network. Defaults to False.
    """
    log_weight: bool = False


class DependencyNetworkFilter(Filter[PythonImport, Graph, DependencyNetworkConfig]):
    def __init__(self, name: str, config: DependencyNetworkConfig):
        super().__init__(name, config)
        self._graph: Graph = Graph()
        self._items: list[PythonImport] = []

    def process(self, item: PythonImport) -> Iterable[Graph]:
        self._items.append(item)
        return ()

    def _create_node_from(self, item: PythonImport):
        if item.dependant.canonical_id not in self._graph:
            self._graph.add_node(
                GraphNode(
                item.dependant.canonical_id,
                'internal',
                'module',
                module_type='project'
                )
            )

    def _create_node_from_external(self, item: PythonImport):
        if item.dependency_id not in self._graph:
            category: str = first(item.import_category().values())
            self._graph.add_node(
                GraphNode(
                item.dependency_id,
                'external',
                'module',
                module_type=category
                )
            )
            self._graph.connect_nodes(
                item.dependant.canonical_id,
                item.dependency_id,
                weight=self._calculate_weight(len(item.imported_artifacts))
            )

    def close(self) -> Iterable[Graph]:
        for item in self._items:
            self._create_node_from(item)
        for item in self._items:
            self._create_node_from_external(item)
        yield self._graph

    def _calculate_weight(self, import_count: int) -> int | float:
        return log(import_count + 1, 2) if self.config.log_weight else import_count