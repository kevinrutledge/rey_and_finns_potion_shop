from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple

class Utils:
    IN_GAME_DAYS = [
        "Hearthday",
        "Crownday",
        "Blesseday",
        "Soulday",
        "Edgeday",
        "Bloomday",
        "Aracanaday"
    ]
    DAYS_PER_WEEK = len(IN_GAME_DAYS)
    LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")

    @staticmethod
    def compute_in_game_time(real_time: datetime) -> Tuple[str, int]:
        """
        Convert real-time to in-game day and hour.

        Rounding Rules:
        - If real_time.hour is odd:
            - Round up to next hour.
        - If real_time.hour is even:
            - Round down to same hour.

        Args:
            real_time (datetime): Real-world local timestamp to convert.

        Returns:
            Tuple[str, int]: Tuple containing in-game day and in-game hour.
        """

        EPOCH = datetime(2024, 1, 1, 0, 0, 0, tzinfo=Utils.LOCAL_TIMEZONE)
        delta = real_time - EPOCH
        total_hours = int(delta.total_seconds() // 3600)

        in_game_day_index = (total_hours // 24) % Utils.DAYS_PER_WEEK
        in_game_day = Utils.IN_GAME_DAYS[in_game_day_index]
        in_game_hour = real_time.hour

        # Apply Even/Odd Rounding Logic
        if real_time.hour % 2 == 1:
            # Odd hour: round up to next hour
            rounded_time = (real_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            # Check if day changes
            if rounded_time.day != real_time.day:
                in_game_day_index = (in_game_day_index + 1) % Utils.DAYS_PER_WEEK
                in_game_day = Utils.IN_GAME_DAYS[in_game_day_index]
        else:
            # Even hour: round down to same hour
            rounded_time = real_time.replace(minute=0, second=0, microsecond=0)

        # Update in_game_hour based on rounded_time
        in_game_hour = rounded_time.hour

        return in_game_day, in_game_hour


    def get_hour_block(current_hour: int) -> str:
        """
        Determine hour block based on current in-game hour.
        
        Args:
            current_hour (int): current in-game hour (1-24).
        
        Returns:
            str: hour block ('night', 'morning', 'afternoon', 'evening').
        """
        try:
            if current_hour in [2, 4, 6]:
                return "night"
            elif current_hour in [8, 10, 12]:
                return "morning"
            elif current_hour in [14, 16, 18]:
                return "afternoon"
            elif current_hour in [20, 22, 24]:
                return "evening"
            else:
                return "invalid"
        except Exception as e:
            raise e