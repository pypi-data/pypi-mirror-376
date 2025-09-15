from __future__ import annotations

"""
Core generator for Python → TypeScript declarations.

Features
- Parse static types (dataclasses, Enums, TypedDicts, type aliases) from .py
  files via AST (no runtime import side effects).
- Capture Python function signatures (type‑annotated) into TS interfaces via a
  decorator.
- Emit a single .ts file with all collected declarations.

Typing coverage (runtime annotations)
- Primitives, None → string/number/boolean/null
- list/List/Sequence/MutableSequence/Iterable[T] → (T)[]
- dict/Dict/Mapping/MutableMapping[K, V] → Record<K, V>
- set/Set/frozenset/FrozenSet/AbstractSet[T] → Set<T>
- tuple[Ts] → [T1, T2, ...]; tuple[T, ...] → (T)[]
- Union/Optional[Ts] → unions with null for NoneType
- Literal[...] → union of literal types
- Annotated[T, ...] → T
- Callable[[Args], Ret] → ((...args) => Ret) with arg names a1, a2, … where
  needed
- Type[T] → new (...args: any[]) => T
"""

import ast
import inspect
from pathlib import Path
from typing import (
    Any,
    Final,
    Iterable,
    List,
    Tuple,
    get_args,
    get_origin,
    get_type_hints,
)
import typing as _t
import collections.abc as _abc


# ----------------------------- Maps & helpers -----------------------------

PY_PRIMITIVE_TO_TS: Final[dict[str, str]] = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "None": "null",
    "NoneType": "null",
    "Any": "any",
}


def _map_primitive(name: str) -> str:
    """Map a Python primitive name to a TypeScript type string."""
    return PY_PRIMITIVE_TO_TS.get(name, name)


# ----------------------------- AST → TS types -----------------------------

