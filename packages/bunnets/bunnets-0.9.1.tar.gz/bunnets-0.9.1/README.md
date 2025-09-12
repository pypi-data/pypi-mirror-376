# bunnets

_Tidy wee caps to keep your code neat_

To install: `pip install bunnets` or `uv add bunnets`

Development versions currently published to Codeberg at https://codeberg.org/api/packages/maff/pypi/simple

Components are categorised into individual bunnets, documented below.

## Data bunnet

Provides types, decorators and functions for more easily working with datatypes.


### Types

#### bunnets.typedefs

##### Lockable

Interface class for providing a way of making an object immutable or mutable.

##### Properties

Class for making a dictionary accessible as if it were an object.

Can be deserialised back to the underlying dict by calling `vars(...)`

More documentation to come.

##### SelectableDict

Basic wrapper around a dict that provides an XPath-like selection interface. Tries its hardest to
otherwise be a regular ol' dict.

##### Typed

The real meat and potatoes of this library. Akin to a dataclass that started HRT.
Intended for use in serialising or deserialising data in scenarios such as request and response
objects, but can be used for essentially anything.

Complex data structures can be specified without writing any scaffolding code - it works off of
just typehints. Input object doesn't quite match your desired structure? Map them with the
`_aliases` dict. Supports (automatically!) XPath-style selectors as well as simple keys.
Supports subclassing, type unions, nested types, optional types, variants and more.

If a typehint cannot be satisfied at any point in the chain of typehint resolution, raises a
`bunnets.error.UnresolvableTypeError` detailing the exact point of failure.

More documentation to come later

### Function decorators / wrappers

#### bunnets.func

##### coerce_params

Applies the same type casting functionality used by `bunnets.typedefs.Typed` to a
given positional or keyword argument on the wrapped function.

More documentation to come.

##### typed

Implicit version of `bunnets.func.coerce_params` - applies typehints to all arguments to a function,
and to its output.

More documentation to come.

### Functions

#### bunnets.func

##### lock

Locks a `bunnets.typedefs.Lockable` object. If the object is not `Lockable`, raises a
`bunnets.error.NonLockingError`. Any other behaviour is left to the implementation. Does not return
anything.

##### locked

Returns a boolean indicating if the given `bunnets.typedefs.Lockable` object is currently locked /
immutable. If the given object is not `Lockable`, raises a `bunnets.error.NonLockingError`.

##### mutable

The opposite of `bunnets.func.locked` - returns True if the given `bunnets.typedefs.Lockable` is
unlocked / mutable, and raises the same exceptions in the same situations.

##### unlock

Unlocks a `bunnets.typedefs.Lockable` object. If the object is not a `Lockable`, raises a
`bunnets.error.NonLockingError`. If the object is locked, and has a `__lock__` method, but does
not have an `__unlock__` method, raises an `bunnets.error.ImmutableObjectError`. Like `lock`,
any other behaviour is left to the implementation. Does not return anything.

#### bunnets.typehintlib

##### coerce_type

The foundational part of all other type enforcement components in this library. Takes an input
object, a type or an instance of a type, and whether the coercion is mandatory, and attempts to
cast the input object to the desired type. If it is already the desired type, returns it unaltered.
If it is unable to be cast to the desired type and coercion is not mandatory, returns it unaltered.
If it is unable to be cast and coercion is mandatory, raises a `bunnets.error.InvalidInputError`.
If it is None and the desired type is an instance rather than a bare type, returns the instance.
Intended for use in cases such as normalising environment variables to a structure of various
types, but can be used for many things.
