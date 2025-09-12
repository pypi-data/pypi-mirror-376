import pytest
import sgn
from sgn.transforms import CallableTransform

from ..registry import ElementType, discover_elements


def test_registry():
    elements = discover_elements()
    assert "NullSink" in elements
    info = elements["NullSink"]
    assert not info.broken
    assert info.kind is ElementType.SINK


def test_invalid_element():
    with pytest.raises(TypeError):
        ElementType.from_element(object)


@pytest.mark.skipif(
    sgn.__version__ <= "0.2.0", reason="version greater than sgn 0.2 required"
)
def test_valid_element():
    kind = ElementType.from_element(CallableTransform.from_callable)
    assert kind is ElementType.TRANSFORM
