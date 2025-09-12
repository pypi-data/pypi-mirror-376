class ImmutableValueError(RuntimeError):
    """Raised when something tries to modify an immutable value"""


class NonLockingError(RuntimeError):
    """Raised when something tries to lock or unlock a non-lockable object"""


class ImmutableObjectError(ImmutableValueError):
    """Raised when something tries to unlock an object that can only be locked"""


class _UndefinedObj:
    """Undefined for a reason"""


class InvalidInputError(ValueError):
    """Raised when an input value is, in some way, erroneous :)"""


class OperationalTypeError(ValueError):
    """Raised when a type coercion occurs during an operation, and the coercion fails."""


class UnresolvableTypeError(Exception):
    """Raised when Typed or coerce_type cannot coerce a required value to be of the requested type"""
