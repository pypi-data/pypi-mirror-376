from copy import deepcopy
from datetime import datetime
from enum import Enum
from types import UnionType, NoneType
from typing import Any, get_type_hints, Union

from .error import (
    ImmutableValueError,
    NonLockingError,
    ImmutableObjectError,
    UnresolvableTypeError,
    InvalidInputError,
)
from .func import hasattrs, lock, unlock
from .typehintlib import apply_typehints


class Lockable:
    """Simple mechanism for marking an object as supporting being made immutable.

    Can be used with `lock(obj)`, `unlock(obj)`, `locked(obj)` and `mutable(obj)`.
    Compatible implementations must have the following method signatures:
    - `__lock__() -> None` - Performs some action to make the called object immutable
    - `__locked__() -> bool` - Returns True or False to indicate the object's lock state
    Implementations that support being made mutable again must also implement the following:
    - `__unlock__() -> None` - Performs some action to make the called object mutable.

    When an object is locked, any attempts to write to any member/property/attribute of the object
    should raise an ImmutableValueError.
    When an object is locked and `__unlock__` is implemented, but making it mutable is not wanted,
    the method should raise an ImmutableObjectError.
    It is the responsibility of the implementing class to ensure the mutable state is enforced.
    """

    _mutable: bool

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._mutable = True

    def __lock__(self):
        self._mutable = False

    def __unlock__(self):
        self._mutable = True

    def __locked__(self) -> bool:
        return self._mutable is False


class Properties:
    """Simple dict-like object that exposes members as attributes/properties.
    Case-insensitive by default, and supports returning a default value.
    Supports being made immutable.
    """

    _case_sensitive: bool = None
    _catchall: Any | None = None
    _catchall_enabled: bool = None
    _inner: dict = None
    _mut: bool = True

    _special_keys: tuple[str] = ()
    _special: tuple[str] = (
        "_case_sensitive",
        "_catchall",
        "_catchall_enabled",
        "_inner",
        "_mut",
        "_special",
        "_special_keys",
    )

    def __init__(
        self,
        data: dict = None,
        of: dict = None,
        catchall: bool = None,
        default_value=None,
        case_sensitive: bool = None,
        **kwargs,
    ):
        """
        Creates a new Properties object
        :param data: An optional dict, or dict-like, to initialise this Properties object with.
            If not provided, kwargs can be used instead.
        :param of: Alias of the data parameter.
        :param catchall: Optional; if true, any missing value will have a default value returned.
        :param default_value: Optional; if not None, also sets catchall to true if not specified.
        :param case_sensitive: Optional; if True, does not lowercase all keys. Default False.
        """
        self._special += self._special_keys
        if catchall is not None:
            self._catchall_enabled = catchall
        else:
            self._catchall_enabled = default_value is not None
        self._catchall = default_value
        self._case_sensitive = case_sensitive or False
        self._mut = True

        self._inner = {}

        # This is almost certainly completely overkill.
        if data is None and of is not None:
            data = of
        if data is None and len(kwargs.keys()) > 0:
            data = kwargs
        if data is None or (hasattr(data, "keys") and len(data.keys()) == 0) or len(data) == 0:
            return
        if not hasattrs(data, any_of=("keys", "items", "__dict__")):
            raise ValueError("data object does not appear to be a dict")
        if hasattr(data, "__dict__") and not hasattrs(data, any_of=("items", "keys")):
            data = vars(data)
        if hasattr(data, "items"):
            for k, v in data.items():
                if not self._case_sensitive:
                    k = str(k).lower()
                self._inner[k] = self.__cast(v)
            return
        if hasattr(data, "keys"):
            for k in data.keys():
                if not self._case_sensitive:
                    k = str(k).lower()
                if hasattr(data, "__getitem__"):
                    self._inner[k] = self.__cast(data[k])
                elif hasattrs(data, "__getattr__", k):
                    self._inner[k] = self.__cast(getattr(data, k))
                else:
                    raise ValueError("data object has keys but no way to get their values?")
            return
        raise ValueError("data object could not be handled")

    def keys(self):
        return self._inner.keys()

    def values(self):
        return self._inner.values()

    def items(self):
        return self._inner.values()

    def __lock__(self):
        self._mut = False
        for i in self._inner:
            try:
                lock(i)
            except NonLockingError:
                if isinstance(i, (tuple, list, set)):
                    [
                        lock(attr)
                        for attr in i
                        if hasattr(attr, "__lock__") and callable(attr.__lock__)
                    ]

    def __unlock__(self):
        self._mut = True
        for i in self._inner:
            try:
                unlock(i)
            except ImmutableObjectError:
                continue
            except NonLockingError:
                if isinstance(i, (tuple, list, set)):
                    [
                        unlock(attr)
                        for attr in i
                        if hasattr(attr, "__lock__") and callable(attr.__lock__)
                    ]

    def __cast(self, _in):
        if isinstance(_in, dict) and not isinstance(_in, Properties):
            return Properties(
                data=_in,
                catchall=self._catchall_enabled,
                default_value=self._catchall,
                case_sensitive=self._case_sensitive,
            )
        if isinstance(_in, (tuple, list, set)):
            return type(_in)((self.__cast(_iter) for _iter in _in))
        return _in

    def __setitem__(self, key: str, value):
        if not self._mut:
            raise ImmutableValueError(key)
        if not self._case_sensitive:
            key = str(key).lower()
        self._inner[key] = self.__cast(value)

    def __setattr__(self, key: str, value):
        if hasattr(self, "_mut") and not self._mut and key != "_mut":
            raise ImmutableValueError(key)
        if key in self._special:
            return super().__setattr__(key, value)
        return self.__setitem__(key, value)

    def __delitem__(self, key):
        """
        If present, deletes the given name from the inner dict. If not present, raises a KeyError.
        Usage: `del properties[name]`
        """
        if not self._case_sensitive:
            key = key.lower()
        if key in self._special:
            raise AttributeError(key)
        if key not in self._inner.keys():
            raise KeyError(key)

        self._inner.pop(key)

    def __delattr__(self, name):
        """
        If present, deletes the given name from the inner dict. If not present, raises an AttributeError.
        Usage: `del properties.name`
        """
        if not self._case_sensitive:
            name = name.lower()
        if name in self._special or name not in self._inner.keys():
            raise AttributeError(name)
        self._inner.pop(name)

    @property
    def __dict__(self) -> dict:
        """Deserialises the Properties back to a primitive dict"""
        ret = {}
        for k, v in self._inner.items():
            if isinstance(v, Properties):
                ret[k] = vars(v)
            elif isinstance(v, (tuple, list, set)):
                ret[k] = [vars(iv) if isinstance(iv, Properties) else iv for iv in v]
            else:
                ret[k] = v
        return ret

    def __getattr__(self, key: str):
        if not self._case_sensitive:
            key = key.lower()
        if key not in self._inner.keys():
            if self._catchall_enabled:
                return self._catchall
            raise AttributeError(key)
        return self._inner[key]

    def __getitem__(self, item: str):
        if not self._case_sensitive:
            item = item.lower()
        if item not in self._inner.keys():
            if self._catchall_enabled:
                return self._catchall
            raise KeyError(item)
        return self._inner[item]

    def __repr__(self):
        return (
            f"<Properties n={len(self)} k=[{','.join(self._inner.keys())}] "
            f"cs={'y' if self._case_sensitive else 'n'} >"
        )

    def __str__(self) -> str:
        return str(self._inner)

    def __len__(self) -> int:
        return len(self._inner)

    def __contains__(self, item):
        if not self._case_sensitive:
            item = item.lower()
        return item in self._inner

    def __hash__(self) -> int:
        return self._inner.__hash__()


