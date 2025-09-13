from typing import List

import pytest
from click.testing import CliRunner
from mock import Mock
from pytest_mock import MockerFixture

# # module under test :
from mpflash import cli_main
from mpflash.common import DownloadParams
from mpflash.mpremoteboard import MPRemoteBoard

# mark all tests
pytestmark = pytest.mark.mpflash


##########################################################################################
# download


@pytest.mark.parametrize(
    "id, ex_code, args",
    [
        ("10", 0, ["download"]),
        ("30", 0, ["download", "--version", "1.22.0"]),
        ("31", 0, ["download", "--version", "stable"]),
        ("32", 0, ["download", "--version", "stable", "--version", "1.22.0"]),
        ("40", 0, ["download", "--board", "ESP32_GENERIC"]),
        ("41", 0, ["download", "--board", "?"]),
        ("42", 0, ["download", "--board", "?", "--board", "ESP32_GENERIC"]),
        ("43", 0, ["download", "--board", "ESP32_GENERIC", "--board", "?"]),
        ("60", 0, ["download", "--no-clean"]),
        ("61", 0, ["download", "--clean"]),
        ("62", 0, ["download", "--force"]),
    ],
)
def test_mpflash_download(id, ex_code, args: List[str], mocker: MockerFixture, session_fx):
    def fake_ask_missing_params(params: DownloadParams) -> DownloadParams:
        if "?" in params.ports:
            params.ports = ["esp32"]
        if "?" in params.boards:
            params.ports = ["esp32"]
            params.boards = ["ESP32_GENERIC"]
        if "?" in params.versions:
            params.versions = ["1.22.0"]
        return params

    m_connected_ports_boards = mocker.patch(
        "mpflash.cli_download.connected_ports_boards_variants",
        return_value=(["esp32"], ["ESP32_GENERIC"], [], [MPRemoteBoard("COM99")]),
        autospec=True,
    )
    m_download = mocker.patch("mpflash.cli_download.download", return_value=None, autospec=True)
    m_ask_missing_params = mocker.patch(
        "mpflash.cli_download.ask_missing_params",
        Mock(side_effect=fake_ask_missing_params),
    )
    mocker.patch("mpflash.download.Session", session_fx)
    mocker.patch("mpflash.mpboard_id.known.Session", session_fx)
    runner = CliRunner()
    result = runner.invoke(cli_main.cli, args, standalone_mode=True)
    assert result.exit_code == ex_code
    if "--board" not in args:
        m_connected_ports_boards.assert_called_once()
    m_ask_missing_params.assert_called_once()
    m_download.assert_called_once()

    assert m_download.call_args.args[1], "one or more ports should be specified for download"

    if "--clean" in args:
        assert m_download.call_args.args[4] == True, "clean should be True"
    if "--no-clean" in args:
        assert m_download.call_args.args[4] == False, "clean should be False"
    else:
        assert m_download.call_args.args[4] == True, "clean should be True"

    if "--force" in args:
        assert m_download.call_args.args[3] == True, "force should be True"
    else:
        assert m_download.call_args.args[3] == False, "force should be False"
