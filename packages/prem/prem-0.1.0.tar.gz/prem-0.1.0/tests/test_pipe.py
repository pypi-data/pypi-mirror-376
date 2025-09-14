from prem import cat, grep, ls, sed, xargs

TEST_STR = "hello\nWorld\ngoodbye world\n"


def test_lt():
    res = grep("[Ww]or") < TEST_STR
    assert str(res) == "World\ngoodbye world\n"


def test_lshift():
    res = grep("[Ww]or") << TEST_STR
    assert str(res) == "World\ngoodbye world\n"


def test_or():
    res = grep("[Ww]or") << TEST_STR | grep("good")
    assert str(res) == "goodbye world\n"


def test_generators():
    # out
    res = grep("[Ww]or") < TEST_STR
    assert tuple(res) == ("World", "goodbye world")

    # in
    res = grep("[Ww]or") < TEST_STR.splitlines()
    assert str(res) == "World\ngoodbye world\n"

    # both
    res = grep("[Ww]or") < TEST_STR.splitlines()
    assert tuple(res) == ("World", "goodbye world")


def test_grep():
    res = grep("wor", invert_match=True) < TEST_STR
    assert tuple(res) == ("hello", "World")
    res = grep("wor", invert_match=True) < TEST_STR.splitlines()
    assert tuple(res) == ("hello", "World")
    res = grep("wor", ignore_case=True) < TEST_STR
    assert tuple(res) == ("World", "goodbye world")


def test_cat():
    assert len(tuple(cat(__file__) | grep(r"def test_cat\(\)"))) == 1
    assert len(tuple(cat(__file__) | grep("def test_cat"))) == 3
    with open(__file__) as fd:
        assert str(cat(__file__)) == fd.read()


def test_ls():
    assert tuple(ls())
    assert tuple(ls("?*.*"))
    assert tuple(ls("/*"))


def test_xargs():
    assert tuple(ls("?*.*") | grep(r"\.(egg.*|xml)$", invert_match=True) | xargs(cat))


def test_sed():
    src = cat(__file__) | grep("hello")
    assert str(sed("s/h/H/g") < src) == str(sed("s/h/H/g") < str(src))
    assert str(src | sed("s/h/H/g")).count("Hello") > str(src).count("Hello")
    assert tuple(src | sed("/world/d")) == tuple(src | grep("world", invert_match=True))
    assert 0 < len(tuple(src | sed("/world/d"))) < len(tuple(src))
