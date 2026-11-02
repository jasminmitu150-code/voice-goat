"""Flag capture system for VoiceGoat gamification."""

from services.common.flags.models import Flag, FlagCapture, FlagDifficulty
from services.common.flags.service import FlagService, flag_service
from services.common.flags.decorators import vulnerable, check_flag_in_response

__all__ = [
    "Flag",
    "FlagCapture",
    "FlagDifficulty",
    "FlagService",
    "flag_service",
    "vulnerable",
    "check_flag_in_response",
]
