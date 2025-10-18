import importlib.util
import logging
import os
import sys
import types
from pathlib import Path

import pytest


class _DummyFlask:
    def __init__(self, *_, **__):
        self.config = {}

    def route(self, *_args, **_kwargs):
        def decorator(func):
            return func
        return decorator

    def run(self, *_args, **_kwargs):
        return None


def _jsonify(*_args, **_kwargs):
    return {}


class _DummyResponse:
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


_dummy_request = types.SimpleNamespace(get_json=lambda: {}, json={}, args={})

fake_flask = types.ModuleType('flask')
fake_flask.Flask = _DummyFlask
fake_flask.jsonify = _jsonify
fake_flask.request = _dummy_request
fake_flask.Response = _DummyResponse
sys.modules.setdefault('flask', fake_flask)


class _DummySock:
    def __init__(self, *_args, **_kwargs):
        pass

    def route(self, *_args, **_kwargs):
        def decorator(func):
            return func
        return decorator


fake_flask_sock = types.ModuleType('flask_sock')
fake_flask_sock.Sock = _DummySock
sys.modules.setdefault('flask_sock', fake_flask_sock)


fake_requests = types.ModuleType('requests')
fake_requests.get = lambda *args, **kwargs: types.SimpleNamespace(status_code=200, json=lambda: {}, text='', headers={})
fake_requests.post = fake_requests.get
fake_requests.exceptions = types.SimpleNamespace(
    RequestException=Exception,
    ConnectionError=Exception,
    Timeout=Exception,
)
sys.modules.setdefault('requests', fake_requests)


os.environ.setdefault('SUPERVISOR_TOKEN', 'test-supervisor-token')


BACKEND_PATH = Path(__file__).resolve().parents[1] / 'sense-360-zone-configurator' / 'backend.py'

spec = importlib.util.spec_from_file_location('backend', BACKEND_PATH)
backend = importlib.util.module_from_spec(spec)
assert spec and spec.loader  # satisfy type checkers
spec.loader.exec_module(backend)  # type: ignore[attr-defined]


def test_get_ha_websocket_url_supervisor():
    url = backend.get_ha_websocket_url('http://example.local/api', 'super-token')
    assert url == 'ws://supervisor/core/websocket'


@pytest.mark.parametrize(
    'api_url,expected',
    [
        ('http://example.local:8123/api', 'ws://example.local:8123/api/websocket'),
        ('https://ha.example/api/', 'wss://ha.example/api/websocket'),
    ],
)
def test_get_ha_websocket_url_direct(api_url, expected):
    url = backend.get_ha_websocket_url(api_url, None)
    assert url == expected


def test_build_auth_message_prefers_supervisor(caplog):
    caplog.set_level(logging.INFO)
    message = backend.build_auth_message('super-token', 'ha-token')
    assert message == {'type': 'auth', 'access_token': 'super-token'}
    assert 'Supervisor token' in caplog.text


def test_build_auth_message_falls_back_to_ha_token(caplog):
    caplog.set_level(logging.INFO)
    message = backend.build_auth_message(None, 'ha-token')
    assert message == {'type': 'auth', 'access_token': 'ha-token'}
    assert 'Home Assistant token' in caplog.text


def test_should_forward_state_change(caplog):
    caplog.set_level(logging.INFO)
    should_forward = backend.should_forward_state_change('sensor.presence', {'sensor.presence'})
    assert should_forward is True
    assert 'Forwarding state_changed event for sensor.presence' in caplog.text


def test_should_not_forward_unselected_state_change():
    should_forward = backend.should_forward_state_change('sensor.other', {'sensor.presence'})
    assert should_forward is False


def test_should_forward_mmwave_when_selection_empty(caplog):
    caplog.set_level(logging.INFO)
    entity_id = 'sensor.mmwave_zone_1_begin_x'
    should_forward = backend.should_forward_state_change(entity_id, set())
    assert should_forward is True
    assert 'Forwarding mmWave state_changed event' in caplog.text


def test_should_not_forward_non_mmwave_when_selection_empty():
    should_forward = backend.should_forward_state_change('sensor.other', set())
    assert should_forward is False