class _TypeScriptMapper:
    """Translate Python AST and runtime annotations to TypeScript strings.

    This internal helper keeps the conversion logic cohesive and testable.
    """

    # ---- AST → TS -----------------------------------------------------
    def ts_from_ast(self, expr: ast.AST) -> str:
        """Translate a Python type expression AST into a TS type string."""
        match expr:
            case ast.Name(id=name):
                return _map_primitive(name)
            case ast.Attribute(attr=attr):
                if attr in {"List", "Dict", "Union", "Optional"}:
                    return attr
                return _map_primitive(attr)
            case ast.BinOp(left=l, op=ast.BitOr(), right=r):
                return f"{self.ts_from_ast(l)} | {self.ts_from_ast(r)}"
            case ast.Subscript(value=v, slice=s):
                base = None
                if isinstance(v, ast.Name):
                    base = v.id
                elif isinstance(v, ast.Attribute):
                    base = v.attr

                if isinstance(s, ast.Index):  # py<3.9 wrapper  # type: ignore[attr-defined]
                    s = s.value  # type: ignore[attr-defined]

                if base in {"List", "list"}:
                    return f"({self.ts_from_ast(s)})[]"
                if base in {"Dict", "dict"}:
                    if isinstance(s, ast.Tuple) and len(s.elts) == 2:
                        k, v = s.elts
                    else:
                        k = v = ast.Name(id="Any")
                    return f"Record<{self.ts_from_ast(k)}, {self.ts_from_ast(v)}>"
                if base == "Union":
                    if isinstance(s, ast.Tuple):
                        return " | ".join(self.ts_from_ast(e) for e in s.elts)
                    return self.ts_from_ast(s)
                if base == "Optional":
                    return f"{self.ts_from_ast(s)} | null"
                return "any"
            case ast.Constant(value=v):
                if v is None:
                    return "null"
                if isinstance(v, str):
                    return "string"
                if isinstance(v, (int, float)):
                    return "number"
                if isinstance(v, bool):
                    return "boolean"
                return "any"
            case _:
                return "any"

    # ---- Runtime annotations → TS ------------------------------------
    @staticmethod
    def string_anno_to_ts(text: str) -> str:
        """Best‑effort conversion for string annotations into TS types."""
        import re as _re
        s = text.strip()
        mapping = [
            (r"\bNone\b", "null"),
            (r"\bstr\b", "string"),
            (r"\bint\b", "number"),
            (r"\bfloat\b", "number"),
            (r"\bbool\b", "boolean"),
        ]
        for pat, rep in mapping:
            s = _re.sub(pat, rep, s)
        return s

    def anno_to_ts(self, anno: Any) -> str:
        """Translate a runtime annotation (typing) into a TS type string."""
        if isinstance(anno, str):
            return self.string_anno_to_ts(anno)
        if anno is None or anno is type(None):  # noqa: E721
            return "null"
        origin = get_origin(anno)
        args = get_args(anno)

        if origin in (list, List, _t.Sequence, _t.MutableSequence, _t.Iterable, _abc.Sequence, _abc.MutableSequence, _abc.Iterable):
            inner = self.anno_to_ts(args[0]) if args else "any"
            return f"({inner})[]"
        if origin in (dict, _t.Dict, _t.Mapping, _t.MutableMapping, _abc.Mapping, _abc.MutableMapping):
            k = self.anno_to_ts(args[0]) if len(args) >= 1 else "any"
            v = self.anno_to_ts(args[1]) if len(args) >= 2 else "any"
            return f"Record<{k}, {v}>"
        if origin in (set, _t.Set, _t.AbstractSet, _t.FrozenSet, frozenset, _abc.Set):
            inner = self.anno_to_ts(args[0]) if args else "any"
            return f"Set<{inner}>"
        if origin in (tuple, Tuple):
            inner = ", ".join(self.anno_to_ts(a) for a in args)
            return f"[{inner}]"
        if origin is None and isinstance(anno, type):
            return _map_primitive(getattr(anno, "__name__", "any"))
        if args and (str(origin).endswith("typing.Union") or str(origin).endswith("UnionType")):
            parts: list[str] = []
            for a in args:
                parts.append("null" if a is type(None) else self.anno_to_ts(a))  # noqa: E721
            seen: set[str] = set()
            uniq = [p for p in parts if not (p in seen or seen.add(p))]
            return " | ".join(uniq)
        if origin in (_t.Literal, getattr(_t, "Literal", None)):
            lits: list[str] = []
            for val in args:
                if isinstance(val, str):
                    lits.append(f'"{val}"')
                elif isinstance(val, bool):
                    lits.append("true" if val else "false")
                elif isinstance(val, (int, float)):
                    lits.append(str(val))
            return " | ".join(lits) if lits else "any"
        if origin in (_t.Annotated, getattr(_t, "Annotated", None)) and args:
            return self.anno_to_ts(args[0])
        if origin in (_t.Callable, _abc.Callable):
            if args:
                try:
                    param_list, ret = args
                except ValueError:
                    param_list, ret = args[:-1], args[-1]
                if param_list is Ellipsis:
                    params_ts = "...args: any[]"
                else:
                    ptypes = param_list if isinstance(param_list, (list, tuple)) else []
                    params_ts = ", ".join(
                        f"a{i+1}: {self.anno_to_ts(t)}" for i, t in enumerate(ptypes)
                    ) or ""
                ret_ts = self.anno_to_ts(ret)
                return f"({params_ts}) => {ret_ts}"
            return "(...args: any[]) => any"
        if origin in (_t.Type, type):
            inner = self.anno_to_ts(args[0]) if args else "any"
            return f"new (...args: any[]) => {inner}"
        name = getattr(anno, "__name__", None) or str(anno)
        return _map_primitive(name)


# Single shared mapper (keeps functions below as thin wrappers)
_MAPPER = _TypeScriptMapper()


def _ts_from_ast(expr: ast.AST) -> str:
    """Compatibility wrapper – use the shared mapper for AST conversion."""
    return _MAPPER.ts_from_ast(expr)
    match expr:
        case ast.Name(id=name):
            return _map_primitive(name)
        case ast.Attribute(attr=attr):
            # typing.List, typing.Dict, typing.Union, typing.Optional
            if attr in {"List", "Dict", "Union", "Optional"}:
                return attr  # handled in Subscript below
            return _map_primitive(attr)
        case ast.BinOp(left=l, op=ast.BitOr(), right=r):
            return f"{_ts_from_ast(l)} | {_ts_from_ast(r)}"
        case ast.Subscript(value=v, slice=s):
            # Resolve value's "name"
            base = None
            if isinstance(v, ast.Name):
                base = v.id
            elif isinstance(v, ast.Attribute):
                base = v.attr

            # py<3.9 Index wrapper
            if isinstance(s, ast.Index):  # type: ignore[attr-defined]
                s = s.value  # type: ignore[attr-defined]

            if base in {"List", "list"}:
                return f"({_ts_from_ast(s)})[]"
            if base in {"Dict", "dict"}:
                if isinstance(s, ast.Tuple) and len(s.elts) == 2:
                    k, v = s.elts
                else:
                    k = v = ast.Name(id="Any")
                return f"Record<{_ts_from_ast(k)}, {_ts_from_ast(v)}>"
            if base == "Union":
                if isinstance(s, ast.Tuple):
                    return " | ".join(_ts_from_ast(e) for e in s.elts)
                return _ts_from_ast(s)
            if base == "Optional":
                return f"{_ts_from_ast(s)} | null"
            # Fallback generic
            return "any"
        case ast.Constant(value=v):
            if v is None:
                return "null"
            if isinstance(v, str):
                return "string"
            if isinstance(v, (int, float)):
                return "number"
            if isinstance(v, bool):
                return "boolean"
            return "any"
        case _:
            return "any"


