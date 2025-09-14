from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from asteval import Interpreter

from bauklotz.business.filter import FilterConfig, Filter
from bauklotz.reporting.item import Item, Label
from bauklotz.reporting.types import JSONType


@dataclass(frozen=True)
class ComplexLabelConfig(FilterConfig):
    code: Path

    @property
    def content(self):
        with open(self.code) as src:
            return src.read().strip()


class ComplexLabelFilter[I: Item](Filter[I, I, ComplexLabelConfig]):
    def __init__(self, name: str, config: ComplexLabelConfig):
        super().__init__(name, config)
        self._code: str = config.content

    def process(self, item: I) -> Iterable[I]:
        interpreter: Interpreter = Interpreter()
        interpreter.symtable['facts'] = dict(item.facts.items())
        interpreter.symtable['labels'] = item.labels
        interpreter.symtable['item'] = item.serialize()
        interpreter(self._code)
        item.labels = Label(interpreter.symtable['labels'])
        yield item
