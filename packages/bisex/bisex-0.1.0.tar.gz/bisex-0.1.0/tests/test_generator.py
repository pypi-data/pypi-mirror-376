import unittest
import tempfile
from pathlib import Path

from bisex import TsGen
import ast


PY_SRC = """
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Optional, Union, TypedDict

@dataclass
class User:
    name: str
    age: int
    tags: List[str]
    meta: Dict[str, int]
    nickname: Optional[str]
    rating: Union[int, float]

class Kind(Enum):
    A = "a"
    B = 2
    C = 1 + 1

# Python 3.12+ syntax (optional)
try:
    from typing import TypeAlias  # noqa: F401
    type MyId = int | str
except Exception:
    pass

class UInfo(TypedDict):
    id: int
    label: str
"""


class TestTsGen(unittest.TestCase):
    def test_static_types_generation(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "types.py"
            out = Path(td) / "out.ts"
            src.write_text(PY_SRC, encoding="utf-8")

            gen = TsGen(py_types=[src], out_ts=out)
            ts = gen.produce_ts()

            # Interface
            self.assertIn("export interface User {", ts)
            self.assertIn("name: string;", ts)
            self.assertIn("age: number;", ts)
            self.assertIn("tags: (string)[];", ts)
            self.assertIn("meta: Record<string, number>;", ts)
            self.assertIn("nickname: string | null;", ts)
            self.assertIn("rating: number | number;", ts)  # int | float → number | number

            # Enum
            self.assertIn("export enum Kind {", ts)
            self.assertIn('A = "a"', ts)
            self.assertIn("B = 2", ts)
            # Non-literal becomes its name as string
            self.assertIn('C = "C"', ts)

            # TypeAlias (only on 3.12+) – gate by ast support
            if hasattr(ast, "TypeAlias"):
                self.assertIn("export type MyId = number | string;", ts)

            # TypedDict → interface
            self.assertIn("export interface UInfo {", ts)
            self.assertIn("id: number;", ts)
            self.assertIn("label: string;", ts)

    def test_interface_generation(self):
        gen = TsGen(py_types=[], out_ts=Path("dummy"))

        @gen.interface("API")
        def ping(name: str) -> None:  # noqa: ANN001
            ...

        @gen.interface("API")
        def add(a: int, b: int) -> int:  # noqa: ANN001
            ...

        @gen.interface("API")
        def maybe(x: str | None) -> str | None:  # noqa: ANN001
            ...

        ts = gen.produce_ts()
        self.assertIn("export interface API {", ts)
        self.assertIn("ping: (name: string) => null;", ts)
        self.assertIn("add: (a: number, b: number) => number;", ts)
        self.assertIn("maybe: (x: string | null) => string | null;", ts)

    def test_return_wrapper(self):
        gen = TsGen(py_types=[], out_ts=Path("dummy"), return_wrapper="() => Promise<{ret}>")

        @gen.interface("Svc")
        def hello(x: str) -> None:  # noqa: ANN001
            ...

        ts = gen.produce_ts()
        self.assertIn("export interface Svc {", ts)
        self.assertIn("hello: (x: string) => () => Promise<null>;", ts)

    def test_annotation_coverage(self):
        from typing import Callable, Literal, Annotated, Mapping, MutableMapping, Sequence, Iterable, Type, Dict

        gen = TsGen(py_types=[], out_ts=Path("dummy"))

        @gen.interface("More")
        def f_list(a: list[int]) -> list[str]:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_seq(a: Sequence[str]) -> Sequence[int]:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_map(m: dict[str, float]) -> Dict[str, float]:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_mapping(m: Mapping[str, int]) -> MutableMapping[str, int]:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_set(s: set[int]) -> set[int]:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_call(cb: Callable[[int, str], bool]) -> None:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_ann(x: Annotated[int, "meta"]) -> Annotated[str, "m"]:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_lit(x: Literal['a', 1, True]) -> Literal['b']:  # noqa: ANN001
            ...

        @gen.interface("More")
        def f_type(t: Type[str]) -> Type[int]:  # noqa: ANN001
            ...

        ts = gen.produce_ts()
        self.assertIn("export interface More {", ts)
        self.assertIn("f_list: (a: (number)[]) => (string)[];", ts)
        self.assertIn("f_seq: (a: (string)[]) => (number)[];", ts)
        self.assertIn("f_map: (m: Record<string, number>) => Record<string, number>;", ts)
        self.assertIn("f_mapping: (m: Record<string, number>) => Record<string, number>;", ts)
        self.assertIn("f_set: (s: Set<number>) => Set<number>;", ts)
        self.assertIn("f_call: (cb: (a1: number, a2: string) => boolean) => null;", ts)
        self.assertIn("f_ann: (x: number) => string;", ts)
        self.assertIn("f_lit: (x: \"a\" | 1 | true) => \"b\";", ts)
        self.assertIn("f_type: (t: new (...args: any[]) => string) => new (...args: any[]) => number;", ts)

    def test_type_alias_variants(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "types.py"
            out = Path(td) / "out.ts"
            src.write_text(
                """
from typing import Optional, TypeAlias

# Simple assignment alias
MyNum = int

# Annotated TypeAlias form
UserId: TypeAlias = str

# More complex type expression
MaybeStr: TypeAlias = Optional[str]

# Non-alias assignments should be ignored
VERSION = "1.0.0"
FLAGS = 3
""",
                encoding="utf-8",
            )

            gen = TsGen(py_types=[src], out_ts=out)
            ts = gen.produce_ts()

            # Aliases
            self.assertIn("export type MyNum = number;", ts)
            self.assertIn("export type UserId = string;", ts)
            self.assertIn("export type MaybeStr = string | null;", ts)

            # Non-alias constants are not converted
            self.assertNotIn("export type VERSION", ts)
            self.assertNotIn("export type FLAGS", ts)

    def test_enum_negative_and_float(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "types.py"
            out = Path(td) / "out.ts"
            src.write_text(
                """
from enum import Enum

class K(Enum):
    NEG = -1
    PI = 3.14
    NAME = "n"
    SUM = 1 + 2  # not a literal; becomes name string
""",
                encoding="utf-8",
            )

            gen = TsGen(py_types=[src], out_ts=out)
            ts = gen.produce_ts()

            self.assertIn("export enum K {", ts)
            self.assertIn("NEG = -1", ts)
            self.assertIn("PI = 3.14", ts)
            self.assertIn('NAME = "n"', ts)
            self.assertIn('SUM = "SUM"', ts)


if __name__ == "__main__":
    unittest.main()
