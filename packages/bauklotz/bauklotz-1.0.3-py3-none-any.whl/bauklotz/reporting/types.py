from collections.abc import Sequence, Mapping

type PrimitiveType = str | int | float | bool | None
type JSONType = PrimitiveType | Sequence['JSONType'] | Mapping[str, 'JSONType']