class SelectableDict(dict):
    """dict subclass providing an extremely simple XPath-style selector interface"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for k, v in self.items():
            self[k] = self.__enforce_type(v)

    def __setattr__(self, key, value):
        if not isinstance(value, SelectableDict) and isinstance(value, dict):
            value = SelectableDict(value)
        super().__setattr__(key, value)

    def __setitem__(self, key, value):
        if not isinstance(value, SelectableDict) and isinstance(value, dict):
            value = SelectableDict(key, value)
        super().__setitem__(key, value)

    def __enforce_type(self, _in):
        if isinstance(_in, dict) and not isinstance(_in, SelectableDict):
            return SelectableDict(_in)
        if isinstance(_in, list):
            return [self.__enforce_type(_iter) for _iter in _in]
        return _in

    def select[T](self, path: str) -> T:
        this_iter = self
        prog = "root"
        for segment in path.split("."):
            if isinstance(this_iter, list) and int(segment) in range(0, len(this_iter)):
                prog = ".".join([prog, segment])
                this_iter = this_iter[int(segment)]
            elif segment in this_iter.keys():
                prog = ".".join([prog, segment])
                this_iter = this_iter[segment]
            elif int(segment) in this_iter.keys():
                prog = ".".join([prog, segment])
                this_iter = this_iter[int(segment)]
            else:
                raise KeyError(
                    f"Key '{segment}' from selected path '{path}' not present "
                    f"(searched as far as '{prog}')"
                )
        return this_iter


class Typed:
    """A "dataclass on steroids" style class.
    Intended for data structures which have an uncomplicated input (for example, a dict returned
        from Requests' Response.json() method)


    Subclasses of this can define their entire structure using only typehints, eg:
    >>> class MySmallerClass(Typed):
    ...     some_flag: bool
    ...
    >>> class MyBiggerClass(Typed):
    ...     my_numbers: list[int]
    ...     my_complex_flags: dict[str, MySmallerClass]
    ...     something_optional: str | None
    ...
    >>> class_instance = MyBiggerClass({"my_numbers": ["1", "2", "9",], "my_complex_flags": {"something": {"some_flag": "yes"}, "something_else": {"some_flag": "no"}}})
    >>> class_instance
    <MyBiggerClass my_numbers=[1, 2, 9], my_complex_flags={'something': <MySmallerClass some_flag=True >, 'something_else': <MySmallerClass some_flag=False >}, something_optional=None >

    Sometimes you may wish to define a class with members that don't directly match the input object, for example
        a data model for a response from an API which uses camel-cased property names.
    For this purpose, you can define an alias, eg.:
    >>> class MyResponseData(Typed):
    ...     _aliases = {"my_attribute": "someAttribute",}
    ...     my_attribute: int
    >>> MyResponseData({"someAttribute": "9"})
    <MyResponseData some_attribute=9 >

    This can extend to structural differences. Imagine you're parsing the response from a JSON-RPC call. You can pass
        just the first "results" value from the response dict, but you can also have it done for you, eg:
    >>> class MyResponseData(Typed):
    ...     _aliases = {"my_attribute": "result.0.theAttribute"}
    ...     my_attribute: str
    >>> MyResponseData({"id": 1, "jsonrpc": "2.0", "result": [{"theAttribute": "Some Value"}]})
    <MyResponseData my_attribute=Some Value >

    You may also wish to make an attribute have a default value. This works much like you'd expect, with a catch:
        You need to make the typehint be optional:
    >>> class MyModel(Typed):
    ...     attribute: bool | None = False
    >>> MyModel({})
    <MyModel attribute=False >

    Finally, you may have multiple classes that inherit from a base, and you want to get whichever one matches.
        This, too, is rather simple:
    >>> class MyType(Enum):
    ...     TypeA = "a"
    ...     TypeB = "b"
    >>> class MyBase(Typed):
    ...     _discriminator = lambda self: self.my_differentiator is self._discriminator_match  # noqa: E731
    ...     my_differentiator: MyType
    >>> class MyTypeA(MyBase):
    ...     _discriminator_match = MyType.TypeA
    ...     type_a_only: str
    >>> class MyTypeB(MyBase):
    ...     _discriminator_match = MyType.TypeB
    ...     type_b_only: str
    >>> class MyFinalClass(Typed):
    ...     my_mixed_type: list[MyTypeA | MyTypeB]
    >>> MyFinalClass({"my_mixed_type": [{"my_differentiator": "b", "type_a_only": "not present!", "type_b_only": "present!"}, {"my_differentiator": "a", "type_a_only": "present!", "type_b_only": "not present!"}]})
    <MyFinalClass my_mixed_type=[<MyTypeB my_differentiator=MyType.TypeB, type_b_only=present! >, <MyTypeA my_differentiator=MyType.TypeA, type_a_only=present! >] >

    This also demonstrates useful features of Typed: Inheritance and enum handling. Any Typed class can be subclassed,
        and as you'd expect, the properties of the parent will be inherited by the subclass. Enums can be matched by
        either their identifier/name ("TypeA") or their assigned value ("a").
    Note that the use of _discriminator is optional in situations where you know for sure that the input object will
        only match a single type in a member's typehints. If a TypeA object was guaranteed to never include
        'type_b_only', and vice-versa for TypeB, the _discriminator would not be needed, because the typehint resolver
        would attempt to instantiate a TypeA object with the payload for a TypeB object, which would throw an exception,
        and it would then move on to TypeB, which would succeed. The typehint resolver iterates through every
        possibility before giving up. It recurses, too, so for more complex data structures, eg. a member defined as
        a dict[SomeEnum, dict[str, list[SomeObject[SomeOtherType]] | dict[str, SomeType]]],
        the typehint resolver would do exactly as you would expect: produce a dict whose keys are of type SomeEnum,
        and whose values are dicts whose keys are strings and whose values are either a list whose contents are all
        SomeObject which contains SomeOtherType, or if any items in the list couldn't be instantiated as a SomeObject
        with a SomeOtherType argument OR the list itself is not a list, a dict whose keys are strings and whose values
        are SomeType. What a mouthful.
    Note also that _discriminator is just a Callable that is expected to be called with one argument
        (self - the object being instantiated), and as such, can do essentially anything, as long as it returns a bool.
        For convenience, _discriminator_match is included, but can be ignored if unnecessary.
    You may also notice that your editor knows the type-hints for _aliases, _discriminator and _discriminator_match
        already, despite them not having typehints. These also act to demonstrate ways of having class members that are
        ignored by the Typed initialiser: declare the variable to have a default value of None, and use comment-based
        typehints, which aren't included in the typehint inspections built into Python.

    For more information on how an input object becomes a specific type, see bunnets.typehintlib.coerce_type.

    Possible future improvements to this library:
        * Handle 'Literal[]' typehints
        * Use ClassVar types as indicators to Typed's initialiser that it should ignore members?
    """

    _aliases = {}  # type: dict[str, str]
    _discriminator = None  # type: Callable[[Self], bool] | None
    _discriminator_match = None  # type: Any

    def __init__(self, source: dict | None = None, *args, **kwargs):
        # Allow kwargs in lieu of source if missing and kwargs isn't empty
        if source is None and len(kwargs) > 0:
            source = deepcopy(kwargs)
            kwargs = {}
        # members: dict = dict(getmembers(self))["__annotations__"]
        members = get_type_hints(self.__class__)
        for member, mtype in members.items():
            # Iterate through all typehints in the class
            is_optional = is_optional_typehint(mtype)
            source_key = resolve_member(member, self._aliases)
            try:
                value = resolve_value(source_key, source)
            except KeyError:
                if is_optional:
                    # fucking lmfao
                    setattr(self, member, getattr(self, member, None))
                    continue
                raise InvalidInputError(
                    f"Required attribute '{member}'{f" (aliased to '{source_key}')" if member != source_key else ''} missing from source {type(source)}({source})"
                )
            try:
                setattr(self, member, apply_typehints(value, mtype, is_optional=is_optional))
            except UnresolvableTypeError:
                raise InvalidInputError(
                    f"Required attribute '{member}'"
                    f"{f" (aliased to '{source_key}')" if member != source_key else ''} "
                    f"with value '{value}' from source {type(source)} "
                    f"could not be coerced to type definition {mtype}"
                )
        if (
            hasattr(self, "_discriminator")
            and callable(self._discriminator)
            and not self._discriminator()
        ):
            raise InvalidInputError("Discriminator did not match")
        super().__init__(*args, **kwargs)

    def as_dict(self, unmarshal: bool = False) -> dict:
        return {
            member
            if not unmarshal or member not in self._aliases
            else self._aliases[member]: serialise_co(getattr(self, member))
            if unmarshal
            else getattr(self, member)
            for member in get_type_hints(self.__class__)
        }

    def __eq__(self, other) -> bool:
        """
        Equality check - an object is determined to equal this one if:
        * it is an instance of the same class as this one
        * its class has the same typehints as this one
        * every typehinted class member has an equal value to the same member in this one
        """
        if not isinstance(other, type(self)):
            return False
        this_m = get_type_hints(self.__class__)
        that_m = get_type_hints(other.__class__)
        if this_m != that_m:
            return False
        for member in this_m.keys():
            if getattr(self, member) != getattr(other, member):
                return False
        return True

    def __repr__(self):
        return f"<{type(self).__name__} {', '.join([f'{i}={getattr(self, i)}' for i in self.as_dict(False)])} >"

    def __hash__(self) -> int:
        return hash(((member, getattr(self, member)) for member in get_type_hints(self.__class__)))


def is_optional_typehint(t: Any) -> bool:
    """Determines if the given typehint allows an optional value

    :param t: Typehint for a member of a class
    :return bool: indicating if the typehint dictates the member may be None
    """

    if not hasattr(t, "__args__"):
        return False
    if isinstance(t, UnionType) or (hasattr(t, "__origin__") and t.__origin__ is Union):
        return NoneType in t.__args__
    return False


def resolve_member(member_name: str, aliases: dict[str, str]) -> str:
    if member_name in aliases:
        return aliases[member_name]
    return member_name


def resolve_value(target: str, inp: SelectableDict | dict):
    if isinstance(inp, SelectableDict):
        return inp.select(target)
    # Kludgy as fuck but y'know..
    try:
        return inp[target]
    except Exception as e:
        try:
            return SelectableDict(inp).select(target)
        except:  # noqa: E722
            raise e


def serialise_co(target: Any):
    # recursion
    if isinstance(target, Typed):
        return serialise_co(target.as_dict())
    if isinstance(target, dict):
        return {k: serialise_co(v) for k, v in target.items()}
    if isinstance(target, list):
        return [serialise_co(i) for i in target]
    if isinstance(target, tuple):
        return (serialise_co(i) for i in target)
    # recursion over. now it is time to handle normal types.
    if isinstance(target, Enum):
        return target.name
    if isinstance(target, datetime):
        return target.timestamp()
