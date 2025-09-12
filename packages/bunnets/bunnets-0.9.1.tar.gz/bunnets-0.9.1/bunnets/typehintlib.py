import builtins
import datetime as _datetime
from datetime import datetime
from enum import Enum
from types import GenericAlias, UnionType, NoneType
from typing import Any

from .error import InvalidInputError, _UndefinedObj, UnresolvableTypeError


FALSY_WORDS = [
    ":(",
    "bad",
    "decline",
    "denied",
    "deny",
    "erroneous",
    "error",
    "f",
    "fail",
    "failed",
    "failing",
    "fails",
    "failure",
    "failures",
    "false",
    "incorrect",
    "n",
    "nah",
    "nay",
    "negative",
    "negatory",
    "nein",
    "never",
    "no",
    "non",
    "nope",
    "nyet",
    "refuse",
    "truen't",
    "unsuccessful",
    "wrong",
    "yesn't",
]

TRUEABLE_WORDS = [
    "accept",
    "accepted",
    "affirm",
    "affirmative",
    "agree",
    "allow",
    "alright",
    "approve",
    "approved",
    "comply",
    "confirm",
    "consent",
    "cool",
    "da",
    "enable",
    "enabled",
    "e",
    "grant",
    "ja",
    "okay",
    "ok",
    "on",
    "pass",
    "passed",
    "permit",
    "please",
    "sure",
    "taxed",
    "true",
    "tru",
    "t",
    "valid",
    "yeag",
    "yeah",
    "yea",
    "yes",
    "yass",
    "yay",
    "y",
]

REPLACABLE_CHARS_ENUM = " /()"


def enum_str(instr: str, withchar: str) -> str:
    for char in REPLACABLE_CHARS_ENUM:
        instr = instr.replace(char, withchar)
    return instr


def coerce_type[Ti, Td](have: Ti, want: Td, need: bool = False) -> Ti | Td:
    """Function to coerce a given input Ti to type Td, optionally raising an InvalidInputError if impossible.

    If the given input is already of type Td, it is returned as-is.
    Otherwise, this function follows the given chain of logic:

    * If Td is an Enum or a member thereof, attempt to coerce input into a member of Td.
    * If input is a value known to the enum, the primary member with that value is returned
    * If input is the name of a member of the enum, that member is returned
    * If input, case insensitive, is the name or value of any member in the enum, that member is
        returned
    * If none of the above, return None (or exception)
    * If Td is a bool, attempt to coerce input to a boolean value by casting the input to a string,
        then checking if it is empty, zero, one, or a member of TRUEABLE_WORDS or FALSY_WORDS.
        Previously, this would treat any non-trueable string as false, but if the input is
        neither trueable nor falsy, the coercion fails.
    * If Td is a datetime, attempt to pass input as an integer to datetime.fromtimestamp
    * If Td is a datetime and attempt to parse as timestamp fails, attempt to pass input
        to datetime.fromisoformat
    * If none of the above, attempts to produce Td by calling Td(input). Works well for Typed objects.
    * if none of the above, return False

    Args:
        have (Ti): Arbitrary data to be coerced.
        want (Td): The desired type for `have`, or if `need` is False, a default value.
        need (bool, optional): Whether to raise an exception on coercion failure. Defaults to False.

    Returns:
        Td | Ti: Returns either the input (have) coerced to type Td (want)
                    or, if Td is not directly a type, returns Td. Otherwise returns input.
    """

    def _coerce(_have: Ti, _want: Td, _need: bool) -> Td | Ti | None:
        # required because otherwise str(None) returns "None"
        if isinstance(_want, type) and _have is None:
            return _have
        if not isinstance(_want, type):
            _want = type(_want)
        if type(_have) is _want or isinstance(_want, type(None)):
            return _have
        if isinstance(_want, type(Enum)):
            # Enum(Item) returns the enum member corresponding to the value
            #  ie. for Example(Enum): A=1, Example(1) will return Example.A
            #  and Example('A') will throw a ValueError
            try:
                return _want(_have)
            except ValueError:
                # Enum[Item] returns the enum member corresponding to the name
                #  ie. for Example(Enum): A=1, Example['A'] will return Example.A
                #  and Example[1] will throw a KeyError
                try:
                    return _want[_have]
                except KeyError:
                    # Hail Mary - case-insensitively search for an enum member which has either a
                    #  matching name or value, both with and without spaces
                    # TODO: Work out a way of doing this without using _member_map_
                    for name in _want._member_map_.keys():
                        if name.upper() == str(_have).upper():
                            return _want[name]
                    # Replace spaces and slashes with underscores
                    for name in _want._member_map_.keys():
                        if name.upper() == enum_str(str(_have).upper(), "_"):
                            return _want[name]
                    # Strip spaces and slashes
                    for name in _want._member_map_.keys():
                        if name.upper() == enum_str(str(_have).upper(), ""):
                            return _want[name]
                    for member in _want:
                        if member.name.upper() == str(_have).upper():
                            return _want[member.name]
                        if member.name.upper() == enum_str(str(_have).upper(), "_"):
                            return _want[member.name]
                        if member.name.upper() == enum_str(str(_have).upper(), ""):
                            return _want[member.name]
                        if str(member.value).upper() == str(_have).upper():
                            return _want(member.value)
                        if str(member.value).upper() == enum_str(str(_have).upper(), "_"):
                            return _want(member.value)
                        if str(member.value).upper() == enum_str(str(_have).upper(), ""):
                            return _want(member.value)
                    # If we reach this point, there is no possibility of automatically turning `O`
                    #  into a member of the given Enum.
                    if _need:
                        raise InvalidInputError(
                            "Unable to coerce input value to a member of desired enum"
                        )
                    return None
        match _want:
            case builtins.bool:
                # Have to cast O to string, because O could be anything.
                #  Goodness, what if it were an int?
                is_true = str(_have).lower() in ("1", *TRUEABLE_WORDS)
                is_false = str(_have).lower() in ("", "0", *FALSY_WORDS)
                if is_true:
                    return True
                if is_false:
                    return False
                return None
            case _datetime.datetime:
                _have = _coerce(_have, int, False)
                try:
                    return datetime.fromtimestamp(_have)
                except Exception:
                    # so gross
                    try:
                        return datetime.fromisoformat(_have)
                    except Exception:
                        return None
            case _:
                # Ultimate fallback: Hope that you can instantiate Td with input
                returnval = None
                try:
                    returnval = _want(_have)
                except Exception:
                    if not _need:
                        returnval = _have
                finally:
                    return returnval

    output = _coerce(have, want, need)
    if need and output is None:
        if not isinstance(want, type):
            want = type(want)
        raise InvalidInputError(f"Coercion error: Coerce to type {want} required, but impossible.")
    return output


