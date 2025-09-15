"""
Dice Apply - Automated job application tool for Dice.com

A command-line tool for automating job applications on Dice.com with smart
session management and anti-detection features.
"""

__version__ = "0.1.0"
__author__ = "Sam Savage"
__email__ = "samatcrispy@gmail.com"
__description__ = "Automated job application tool for Dice.com"

from .core import get_driver, login_to_dice, get_job_links, apply_to_job
from .cli import main

__all__ = [
    "get_driver",
    "login_to_dice",
    "get_job_links",
    "apply_to_job",
    "main",
]