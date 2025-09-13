"""mpflash is a CLI to download and flash MicroPython firmware to various boards."""

import os

import click.exceptions as click_exceptions
from loguru import logger as log

from mpflash.errors import MPFlashError

from .cli_add import cli_add_custom
from .cli_download import cli_download
from .cli_flash import cli_flash_board
from .cli_group import cli
from .cli_list import cli_list_mcus
from .db.core import migrate_database


def mpflash():
    """Main entry point for the mpflash CLI."""
    migrate_database(boards=True, firmwares=True)

    cli.add_command(cli_list_mcus)
    cli.add_command(cli_download)
    cli.add_command(cli_flash_board)
    cli.add_command(cli_add_custom)

    # cli(auto_envvar_prefix="MPFLASH")
    if False and os.environ.get("COMPUTERNAME").upper().startswith("JOSVERL"):
        # intentional less error suppression on dev machine
        result = cli(standalone_mode=False)
    else:
        try:
            result = cli(standalone_mode=True)
            exit(result)
        except AttributeError as e:
            log.error(f"Error: {e}")
            exit(-1)
        except click_exceptions.ClickException as e:
            log.error(f"Error: {e}")
            exit(-2)
        except click_exceptions.Abort:
            # Aborted - Ctrl-C
            exit(-3)
        except MPFlashError as e:
            log.error(f"MPFlashError: {e}")
            exit(-4)


if __name__ == "__main__":
    mpflash()
