"""

@Component[Layer] Filter
@Component[SubLayer] Python
"""
from ast import walk, ClassDef, parse, If, IfExp, ExceptHandler, Match, For, While, Name, Subscript, Attribute, BinOp, BitOr
from collections.abc import Sequence
from dataclasses import dataclass
from functools import singledispatchmethod
from typing import Iterable, ClassVar, Literal

from toolz import count, drop, compose

from bauklotz.business.filter import FilterConfig, Filter
from bauklotz.reporting.types import JSONType
from bauklotz.reporting.item.python.definition import PythonClass, ClassMethod, DefinitionInspector, InspectionError
from bauklotz.reporting.item.python.project import PythonSourceFile


@dataclass(frozen=True)
class PythonClassConfig(FilterConfig):
    """
    Configuration class for PythonClass filtering.

    Represents configuration details to control filtering functionality for Python
    classes, with options to ignore dataclasses and inspect attributes. This class
    also includes methods for deserialization of configuration data.

    Attributes:
        _ignore_dataclasses (bool): Determines whether dataclasses should be ignored
            in filtering.
        _inspect (bool): Indicates whether inspection of attributes should be
            enabled or not.
    """
    ignore_dataclasses: bool = False
    inspect: bool = True

class PythonClassFilter(Filter[PythonSourceFile, PythonClass, PythonClassConfig]):
    """Filters and processes Python class definitions within source files.

    The PythonClassFilter is used for analyzing Python source files to identify
    and process class definitions, extracting relevant information including
    type parameters, abstract class status, and interface status. This filter
    yields processed representations of the discovered classes for further use.

    Attributes:
        provides_facts (frozenset[str]): Specifies the types of facts that
            this filter provides, including 'classes', 'type_parameters',
            'abstract', and 'interface'.
    """
    provides_facts: ClassVar[frozenset[str]] = frozenset({'classes', 'type_parameters', 'abstract', 'interface'})


    def __init__(self, name: str, config: PythonClassConfig):
        super().__init__(name, config)

    def process(self, item: PythonSourceFile) -> Iterable[PythonClass]:
        """
        Processes a Python source file to extract class definitions and append them to
        the corresponding facts list.

        This method traverses the abstract syntax tree (AST) of a provided Python source
        file. It identifies class definitions within the structure, generates result
        items for these definitions, and appends the identified class names to the
        source file's facts under the 'classes' category.

        Args:
            item: The Python source file to process, represented as a PythonSourceFile
                object.

        Yields:
            An iterable of PythonClass objects, each corresponding to a class
            definition found within the provided source file.
        """
        for element in walk(item.get_ast()):
            if isinstance(element, ClassDef):
                yield self._build_result_item(item, element)
                item.facts.extend('classes', element.name)

    def _build_result_item(self, item: PythonSourceFile, element: ClassDef) -> PythonClass:
        lines: Sequence[str] = item.content.splitlines()
        class_item: PythonClass = PythonClass(
            item.canonical_id,
            element.name,
            '\n'.join(lines[element.lineno -1 : element.end_lineno]),
            item
        )
        self._handle_generics(class_item, element)
        if self.config.inspect:
            self._inspect(class_item)
        return class_item

    def _inspect(self, class_item: PythonClass) -> None:
        """
        Inspects a given Python class and sets facts about its attributes such as
        whether it's abstract or an interface.

        Args:
            class_item (PythonClass): The class to be inspected. The `class_item`
                parameter should contain both module and name attributes to locate
                the class for inspection.

        Raises:
            InspectionError: This will usually happen if there's an issue during
                reflection or retrieval of the class object.

        """
        inspector: DefinitionInspector = DefinitionInspector()
        try:
            class_obj: object = inspector.inspect(class_item.module, class_item.name)
            if isinstance(class_obj, type):
                class_item.facts.set('abstract', bool(getattr(class_obj, '__abstractmethods__', False)))
                class_item.facts.set('interface', bool(getattr(class_obj, '_is_protocol', False)))
        except InspectionError as error:
            self.logger.error(f"Error inspecting class {class_item.name}: {error}")


    def _handle_generics(self, item: PythonClass, element: ClassDef) -> None:
        generics: dict[str, JSONType] = {
            generic.name: self._parse_generic_bound(generic.bound) for generic in element.type_params
            if hasattr(generic, "name") and hasattr(generic, "bound")
        }
        item.facts.set('type_parameters', generics)

    @singledispatchmethod
    def _parse_generic_bound(self, bound) -> str | dict[str, JSONType]:
        return str(bound)

    @_parse_generic_bound.register
    def _parse_name(self, bound: Name) -> str:
        return bound.id

    @_parse_generic_bound.register
    def _parse_op(self, bound: BinOp) -> dict[str, JSONType]:
        op: str = bound.op.__class__.__name__
        match bound.op:
            case BitOr(): op = 'or'
        return {'op':op, 'left': self._parse_generic_bound(bound.left), 'right': self._parse_generic_bound(bound.right)}

