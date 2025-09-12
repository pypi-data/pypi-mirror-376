from pytest import raises
from bunnets import Properties, SelectableDict, Typed


def test_properties_empty():
    ao = Properties()

    assert len(ao) == 0
    assert vars(ao) == {}


def test_properties_withdict():
    att = {
        "prop1": "val1",
    }
    ao = Properties(of=att)

    assert len(ao) == 1
    assert "prop1" in ao
    assert ao.prop1 == "val1"
    assert vars(ao) == att


def test_properties_wr_dict():
    att = [
        {
            "prop1": "val1",
        },
        {
            "prop2": "val2",
        },
    ]
    ao = Properties(of=att[0])

    assert len(ao) == 1
    assert "prop1" in ao

    [setattr(ao, k, v) for k, v in att[1].items()]

    ao.prop3 = "val3"

    assert len(ao) == 3
    assert "prop2" in ao
    assert ao.prop2 == "val2"
    assert ao.prop3 == "val3"
    assert vars(ao) == {**att[0], **att[1], "prop3": "val3"}


def test_properties_subdict():
    att = {
        "d1": {
            "prop1": "val1",
        },
        "d2": {
            "prop2": "val2",
        },
    }
    ao = Properties(of=att)

    assert len(ao) == 2
    assert isinstance(ao.d1, Properties)
    assert isinstance(ao.d2, Properties)
    assert vars(ao.d1) == att["d1"]
    assert vars(ao.d2) == att["d2"]
    assert vars(ao) == att


def test_properties_dict_w_list():
    att = {
        "d1": {
            "prop1": "val1",
            "prop2": "val2",
        },
        "d2": [
            {
                "sd1": {
                    "prop1": "val1",
                },
                "sd2": {
                    "prop2": "val2",
                },
            },
            {
                "sd1": {
                    "prop2": "val3",
                },
                "sd3": {
                    "prop1": "val4",
                },
            },
        ],
    }
    ao = Properties(of=att)

    assert len(ao) == 2
    assert isinstance(ao.d1, Properties)
    assert isinstance(ao.d2, list)
    assert False not in [isinstance(v, Properties) for v in ao.d2]
    assert vars(ao) == att


def test_properties_case_insensitive():
    att = {"D1": {"Prop1": "val1"}, "dD2": 3}
    ao = Properties(of=att, case_sensitive=False)

    assert len(ao) == 2
    assert "d1" in ao
    assert "DD2" in ao
    assert "prOP1" in ao.d1
    assert ao.Dd2 == 3


def test_properties_subclass():
    class inner_class(Properties):
        _special_keys = ("_category",)
        _category: str

        def __init__(self, category: str):
            super().__init__()
            print(self._special)
            self._category = category

    ao = inner_class("funny")

    assert ao._category == "funny"
    assert len(ao) == 0
    with raises(AttributeError):
        del ao._category


def test_typed_model():
    class TestModel(Typed):
        one: str
        two: int
        three: list[int]

    inst = TestModel(
        source={
            "one": 1,
            "two": "2",
            "three": (
                "1",
                "2",
            ),
        }
    )

    # inst.one, input type int, should be a str
    assert inst.one == "1"
    # inst.two, input type str, should be an int
    assert inst.two == 2
    # inst.three, input type tuple[str], should be a list[int]
    assert inst.three == [1, 2]


def test_typed_model_complex():
    # TODO: make more complex
    class TestModel(Typed):
        one: int
        two: str | None
        three: int | None

    inst = TestModel(
        source={
            "one": "1",
            "three": "3",
        }
    )

    assert inst.one == 1
    assert inst.two is None
    assert inst.three == 3


def test_typed_model_multi():
    class TestModel(Typed):
        one: int | str
        two: list[int | str]
        three: dict[str, list[int | str]]
        four: dict[str, int] | list[int] | bool
        five: dict[str, int] | list[int] | bool
        six: dict[str, int] | list[int] | bool
        seven: dict[str, int | str | None] | list[bool] | None
        eight: dict[str, int | str | None] | list[bool] | None
        nine: dict[str, int | str | None] | list[bool] | None
        ten: dict[str, int | str | None] | list[bool]
        eleven: dict | list
        twelve: int

    inst = TestModel(
        source={
            "one": "steve coercion",
            "two": ["one", "3"],
            "three": {
                "one": ["david iterable", "9"],
                "two": ["4", "john datastructure"],
            },
            "four": {"a": "1", "b": "2"},
            "five": ["9", "8"],
            "six": "yeah",
            "eight": {1: "2", "a": 3, 3: None},
            "nine": ["yeah", "nah"],
            "ten": ["yeah"],
            "eleven": [],
            "twelve": "12",
        }
    )

    assert inst.one == "steve coercion"
    assert inst.two == ["one", 3]
    assert inst.three == {
        "one": ["david iterable", 9],
        "two": [4, "john datastructure"],
    }
    assert inst.four == {"a": 1, "b": 2}
    assert inst.five == [9, 8]
    assert isinstance(inst.six, bool)
    assert inst.six is True
    assert inst.seven is None
    assert inst.eight == {"1": 2, "a": 3, "3": None}
    assert inst.nine == [True, False]
    assert inst.ten == [True]
    assert inst.eleven == {}
    assert inst.twelve == 12


