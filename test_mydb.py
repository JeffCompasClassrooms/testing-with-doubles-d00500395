# test_mydb.py
import io
import builtins
import pickle
import pytest

from mydb import MyDB

def describe_myDB():
    def it_calls_saveStrings_when_file_missing(mocker):
        mock_isfile = mocker.patch("os.path.isfile", return_value=False)
        save_stub = mocker.patch.object(MyDB, "saveStrings", autospec=True)

        db = MyDB("fakefile.db")

        save_stub.assert_called_once_with(db, [])

    def it_does_not_call_saveStrings_when_file_exists(mocker):
        mocker.patch("os.path.isfile", return_value=True)
        save_stub = mocker.patch.object(MyDB, "saveStrings", autospec=True)

        db = MyDB("whatever.db")

        save_stub.assert_not_called()

def describe_load_and_save_strings():
    def it_loads_strings_using_pickle_load_and_returns_value(mocker):
        fake_file = io.BytesIO(b"not used")
        open_mock = mocker.patch("builtins.open", mocker.mock_open(read_data=b""), create=True)
        load_stub = mocker.patch("pickle.load", return_value=["a", "b"])

        db = object.__new__(MyDB)
        db.fname = "ignored"
        result = MyDB.loadStrings(db)
        assert result == ["a", "b"]
        load_stub.assert_called_once()

    def it_saves_strings_using_pickle_dump(mocker):
        m_open = mocker.patch("builtins.open", mocker.mock_open(), create=True)
        dump_stub = mocker.patch("pickle.dump", autospec=True)

        db = object.__new__(MyDB)
        db.fname = "ignored"
        arr = ["x", "y"]
        MyDB.saveStrings(db, arr)

        dump_stub.assert_called_once()
        called_args = dump_stub.call_args[0]
        assert called_args[0] == arr

def describe_saveString():
    def it_loads_then_appends_then_saves(mocker):
        load_stub = mocker.patch.object(MyDB, "loadStrings", return_value=["first"], autospec=True)
        save_stub = mocker.patch.object(MyDB, "saveStrings", autospec=True)

        db = object.__new__(MyDB)
        db.fname = "ignored"

        MyDB.saveString(db, "second")

        load_stub.assert_called_once_with(db)
        save_stub.assert_called_once_with(db, ["first", "second"])
