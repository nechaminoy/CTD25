# tests/conftest.py
import sys
import types
import pytest

@pytest.fixture(autouse=True)
def fake_pygame(monkeypatch):
    """
    Before any import of engine.sound_handler, inject a fake pygame module
    so that mixer.init() and Sound(...) are no‑ops and fast.
    """
    # create a fake pygame.mixer namespace
    fake_mixer = types.SimpleNamespace(
        init=lambda *a, **k: None,
        Sound=lambda filename: types.SimpleNamespace(
            play=lambda *a, **k: None
        )
    )
    # create a fake pygame module
    fake_pygame = types.SimpleNamespace(mixer=fake_mixer)
    # inject into sys.modules
    monkeypatch.setitem(sys.modules, 'pygame', fake_pygame)
    # also handle direct import of pygame.mixer
    monkeypatch.setitem(sys.modules, 'pygame.mixer', fake_mixer)
