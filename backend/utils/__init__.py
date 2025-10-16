"""Utility functions and helpers for Aviator Bot."""

from .clipboard_utils import clear_clipboard, read_clipboard, select_and_copy_text
from .betting_helpers import (
    verify_bet_placed,
    verify_bet_is_active,
    estimate_multiplier,
    increase_stake,
    reset_stake
)
from .ocr_utils import preprocess_image_for_ocr

__all__ = [
    'clear_clipboard',
    'read_clipboard',
    'select_and_copy_text',
    'verify_bet_placed',
    'verify_bet_is_active',
    'estimate_multiplier',
    'increase_stake',
    'reset_stake',
    'preprocess_image_for_ocr'
]