def _base_is_enum(base: ast.expr) -> bool:
    return (isinstance(base, ast.Name) and base.id == "Enum") or (
        isinstance(base, ast.Attribute) and base.attr == "Enum"
    )


def _base_is_typed_dict(base: ast.expr) -> bool:
    return (isinstance(base, ast.Name) and base.id == "TypedDict") or (
        isinstance(base, ast.Attribute) and base.attr == "TypedDict"
    )


def _convert_enum(node: ast.ClassDef) -> str:
    members: list[tuple[str, str]] = []
    for stmt in node.body:
        if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
            name = getattr(stmt.targets[0], "id", None)
            if not name:
                continue
            value = stmt.value
            # Support string/int/float literals, including negative numbers
            lit: str | None = None
            if isinstance(value, ast.Constant) and isinstance(value.value, (str, int, float)):
                v = value.value
                if isinstance(v, str):
                    lit = f'"{v}"'
                else:
                    lit = str(v)
            elif isinstance(value, ast.UnaryOp) and isinstance(value.op, ast.USub) and isinstance(value.operand, ast.Constant) and isinstance(value.operand.value, (int, float)):
                lit = f"-{value.operand.value}"
            if lit is not None:
                members.append((name, lit))
            else:
                # Non‑literal: fallback to string member with its own name
                members.append((name, f'"{name}"'))

    body = "\n".join(f"  {k} = {v}," for k, v in members)
    return f"export enum {node.name} {{\n{body}\n}}"


def _convert_dataclass(node: ast.ClassDef) -> str:
    fields: list[tuple[str, str]] = []
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            ts_t = _ts_from_ast(stmt.annotation) if stmt.annotation else "any"
            fields.append((name, ts_t))
    body = "\n".join(f"  {n}: {t};" for n, t in fields)
    return f"export interface {node.name} {{\n{body}\n}}"


def _convert_typed_dict(node: ast.ClassDef) -> str:
    fields: list[tuple[str, str]] = []
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            ts_t = _ts_from_ast(stmt.annotation) if stmt.annotation else "any"
            fields.append((name, ts_t))
    body = "\n".join(f"  {n}: {t};" for n, t in fields)
    return f"export interface {node.name} {{\n{body}\n}}"


def _convert_typealias(node: Any) -> str:  # ast.TypeAlias on 3.12+
    name = node.name.id  # type: ignore[attr-defined]
    rhs = _ts_from_ast(node.value)  # type: ignore[attr-defined]
    return f"export type {name} = {rhs};"


def _is_type_expr_ast(expr: ast.AST) -> bool:
    """Heuristic: is this AST node a type expression that we can map to TS?

    Used to detect classic alias forms like `MyT = int | str` or
    `MyT: TypeAlias = list[int]`.
    We intentionally avoid treating plain constants (numbers/strings) as type
    aliases to prevent converting config constants into types.
    """
    match expr:
        case ast.Name():
            return True
        case ast.Attribute():
            return True
        case ast.Subscript(value=_, slice=_):
            return True
        case ast.BinOp(op=ast.BitOr(), left=l, right=r):
            return _is_type_expr_ast(l) and _is_type_expr_ast(r)
        case ast.Tuple(elts=elts):
            return all(_is_type_expr_ast(e) for e in elts)
        case ast.Constant(value=None):
            # Only None as a literal type; other constants are not treated as aliases
            return True
        case _:
            return False


def _maybe_convert_legacy_type_alias(node: ast.AST) -> str | None:
    """Return TS alias string if node looks like a legacy type alias.

    Supports:
    - `Name: TypeAlias = <type expr>`
    - `Name = <type expr>` where the RHS looks like a type expression
    """
    # Annotated alias:  MyT: TypeAlias = int | str
    if isinstance(node, ast.AnnAssign):
        target = node.target
        anno = node.annotation
        value = node.value
        if (
            isinstance(target, ast.Name)
            and value is not None
            and (
                (isinstance(anno, ast.Name) and anno.id == "TypeAlias")
                or (isinstance(anno, ast.Attribute) and anno.attr == "TypeAlias")
            )
            and _is_type_expr_ast(value)
        ):
            name = target.id
            rhs = _ts_from_ast(value)
            return f"export type {name} = {rhs};"

    # Simple assignment alias: MyT = list[int] / int | str / Optional[str]
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        target = node.targets[0]
        value = node.value
        if isinstance(target, ast.Name) and _is_type_expr_ast(value):
            name = target.id
            rhs = _ts_from_ast(value)
            return f"export type {name} = {rhs};"

    return None