@dataclass(frozen=True)
class PythonSuperclassConfig(FilterConfig):
    pass

class PythonSuperclassFilter(Filter[PythonClass, PythonClass, PythonSuperclassConfig]):
    """
    Filters Python classes to extract superclass information based on their definitions.

    This class processes Python class definitions to identify and extract their
    superclass names and canonicalize them. It utilizes the configuration and imports
    available for each Python class item to resolve the canonical names of the superclasses.
    The extracted superclass facts are then set on the processed item. This class also
    provides helper methods and functions to parse and format superclass names accurately.

    Attributes:
        _imports (dict[str, str]): Mapping of import names to their canonical fully-qualified names.
        _module (str): Canonical identifier of the module being processed.
    """
    provides_facts: ClassVar[frozenset[str]] = frozenset({'superclass'})

    def __init__(self, name: str, config: PythonSuperclassConfig = PythonSuperclassConfig()):
        super().__init__(name, config)
        self._imports: dict[str, str] = {}
        self._module: str = ''

    def process(self, item: PythonClass) -> Iterable[PythonClass]:
        """
        Processes a `PythonClass` object to extract and analyze its structure, and yields the processed
        object with updated facts. Specifically, it identifies and processes the superclass relationships
        for the input class object.

        Args:
            item: A `PythonClass` object that contains source code and metadata. It provides information
                such as source imports, module identity, and class body representation.

        Returns:
            Iterable of `PythonClass` objects. The processed object includes the updated `facts`
            attribute, specifically with details of its superclass relationships.

        Raises:
            TypeError: If the input class body is not a valid class definition or does not match the
                expected structure.
        """
        self._imports = item.source.get_imports()
        self._module = item.source.canonical_id
        match next(drop(1, walk(parse(item.body)))):
            case ClassDef(bases=bases):
                item.facts.set(
                    'superclass',
                    list(map(compose(self._get_canonical_base_name, self._parse_superclass), bases))
                )
                yield item
            case _: raise TypeError("Invalid class definition")

    def _get_canonical_base_name(self, name: str) -> str:
        if name in self._imports:
            return self._imports[name]
        if '.' in name:
            base_mod, *path = name.split('.')
            if base_mod in self._imports:
                return f'{self._imports[base_mod]}.{".".join(path)}'
        return f'{self._module}.{name}'


    @singledispatchmethod
    def _parse_superclass(self, base) -> str:
        return str(base)

    @_parse_superclass.register
    def _parse_name(self, base: Name) -> str:
        return base.id

    @_parse_superclass.register
    def _parse_subscript(self, base: Subscript) -> str:
        return self._parse_superclass(base.value)

    @_parse_superclass.register
    def _parse_attribute(self, base: Attribute) -> str:
        return f'{self._parse_superclass(base.value)}.{self._parse_superclass(base.attr)}'


@dataclass(frozen=True)
class PythonMethodConfig(FilterConfig):
    ignore_special_methods: bool = False
    ignore_private: bool = False




class PythonMethodFilter(Filter[PythonClass, ClassMethod, PythonMethodConfig]):
    """A filter for processing methods in Python classes based on specific criteria.

    This class provides functionality to iterate through a Python class's methods
    and yield only those that meet the conditions specified in the configuration.
    It is particularly useful for selectively working with special or private
    methods in Python classes.

    Attributes:
        name (str): The name of the filter instance.
        config (PythonMethodConfig): Configuration settings that define filtering
            criteria such as whether to ignore special or private methods.
    """
    provides_facts: ClassVar[frozenset[str]] = frozenset({'methods'})

    def __init__(self, name: str, config: PythonMethodConfig):
        super().__init__(name, config)


    def process(self, item: PythonClass) -> Iterable[ClassMethod]:
        for method in filter(self._keep_method, item.analyze_body()):
            item.facts.extend('methods', method.name)
            yield method


    def _keep_method(self, method: ClassMethod) -> bool:
        return not any(
            (
                method.name.startswith('__') and self.config.ignore_special_methods,
                method.name.startswith('_') and self.config.ignore_private
            )
        )