def apply_typehint(inval: Any, hint: Any, parent_is_nullable: bool = False) -> Any:
    if isinstance(hint, GenericAlias) or isinstance(hint, UnionType):
        return Typehint(hint).resolve(inval, parent_is_nullable=parent_is_nullable)
    return coerce_type(inval, hint, True)


class Typehint:
    _t: Any

    def __init__(self, _t: Any):
        self._t = _t

    @property
    def debug(self):
        print("debug!")
        print(f"  type:             {type(self._t)}({self._t})")
        print(f"  origin:           {type(self.origin)}({self.origin})")
        print(
            f"  args:             {type(self.args)}({[f'{type(a)}({a})' for a in self.args] if self.args else None})"
        )
        print("  flags:")
        print(f"    is_union:       {self.is_union}")
        print(f"    is_subtyped: :  {self.is_subtyped}")
        print(f"    is_optional:    {self.is_optional}")
        return None

    @property
    def is_union(self) -> bool:
        """
        Returns whether the typehint is a Union (type | type ...)
        """
        return isinstance(self._t, UnionType)

    @property
    def is_subtyped(self) -> bool:
        """
        Returns whether the typehint has inner types (type[...])
        """
        return isinstance(self._t, GenericAlias)

    @property
    def is_optional(self) -> bool:
        """
        Returns whether a typehint is optional (type ... | None)
        """
        return self.is_union and NoneType in self.args

    @property
    def origin(self) -> type | None:
        """
        If subtyped, returns the origin (the 'type' in type[...])
        """
        if not self.is_subtyped:
            return None
        return getattr(self._t, "__origin__", None)

    @property
    def args(self) -> tuple | None:
        """
        If union or subtyped, returns the list of types to iterate over (the '...' in type[...] or type | ...)
        """
        return getattr(self._t, "__args__", None)

    def resolve(self, inval: Any, parent_is_nullable: bool = False) -> Any:
        """
        Resolves a typehint for the input value
        Follows the steps:
        * If the typehint is not a union, nor has subtypes, directly call apply_typehint with the input
        * If the typehint is a union, iterate over all members of the union
        ** Call apply_typehint for each member
        ** If no exception is raised, break out of the loop
        *** Else, skip to the next member
        ** If the input could not be resolved to a final typehint and coerced, set return value to None or raise error
        * If the typehint is subtyped, uhhhh
        """
        if self.is_optional:
            parent_is_nullable = True
        if not self.is_union and not self.is_subtyped:
            return apply_typehint(inval, self._t, parent_is_nullable=parent_is_nullable)
        if self.is_union:
            rtn = _UndefinedObj()
            for cls in self.args:
                try:
                    rtn = apply_typehint(inval, cls, parent_is_nullable=parent_is_nullable)
                    break
                except InvalidInputError:
                    # Skip to next type
                    continue
            if isinstance(rtn, _UndefinedObj):
                if not self.is_optional:
                    if not parent_is_nullable:
                        raise UnresolvableTypeError()
                    raise InvalidInputError("")
                rtn = None
            return rtn
        if self.is_subtyped:
            match self.origin:
                case builtins.dict:
                    if len(self.args) != 2:
                        if not self.is_optional:
                            if not parent_is_nullable:
                                raise UnresolvableTypeError()
                            raise InvalidInputError("")
                        return None
                    Tk, Tv = self.args
                    try:
                        return {
                            apply_typehint(
                                k, Tk, parent_is_nullable=parent_is_nullable
                            ): apply_typehint(v, Tv, parent_is_nullable=parent_is_nullable)
                            for k, v in inval.items()
                        }
                    except AttributeError:
                        raise InvalidInputError("")
                case builtins.list | builtins.tuple:
                    if len(self.args) != 1:
                        if not self.is_optional:
                            if not parent_is_nullable:
                                raise UnresolvableTypeError()
                            raise InvalidInputError("")
                        return None
                    return self.origin(
                        [
                            apply_typehint(v, self.args[0], parent_is_nullable=parent_is_nullable)
                            for v in inval
                        ]
                    )
            raise UnresolvableTypeError()
        return apply_typehint(inval, self._t, parent_is_nullable=parent_is_nullable)


def apply_typehints(target: Any, hint: Any, is_optional: bool = False) -> Any:
    return Typehint(hint).resolve(target, parent_is_nullable=is_optional)
