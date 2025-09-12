import inspect
from functools import wraps

from .error import (
    NonLockingError,
    ImmutableObjectError,
    InvalidInputError,
    UnresolvableTypeError,
    OperationalTypeError,
)
from .typehintlib import apply_typehint, coerce_type


def hasattrs(obj, *attrs: str, **kwargs):
    """ """

    if len(attrs) > 0 and False in [hasattr(obj, attr) for attr in attrs]:
        return False
    if (
        "all" in kwargs
        and isinstance(kwargs["all"], (tuple, list, set))
        and False in [hasattr(obj, attr) for attr in kwargs["all"]]
    ):
        return False
    if (
        "any" in kwargs
        and isinstance(kwargs["any"], (tuple, list, set))
        and True not in [hasattr(obj, attr) for attr in kwargs["any"]]
    ):
        return False
    return True


def lock(obj):
    """Locks a Lockable-compatible object by invoking its `__lock__` method

    :param obj: a Lockable object, or compatible
    :raises NonLockingError: if the given object isn't Lockable-compatible
    """
    if not hasattr(obj, "__lock__") or not callable(getattr(obj, "__lock__")):
        raise NonLockingError(obj)
    obj.__lock__()


def unlock(obj):
    """Unlocks a Lockable-compatible object by invoking its `__unlock__` method

    :param obj: a Lockable object, or compatible
    :raises NonLockingError: if the given object isn't Lockable-compatible
    :raises ImmutableObjectError: if the given object cannot be unlocked
    """
    if not hasattr(obj, "__unlock__") or not callable(getattr(obj, "__unlock__")):
        if not hasattr(obj, "__lock__") or not callable(getattr(obj, "__lock__")):
            raise NonLockingError(obj)
        raise ImmutableObjectError(obj)
    obj.__unlock__()


def locked(obj) -> bool:
    """Returns whether a Lockable-compatible object is currently immutable (locked)

    :param obj: a Lockable object, or compatible
    :return: True if the object is immutable, False if not
    :raises NonLockingError: if the given object is not Lockable-compatible
    """

    if not hasattr(obj, "__locked__") or not callable(getattr(obj, "__locked__")):
        raise NonLockingError(obj)
    return obj.__locked__()


def mutable(obj) -> bool:
    """Returns whether a Lockable-compatible object is currently mutable (unlocked).
    This function is the inverse of `locked(obj)`.

    :param obj: a Lockable object, or compatible
    :return: True if the object is mutable, False if not
    :raises NonLockingError: if the given object is not Lockable-compatible
    """

    return not locked(obj)


def coerce_params(*pairs: tuple[int | str, type]):
    """Attempts to enforce type coercion for arguments to the wrapped function.
    Possible enhancement: autodetection of types based on typehints of wrapped function

    :arg pairs: a pairing of argument number and type
    :type pairs: list[tuple[int | str, type]]
    """

    def wrapper(func):
        @wraps(func)
        def call(*args, **kwargs):
            for arg, c_to in pairs:
                if isinstance(arg, int):
                    if arg > len(args):
                        raise OperationalTypeError("arg!")
                    args = list(args)
                    args[arg] = coerce_type(args[arg], c_to)
                    args = tuple(args)
                if isinstance(arg, str):
                    if kwargs.get(arg, None) is None:
                        raise OperationalTypeError("kwarg!")
                    kwargs[arg] = coerce_type(kwargs.get(arg, None), c_to)
            return func(*args, **kwargs)

        return call

    return wrapper


def typed(func):
    """Implicit version of @coerce_params, uses typehints to check parameters and return values"""

    @wraps(func)
    def call(*args, **kwargs):
        argspec = inspect.getfullargspec(func)
        # If wrapped function doesn't actually have any typehints, just call and return immediately
        if not argspec.annotations or len(argspec.annotations) == 0:
            return func(*args, **kwargs)
        # annotations contains all typehints, including the return value
        rtn_hint = None
        if "return" in argspec.annotations:
            rtn_hint = argspec.annotations["return"]
        in_args = []
        for pos in range(len(args)):
            in_args.append(args[pos])
            if argspec.args[pos] in argspec.annotations:
                try:
                    in_args[pos] = apply_typehint(args[pos], argspec.annotations[argspec.args[pos]])
                except InvalidInputError:
                    continue
                except UnresolvableTypeError as e:
                    raise OperationalTypeError(
                        f"argument at position {pos} (named '{argspec.args[pos]}') requires a value of type(s) {argspec.annotations[argspec.args[pos]]}, but this was impossible to fulfill",
                        e,
                    )
        for k in kwargs:
            if k in argspec.annotations:
                try:
                    kwargs[k] = apply_typehint(kwargs[k], argspec.annotations[k])
                except InvalidInputError:
                    continue
                except UnresolvableTypeError as e:
                    raise OperationalTypeError(
                        f"keyword argument '{k}' requires a value of type(s) {argspec.annotations[k]}, but this was impossible to fulfill",
                        e,
                    )
        rtn = func(*in_args, **kwargs)
        if "return" in argspec.annotations and rtn is not None and not isinstance(rtn, rtn_hint):
            try:
                rtn = apply_typehint(rtn, rtn_hint)
            except InvalidInputError:
                return rtn
            except UnresolvableTypeError as e:
                raise OperationalTypeError(
                    "coerced call returned a value that couldn't be coerced to the return type", e
                )
        return rtn

    return call
