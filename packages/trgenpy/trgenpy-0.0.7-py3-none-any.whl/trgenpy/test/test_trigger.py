import pytest
from trgenpy.trigger import Trgen

def test_trgen_init_ok():
    trig = Trgen(1, 10)
    assert trig is not None

def test_trgen_init_missing_args():
    with pytest.raises(TypeError):
        Trgen()  # Mancano gli argomenti obbligatori

def test_trgen_init_invalid_id():
    with pytest.raises(ValueError):
        Trgen(-1, 10)  # id fuori range

def test_trgeninit_invalid_memory_length():
    with pytest.raises(ValueError):
        Trgen(1, 100)  # memory_length fuori range