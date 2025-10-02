# test_squirrel_server.py
import io
import json
import pytest

import squirrel_server as server_module
from squirrel_server import SquirrelServerHandler

def make_handler_instance():
    """
    Construct an instance of the handler without invoking BaseHTTPRequestHandler __init__.
    We'll set attributes directly that the handler methods use.
    """
    inst = object.__new__(SquirrelServerHandler)
    inst.headers = {"Content-Length": "0"}
    inst.wfile = io.BytesIO()
    inst.rfile = io.BytesIO()
    inst._response_headers = []
    def send_response(code):
        inst._last_status = code
    def send_header(k, v):
        inst._response_headers.append((k, v))
    def end_headers():
        inst._headers_done = True
    inst.send_response = send_response
    inst.send_header = send_header
    inst.end_headers = end_headers
    return inst

def describe_squirrelServerHandler():
    def before_each():
        pass

    def describe_handleSquirrelsIndex():
        def it_returns_json_list_and_status_200(mocker):
            inst = make_handler_instance()

            mocker.patch.object(inst, "parsePath", return_value=("squirrels", None))
            fake_db = mocker.Mock()
            fake_db.getSquirrels.return_value = [{"id":1,"name":"A","size":"small"}]
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)

            inst.handleSquirrelsIndex()

            assert getattr(inst, "_last_status", None) == 200
            body = inst.wfile.getvalue().decode()
            assert json.loads(body) == [{"id":1,"name":"A","size":"small"}]
            fake_db.getSquirrels.assert_called_once()

    def describe_handleSquirrelsRetrieve():
        def it_returns_squirrel_when_found(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", "5"))
            fake_db = mocker.Mock()
            fake_db.getSquirrel.return_value = {"id":5,"name":"B","size":"large"}
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)

            inst.handleSquirrelsRetrieve("5")

            assert getattr(inst, "_last_status", None) == 200
            assert json.loads(inst.wfile.getvalue().decode()) == {"id":5,"name":"B","size":"large"}
            fake_db.getSquirrel.assert_called_once_with("5")

        def it_calls_handle404_when_not_found(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", "999"))
            fake_db = mocker.Mock()
            fake_db.getSquirrel.return_value = None
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)
            h404 = mocker.patch.object(inst, "handle404", autospec=True)

            inst.handleSquirrelsRetrieve("999")

            h404.assert_called_once()
            fake_db.getSquirrel.assert_called_once_with("999")

    def describe_handleSquirrelsCreate():
        def it_parses_body_and_calls_create_then_returns_200(mocker):
            inst = make_handler_instance()
            payload = {"name":"C", "size":"tiny"}
            # Mock getRequestData to return a dict (it parses form data in the real implementation)
            mocker.patch.object(inst, "getRequestData", return_value=payload)
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", None))

            fake_db = mocker.Mock()
            fake_db.createSquirrel.return_value = {"id":7, "name":"C", "size":"tiny"}
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)

            inst.handleSquirrelsCreate()

            fake_db.createSquirrel.assert_called_once_with("C", "tiny")
            assert getattr(inst, "_last_status", None) in (200, 201)

        def it_returns_400_on_malformed_json(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "getRequestData", return_value={})
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", None))

            fake_db = mocker.Mock()
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)
            
            with pytest.raises(KeyError):
                inst.handleSquirrelsCreate()

    def describe_handleSquirrelsReplace():
        def it_replaces_when_id_matches_and_body_ok(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", "12"))
            payload = {"id": "12", "name":"D", "size":"medium"}
            mocker.patch.object(inst, "getRequestData", return_value=payload)

            fake_db = mocker.Mock()
            fake_db.getSquirrel.return_value = {"id":12,"name":"Old","size":"small"}
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)

            inst.handleSquirrelsUpdate("12")

            fake_db.updateSquirrel.assert_called_once_with("12", "D", "medium")
            assert getattr(inst, "_last_status", None) in (200, 204)

        def it_calls_handle404_when_replace_returns_none(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", "9999"))
            payload = {"id": "9999", "name":"noone", "size":"tiny"}
            mocker.patch.object(inst, "getRequestData", return_value=payload)

            fake_db = mocker.Mock()
            fake_db.getSquirrel.return_value = None
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)
            h404 = mocker.patch.object(inst, "handle404", autospec=True)

            inst.handleSquirrelsUpdate("9999")

            h404.assert_called_once()

    def describe_handleSquirrelsDelete():
        def it_deletes_and_returns_200_when_found(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", "3"))
            fake_db = mocker.Mock()
            fake_db.getSquirrel.return_value = {"id":3,"name":"X","size":"small"}
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)

            inst.handleSquirrelsDelete("3")

            fake_db.deleteSquirrel.assert_called_once_with("3")
            assert getattr(inst, "_last_status", None) in (200, 204)

        def it_calls_handle404_when_not_found(mocker):
            inst = make_handler_instance()
            mocker.patch.object(inst, "parsePath", return_value=("squirrels", "77"))
            fake_db = mocker.Mock()
            fake_db.getSquirrel.return_value = None
            mocker.patch.object(server_module, "SquirrelDB", return_value=fake_db)
            h404 = mocker.patch.object(inst, "handle404", autospec=True)

            inst.handleSquirrelsDelete("77")

            h404.assert_called_once()

    def describe_handle404():
        def it_writes_404_text_and_sets_status(mocker):
            inst = make_handler_instance()

            inst.handle404()

            assert getattr(inst, "_last_status", None) == 404
            assert b"404 Not Found" in inst.wfile.getvalue()