import os
from pathlib import Path
from unittest import mock

import pytest
from psutil import NoSuchProcess

from src.instance_checker.utils import CountHelper


@pytest.fixture
def helper():
    with mock.patch("src.instance_checker.utils.gettempdir", return_value="/tmp/locks"):
        yield CountHelper(lock_dir="/tmp/locks")


TEST_IDENTIFIER = "my_app"


@mock.patch("src.instance_checker.utils.process_iter")
def test_process_count_no_matches(mock_process_iter):
    mock_process_iter.return_value = []

    count = CountHelper.process_count(TEST_IDENTIFIER)
    assert count == 0


@mock.patch("src.instance_checker.utils.process_iter")
def test_process_count_one_match(mock_process_iter):
    mock_process_iter.return_value = [
        mock.MagicMock(
            cmdline=mock.MagicMock(return_value=["/usr/bin/python", "my_app.py"]),
        ),
        mock.MagicMock(
            cmdline=mock.MagicMock(return_value=["/bin/sh", "other_script.sh"]),
        ),
    ]

    count = CountHelper.process_count(TEST_IDENTIFIER)
    assert count == 1


@mock.patch("src.instance_checker.utils.process_iter")
def test_process_count_raised(mock_process_iter):
    mock_process_iter.return_value = [
        mock.MagicMock(cmdline=mock.MagicMock(side_effect=NoSuchProcess(123))),
    ]

    count = CountHelper.process_count(TEST_IDENTIFIER)
    assert count == 0


@mock.patch("src.instance_checker.utils.os.walk")
def test_pid_file_count_no_files(mock_walk, helper):
    mock_walk.return_value = [(".", [], [])]

    count = helper.pid_file_count(TEST_IDENTIFIER)
    assert count == 0


@mock.patch("src.instance_checker.utils.os.walk")
def test_pid_file_count_one_file(mock_walk, helper):
    mock_walk.return_value = [("/tmp/locks", [], ["my_app.lock.0"])]

    count = helper.pid_file_count(TEST_IDENTIFIER)
    assert count == 1


@mock.patch("src.instance_checker.utils.os.walk")
def test_get_pid_file(mock_walk, helper):
    mock_walk.return_value = [
        (
            "/tmp/locks",
            [],
            ["my_app.lock.0", "file.71fc8e82be524ebbba98df6564de5008.lock.12345"],
        ),
    ]

    file = helper.get_pid_file(identifier="file.")
    assert str(file.name) == "file.71fc8e82be524ebbba98df6564de5008.lock.12345"


@mock.patch("src.instance_checker.utils.os.walk")
def test_get_pid_file_none(mock_walk, helper):
    mock_walk.return_value = [
        (
            "/tmp/locks",
            [],
            ["my_app.lock.0", "my_app.lock.1"],
        ),
    ]

    file = helper.get_pid_file(identifier="file.")
    assert file is None


@mock.patch("src.instance_checker.utils.os.open", new_callable=mock.mock_open)
def test_acquire_pid_file(mock_open, helper):
    filename = f"file.71fc8e82be524ebbba98df6564de5008.lock.{os.getpid()}"
    expected_path = Path("/tmp/locks") / Path(filename)

    result = helper.acquire_pid_file(filename=filename)

    assert result[0] == expected_path
    mock_open.assert_called_once_with(expected_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)


@mock.patch("src.instance_checker.utils.os.open", side_effect=FileExistsError)
def test_acquire_pid_file_fails_on_exists(mock_open):  # noqa: ARG001
    helper = CountHelper(lock_dir="/tmp/locks")
    filename = f"file.71fc8e82be524ebbba98df6564de5008.lock.{os.getpid()}"

    with pytest.raises(FileExistsError):
        helper.acquire_pid_file(filename=filename)