@dataclass(frozen=True)
class PythonStatementLengthConfig(FilterConfig):
    """
    Configuration class for defining the maximum length of Python statements.

    This class is used to specify and store configuration settings related to the
    maximum permissible length of Python statements. The configuration can be used
    to manage and enforce limits on statement lengths in various code analysis
    tools or frameworks.

    Attributes:
        max_length (int): Maximum allowed length for Python statements.
    """
    max_length: int = 10


class PythonStatementLengthFilter(Filter[PythonClass | ClassMethod, PythonClass | ClassMethod, PythonStatementLengthConfig]):
    """
    Filters Python classes or methods based on statement length.

    The class processes PythonClass or ClassMethod objects to determine the number
    of non-empty, stripped statement lines in their body text. It sets corresponding
    facts, such as statement_length and whether the statement is too long based on
    the provided maximum length configuration.

    Attributes:
        name (str): The name of the filter instance.
        config (PythonStatementLengthConfig): Configuration object containing the
            maximum statement length allowed.
    """
    provides_facts: ClassVar[frozenset[str]] = frozenset({'statement_length', 'statement_to_long'})

    def __init__(self, name: str, config: PythonStatementLengthConfig):
        super().__init__(name, config)

    def process(self, item: PythonClass | ClassMethod) -> Iterable[PythonClass | ClassMethod]:
        """
        Processes an input item to calculate statement length and evaluate whether
        the statement is too long based on configuration parameters. Updates the item's
        facts with the calculated length and the boolean result of the length check.

        Args:
            item: An instance of PythonClass or ClassMethod, representing the input
                item to be processed.

        Yields:
            Iterable[PythonClass | ClassMethod]: The modified input item with updated
                facts reflecting statement length and whether it exceeds the maximum
                allowed length.
        """
        length: int = count(filter(None, map(str.strip, item.body.splitlines())))
        item.facts.set('statement_length', length)
        item.facts.set('statement_to_long', length > self.config.max_length)
        yield item


@dataclass(frozen=True)
class PythonCyclicComplexityConfig(FilterConfig):
    """
    Represents the configuration for Python cyclic complexity analysis.

    This class is used to define the configuration options for analyzing Python
    cyclic complexity. It extends the `FilterConfig` class and includes specific
    attributes relevant to the cyclic complexity configuration. The configuration
    is immutable.

    Attributes:
        method (Literal["simple"]): Specifies the method used for complexity
            analysis. The default value is 'simple'.
    """
    method: Literal["simple"] = 'simple'


class PythonCyclicComplexityFilter(Filter[ClassMethod, ClassMethod, PythonCyclicComplexityConfig]):
    """
    A filter class for calculating and assigning cyclic complexity of Python class methods.

    This class processes Python class methods to calculate their cyclomatic
    complexity (a quantitative measure of the number of linearly independent
    paths through a program's source code) using a specified calculation method
    and assigns the calculated value as a fact for further processing.

    Attributes:
        name (str): The name of the filter.
        config (PythonCyclicComplexityConfig): Configuration options for
            specifying cyclic complexity calculation method.
    """
    provides_facts: ClassVar[frozenset[str]] = frozenset({'cyclic_complexity'})

    def __init__(self, name: str, config: PythonCyclicComplexityConfig):
        super().__init__(name, config)

    def process(self, item: ClassMethod) -> Iterable[ClassMethod]:
        """Processes an item by calculating its cyclic complexity based on the configured method.

        This method determines the cyclic complexity of the given item by evaluating it against
        the specified method in the configuration. The processed item is updated with the
        computed complexity and then yielded. If the configuration method is invalid, an error
        is raised.

        Args:
            item (ClassMethod): The item representing the method to be processed. It must be a
                valid object with relevant properties required for complexity calculation.

        Yields:
            ClassMethod: The processed item with updated cyclic complexity based on the
                configuration.

        Raises:
            ValueError: If the configured method specified in `self.config.method` is invalid.
        """
        complexity: int = 1
        match self.config.method:
            case 'simple': complexity = self._simple_complexity(item)
            case _: raise ValueError(f"Invalid method: {self.config.method}")
        item.facts.set('cyclic_complexity', complexity)
        yield item


    def _simple_complexity(self, item: ClassMethod) -> int:
        complexity: int = 1
        for node in walk(parse(item.body)):
            match node:
                case If() | IfExp() | ExceptHandler() | For() | While(): complexity += 1
                case Match(cases=cases): complexity += len(cases)
        return complexity