def test_typed_model_bare():
    class TestModel(Typed):
        one: int
        two: bool
        three: list[int]

    inst = TestModel({"one": "1", "two": "yeah", "three": ["1", "2"]})
    assert inst.one == 1
    assert isinstance(inst.two, bool)
    assert inst.two
    assert inst.three == [1, 2]


def test_typed_model_aliases():
    class TestModel(Typed):
        _aliases = {
            "uno": "one",
            "dos": "two",
            "tres": "three",
        }

        uno: int
        dos: str | None
        tres: list[str]

    inst = TestModel({"one": "1", "two": None, "three": [1, 2, False]})
    assert inst.uno == 1
    assert inst.dos is None
    assert inst.tres == ["1", "2", "False"]


def test_typed_model_cmp():
    class inner_class_a(Typed):
        a: int
        b: bool

    class inner_class_a_clone(inner_class_a):
        pass

    class inner_class_b(Typed):
        one: list[inner_class_a]
        two: dict[str, inner_class_a]

    class inner_class_c(Typed):
        inner: inner_class_b
        other: inner_class_a

    inst = inner_class_c(
        {
            "inner": {
                "one": [
                    {"a": "1", "b": "yeah"},
                    {"a": "2", "b": "no"},
                    {"a": "3", "b": "sure"},
                ],
                "two": {
                    "uno": {"a": "4", "b": "nyet"},
                    "dos": {"a": "5", "b": "ja"},
                },
            },
            "other": {
                "a": "6",
                "b": "nein",
            },
        }
    )
    cmp = inner_class_a({"a": "1", "b": "true"})
    assert inst.inner.one[0] == cmp
    assert inst.inner.one[1] != cmp
    assert inst.inner.one[2] != cmp
    cmp.a = 4
    assert inst.inner.two["uno"] != cmp
    cmp.b = False
    assert inst.inner.two["uno"] == cmp
    assert cmp != inner_class_a_clone({"a": "1", "b": "true"})


def test_typed_model_nested():
    class inner_class_a(Typed):
        a: int
        b: bool

    class inner_class_b(Typed):
        one: list[inner_class_a]
        two: dict[str, inner_class_a]

    class inner_class_c(Typed):
        inner: inner_class_b
        other: inner_class_a

    inst = inner_class_c(
        {
            "inner": {
                "one": [
                    {"a": "1", "b": "yeah"},
                    {"a": "2", "b": "no"},
                    {"a": "3", "b": "sure"},
                ],
                "two": {
                    "uno": {"a": "4", "b": "nyet"},
                    "dos": {"a": "5", "b": "ja"},
                },
            },
            "other": {
                "a": "6",
                "b": "nein",
            },
        }
    )
    assert isinstance(inst.inner, inner_class_b)
    assert isinstance(inst.other, inner_class_a)
    assert len(inst.inner.one) == 3
    assert len(inst.inner.two) == 2
    assert list(inst.inner.two.keys()) == ["uno", "dos"]
    assert False not in [isinstance(inner, inner_class_a) for inner in inst.inner.one]
    assert False not in [isinstance(inner, inner_class_a) for inner in inst.inner.two.values()]
    assert inst.inner.one[0] == inner_class_a({"a": 1, "b": True})


def test_typed_model_discriminator():
    class inner_base(Typed):
        _discriminator = lambda self: self.a in self._discriminator_match  # noqa: E731
        a: int
        b: bool

    class inner_a(inner_base):
        _discriminator_match = (1, 3, 9)

    class inner_b(inner_base):
        _discriminator_match = (4, 69)

    class inner_c(inner_base):
        _discriminator_match = (22, 651, 90, 99)

    class TestClass(Typed):
        testlist: list[inner_a | inner_b | inner_c]
        testobj: inner_b
        testlist_nullable: list[inner_a | inner_c] | None
        testdict: dict[str, list[inner_b | inner_a | None]]

    inst = TestClass(
        {
            "testlist": [
                {"a": 1, "b": "yes"},
                {"a": 4, "b": "yes"},
                {"a": 22, "b": "yes"},
            ],
            "testobj": {"a": 69, "b": "no"},
            "testlist_nullable": [
                {"a": 5, "b": "yes"},
            ],
            "testdict": {
                "a": [
                    {
                        "a": a,
                        "b": a % 2 == 0,
                    }
                    for a in range(1, 6)
                ]
            },
        }
    )

    assert isinstance(inst.testlist[0], inner_a)
    assert isinstance(inst.testlist[1], inner_b)
    assert isinstance(inst.testlist[2], inner_c)

    assert isinstance(inst.testobj, inner_b)

    assert inst.testlist_nullable is None
    assert inst.testdict["a"] == [
        inner_a({"a": 1, "b": False}),
        None,
        inner_a({"a": 3, "b": False}),
        inner_b({"a": 4, "b": True}),
        None,
    ]


def test_selectabledict_basic():
    sd = SelectableDict({"a": "b"})

    assert sd["a"] == "b"
    assert sd.select("a") == "b"


def test_selectabledict_nested():
    sd = SelectableDict(
        {
            "a": {
                "b": [
                    {"c0": "c0v0"},
                    {"c1": "c1v0"},
                ],
                "d": {
                    "e": "v",
                    "f": {
                        1: {"g": "v2"},
                        2: {"h": "v3"},
                    },
                },
            }
        }
    )

    assert sd["a"]["b"][1]["c1"] == "c1v0"
    assert sd.select("a.b.1.c1") == "c1v0"
    assert sd.select("a.d.e") == "v"
    assert sd.select("a.d.f.1.g") == "v2"
