import re

from telethon._impl.mtsender import RpcError

_code_cache: dict[int, type[RpcError]] = {}
_name_cache: dict[str, type[RpcError]] = {}
_rpc_cache: dict[tuple[int, str], type[RpcError]] = {}


def canonicalize_code(code: int) -> int:
    return abs(code)  # -503 Timeout -> 503


def canonicalize_name(name: str) -> str:
    return name.upper()  # -503 Timeout -> TIMEOUT


def adapt_user_name(name: str) -> str:
    return re.sub(r"[A-Z]", lambda m: "_" + m[0].lower(), name).strip("_").upper()


def pretty_name(name: str) -> str:
    return "".join(map(str.title, name.split("_")))


def from_code(code: int) -> type[RpcError]:
    code = canonicalize_code(code)
    if code not in _code_cache:
        _code_cache[code] = type(f"Code{code}", (RpcError,), {})
    return _code_cache[code]


def from_name(name: str) -> type[RpcError]:
    name = canonicalize_name(name)
    if name not in _name_cache:
        _name_cache[name] = type(pretty_name(name), (RpcError,), {})
    return _name_cache[name]


def adapt_rpc(error: RpcError) -> RpcError:
    code = canonicalize_code(error.code)
    name = canonicalize_name(error.name)
    tup = code, name
    if tup not in _rpc_cache:
        _rpc_cache[tup] = type(
            pretty_name(name), (from_code(code), from_name(name)), {}
        )
    return _rpc_cache[tup](
        code=error.code, name=error.name, value=error.value, caused_by=error.caused_by
    )


class ErrorFactory:
    __slots__ = ()

    def __getattr__(self, name: str) -> type[RpcError]:
        if m := re.match(r"Code(\d+)$", name):
            return from_code(int(m[1]))
        else:
            adapted = adapt_user_name(name)
            if pretty_name(canonicalize_name(adapted)) != name or re.match(
                r"[A-Z]{2}", name
            ):
                raise AttributeError(f"error subclass names must be CamelCase: {name}")
            return from_name(adapted)


errors = ErrorFactory()