def _python_file_to_ts(path: Path) -> str:
    if not Path(path).exists():
        return ""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    parts: list[str] = []
    # Walk entire tree so we see declarations nested under try/if/etc.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            if any(_base_is_enum(b) for b in node.bases):
                parts.append(_convert_enum(node))
            elif any(_base_is_typed_dict(b) for b in node.bases):
                parts.append(_convert_typed_dict(node))
            else:
                parts.append(_convert_dataclass(node))
        elif hasattr(ast, "TypeAlias") and isinstance(node, ast.TypeAlias):
            parts.append(_convert_typealias(node))
        else:
            maybe = _maybe_convert_legacy_type_alias(node)
            if maybe:
                parts.append(maybe)
    return "\n\n".join(p for p in parts if p)


# --------------------- Runtime annotations → TS ---------------------

def _string_anno_to_ts(text: str) -> str:
    """Compatibility wrapper – delegate to the shared mapper."""
    return _MAPPER.string_anno_to_ts(text)


def _anno_to_ts(anno: Any) -> str:
    """Compatibility wrapper – delegate to the shared mapper."""
    return _MAPPER.anno_to_ts(anno)


# --------------------------- Main façade ---------------------------


class TsGen:
    """Collect static types and function signatures → emit TypeScript.

    Parameters
    ----------
    py_types : str | Path | list[str|Path]
        Python files to scan (dataclasses, Enums, type aliases).
    out_ts : Path
        Output .ts file.
    return_wrapper : str | None
        Optional format string wrapping function return type, with `{ret}`
        placeholder. Example for Eel: "() => Promise<{ret}>".
    """

    def __init__(
        self,
        *,
        py_types: str | Path | Iterable[str | Path] = (),
        out_ts: Path | str = Path("types.generated.ts"),
        return_wrapper: str | None = None,
    ) -> None:
        self._py_files: list[Path] = []
        if isinstance(py_types, (str, Path)):
            if py_types:
                self._py_files = [Path(py_types)]
        else:
            self._py_files = [Path(p) for p in py_types]
        self._out_ts = Path(out_ts)
        self._wrapper = return_wrapper
        self._interfaces: dict[str, list[dict[str, Any]]] = {}

    # Decorator to capture functions
    def interface(self, name: str):
        """Decorator capturing the annotated signature of a function.

        The function is returned unmodified.
        """

        def deco(func):
            sig = inspect.signature(func)
            # Resolve forward refs / string annotations to real types
            try:
                hints = get_type_hints(func)
            except Exception:
                hints = getattr(func, "__annotations__", {}) or {}
            params = [
                (param_name or f"arg{idx}", _anno_to_ts(hints.get(param_name)))
                for idx, (param_name, _) in enumerate(sig.parameters.items())
            ]
            ret = _anno_to_ts(hints.get("return"))
            self._interfaces.setdefault(name, []).append(
                {"name": func.__name__, "params": params, "ret": ret}
            )
            return func

        return deco

    def _emit_static(self) -> str:
        blocks = [_python_file_to_ts(p) for p in self._py_files]
        return "\n\n".join(b for b in blocks if b)

    def _emit_interfaces(self) -> str:
        parts: list[str] = []
        for iface, funcs in self._interfaces.items():
            lines = []
            for f in funcs:
                params = ", ".join(
                    f"{n}: {_string_anno_to_ts(t) if isinstance(t, str) else t}"
                    for n, t in f["params"]
                ) or ""
                ret = f["ret"] or "void"
                if isinstance(ret, str):
                    ret = _string_anno_to_ts(ret)
                ret_ts = self._wrapper.format(ret=ret) if self._wrapper else ret
                lines.append(
                    f"  {f['name']}: ({params}) => {ret_ts};"
                )
            body = "\n".join(lines)
            parts.append(f"export interface {iface} {{\n{body}\n}}")
        return "\n\n".join(parts)

    def produce_ts(self) -> str:
        header = [
            "// This file is auto‑generated by bysex.",
            "// Do not edit manually.",
        ]
        static = self._emit_static()
        inter = self._emit_interfaces()
        return "\n\n".join([s for s in ["\n".join(header), static, inter] if s]).rstrip() + "\n"

    def generate(self) -> Path:
        out = self.produce_ts()
        self._out_ts.parent.mkdir(parents=True, exist_ok=True)
        self._out_ts.write_text(out, encoding="utf-8")
        return self._out_ts
