from unittest.mock import MagicMock
def create_request():
    r = MagicMock()
    r.json = lambda: {}
    return r
def create_response(): return MagicMock()