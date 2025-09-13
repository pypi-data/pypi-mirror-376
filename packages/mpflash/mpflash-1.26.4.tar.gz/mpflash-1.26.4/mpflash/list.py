from typing import List

from rich.progress import track
from rich.table import Table

from mpflash.config import config
from mpflash.mpremoteboard import MPRemoteBoard
from mpflash.versions import clean_version

from .logger import console


def show_mcus(
    conn_mcus: List[MPRemoteBoard],
    title: str = "Connected boards",
    refresh: bool = True,
    *,
    title_style="magenta",
    header_style="bold magenta",
):
    console.print(mcu_table(conn_mcus, title, refresh, title_style=title_style, header_style=header_style))


def abbrv_family(family: str, is_wide: bool) -> str:
    if not is_wide:
        ABRV = {"micropython": "mpy", "circuitpython": "cpy", "unknown": "?"}
        return ABRV.get(family, family[:4])
    return family


def mcu_table(
    conn_mcus: List[MPRemoteBoard],
    title: str = "Connected boards",
    refresh: bool = True,
    *,
    title_style="magenta",
    header_style="bold magenta",
):
    """
    builds a rich table with the connected boards information
    The columns of the table are adjusted to the terminal width > 90
    the columns are :
                Narrow      Wide
    - Serial    Yes         Yes
    - Family    abbrv.      Yes
    - Port      -           yes
    - Variant   Yes         Yes     only if any of the mcus have a variant
    - Board     Yes         Yes     BOARD_ID and Description, and the description from board_info.toml
    - CPU       -           Yes
    - Version   Yes         Yes
    - Build     *           *       only if any of the mcus have a build
    - Location  -           -       only if --usb is given
    """
    # refresh if requested
    if refresh:
        for mcu in track(
            conn_mcus,
            description="Updating board info",
            transient=True,
            show_speed=False,
            refresh_per_second=1,
        ):
            try:
                mcu.get_mcu_info()
            except ConnectionError:
                continue
    table = Table(
        title=title,
        title_style=title_style,
        header_style=header_style,
        collapse_padding=True,
        padding=(0, 0),
    )
    # Build the table
    # check if the terminal is wide enough to show all columns or if we need to collapse some
    is_wide = console.width > 99
    needs_build = any(mcu.build for mcu in conn_mcus)
    needs_variant = any(mcu.variant for mcu in conn_mcus)

    table.add_column("Serial" if is_wide else "Ser.", overflow="fold")
    table.add_column("Family" if is_wide else "Fam.", overflow="crop", max_width=None if is_wide else 4)
    if is_wide:
        table.add_column("Port")
    table.add_column("Board", overflow="fold")
    if needs_variant:
        table.add_column("Variant")
    if is_wide:
        table.add_column("CPU")
    table.add_column("Version", overflow="fold", min_width=5, max_width=16)
    if needs_build:
        table.add_column("Build" if is_wide else "Bld", justify="right")
    if config.usb:
        table.add_column("vid:pid", overflow="fold", max_width=14)
        table.add_column("Location", overflow="fold", max_width=60)
    # fill the table with the data
    for mcu in conn_mcus:
        description = f"[italic bright_cyan]{mcu.description}" if mcu.description else ""
        if "description" in mcu.toml:
            description += f"\n[italic bright_green]{mcu.toml['description']}"
        row = [
            mcu.serialport if is_wide else mcu.serialport.replace("/dev/tty", "tty"),
            abbrv_family(mcu.family, is_wide),
        ]
        if is_wide:
            row.append(mcu.port)
        row.append(f"{mcu.board}\n{description}".strip())
        if needs_variant:
            row.append(mcu.variant)
        if is_wide:
            row.append(mcu.cpu)
        row.append(clean_version(mcu.version))
        if needs_build:
            row.append(mcu.build)
        if config.usb:
            row.append(f"{mcu.vid:04x}:{mcu.pid:04x}")
            row.append(mcu.location)

        table.add_row(*row)
    return table
