"""joepie_tools - harmless prank GUI tools."""
__version__ = "0.4.0"

from .hackerprank import (
    fake_hack_screen, fake_matrix, fake_terminal, fake_file_dump, fake_warning_popup,
    fake_bsod, fake_update_screen, fake_virus_scan, random_popups,
    run_full_prank
)
from .cli import main

__all__ = [
    "fake_hack_screen","fake_matrix","fake_terminal","fake_file_dump","fake_warning_popup",
    "fake_bsod","fake_update_screen","fake_virus_scan","random_popups",
    "run_full_prank","main"
]
