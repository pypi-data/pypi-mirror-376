"""CLI to Download MicroPython firmware for specific ports, boards and versions."""

from pathlib import Path

import rich_click as click
from loguru import logger as log

from mpflash.connected import connected_ports_boards_variants
from mpflash.downloaded import clean_downloaded_firmwares
from mpflash.errors import MPFlashError
from mpflash.mpboard_id import find_known_board
from mpflash.mpboard_id.alternate import add_renamed_boards
from mpflash.versions import clean_version

from .ask_input import ask_missing_params
from .cli_group import cli
from .common import DownloadParams
from .config import config
from .download import download


@cli.command(
    "download",
    help="Download MicroPython firmware for specific ports, boards and versions.",
)
@click.option(
    "--version",
    "-v",
    "versions",
    default=["stable"],
    multiple=True,
    show_default=True,
    help="The version of MicroPython to to download.",
    metavar="SEMVER, 'stable', 'preview' or '?'",
)
@click.option(
    "--board",
    "-b",
    "boards",
    multiple=True,
    default=[],
    show_default=True,
    help="The board(s) to download the firmware for.",
    metavar="BOARD_ID or ?",
)
@click.option(
    "--serial",
    "--serial-port",
    "-s",
    "serial",
    default=["*"],
    show_default=True,
    multiple=True,
    help="Which serial port(s) (or globs) to flash",
    metavar="SERIALPORT",
)
@click.option(
    "--ignore",
    "-i",
    is_eager=True,
    help="Serial port(s) to ignore. Defaults to MPFLASH_IGNORE.",
    multiple=True,
    default=[],
    envvar="MPFLASH_IGNORE",
    show_default=True,
    metavar="SERIALPORT",
)
@click.option(
    "--clean/--no-clean",
    default=True,
    show_default=True,
    help="""Remove dates and hashes from the downloaded firmware filenames.""",
)
@click.option(
    "--force",
    "-f",
    default=False,
    is_flag=True,
    show_default=True,
    help="""Force download of firmware even if it already exists.""",
)
def cli_download(**kwargs) -> int:
    params = DownloadParams(**kwargs)
    params.versions = list(params.versions)
    params.boards = list(params.boards)
    params.serial = list(params.serial)
    params.ignore = list(params.ignore)
    if params.boards:
        if not params.ports:
            # no ports specified - resolve ports from specified boards by resolving board IDs
            for board in params.boards:
                if board != "?":
                    try:
                        board_ = find_known_board(board)
                        params.ports.append(board_.port)
                    except MPFlashError as e:
                        log.error(f"{e}")
    else:
        # no boards specified - detect connected ports and boards
        params.ports, params.boards, _, _ = connected_ports_boards_variants(include=params.serial, ignore=params.ignore)

    params = ask_missing_params(params)
    if not params:  # Cancelled by user
        return 2
    params.versions = [clean_version(v, drop_v=True) for v in params.versions]
    assert isinstance(params, DownloadParams)

    try:
        download(
            params.ports,
            add_renamed_boards(params.boards),
            params.versions,
            params.force,
            params.clean,
        )
        clean_downloaded_firmwares()
        return 0
    except MPFlashError as e:
        log.error(f"{e}")
        return 1
