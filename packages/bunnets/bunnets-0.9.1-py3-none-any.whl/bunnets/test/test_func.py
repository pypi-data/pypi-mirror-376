from bunnets.func import hasattrs


def test_hasattrs_args():
    test_object = object()
    assert hasattrs(test_object, "__str__", "__format__", "__repr__")
    assert not hasattrs(test_object, "__str__", "missing attribute")


def test_hasattrs_allof():
    test_object = object()
    assert hasattrs(
        test_object,
        all_of=(
            "__repr__",
            "__eq__",
        ),
    )
    assert not hasattrs(
        test_object,
        all_of=(
            "__str__",
            "missing attribute",
        ),
    )


def test_hasattrs_anyof():
    test_object = object()
    assert hasattrs(
        test_object,
        any_of=(
            "__hash__",
            "missing attribute",
            "__sizeof__",
        ),
    )
    assert not hasattrs(
        test_object,
        any_of=(
            "what if a swedish guy was italian",
            "missing attribute",
        ),
    )


def test_hasattrs_alltogether():
    test_object = object()
    assert hasattrs(
        test_object,
        all_of=(
            "__str__",
            "__repr__",
        ),
        any_of=("missing attribute", "__module__", "cum", "__reduce__"),
    )
    assert not hasattrs(
        test_object,
        "__eq__",
        "__format__",
        all_of=(
            "__str__",
            "missing attribute",
        ),
        any_of=("third funny joke",),
    )
