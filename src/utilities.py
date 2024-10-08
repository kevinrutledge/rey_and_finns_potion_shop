import math
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple
from typing import List, Dict
from pydantic import BaseModel
from src.potion_coefficients import potion_coefficients

logger = logging.getLogger(__name__)

# Constants for capacity calculations
POTION_CAPACITY_PER_UNIT = 50       # Each potion capacity unit allows storage of 50 potions
ML_CAPACITY_PER_UNIT = 10000        # Each ML capacity unit allows storage of 10000 ml
CAPACITY_UNIT_COST = 1000           # Cost per capacity unit in gold
DAYS_PER_WEEK = 7                   # Days of week constant
LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")
IN_GAME_DAYS = [
    "Hearthday",
    "Crownday",
    "Blesseday",
    "Soulday",
    "Edgeday",
    "Bloomday",
    "Aracanaday"
]

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: List[int]  # [red, green, blue, dark]
    price: int
    quantity: int  # Quantity available for sale in catalog

class BarrelPurchase(BaseModel):
    sku: str
    quantity: int

class Utils:
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

        EPOCH = datetime(2024, 1, 1, 0, 0, 0, tzinfo=LOCAL_TIMEZONE)
        delta = real_time - EPOCH
        total_hours = int(delta.total_seconds() // 3600)

        in_game_day_index = (total_hours // 24) % DAYS_PER_WEEK
        in_game_day = IN_GAME_DAYS[in_game_day_index]
        in_game_hour = real_time.hour

        # Apply Even/Odd Rounding Logic
        if real_time.hour % 2 == 1:
            # Odd hour: round up to next hour
            rounded_time = (real_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            # Check if day changes
            if rounded_time.day != real_time.day:
                in_game_day_index = (in_game_day_index + 1) % DAYS_PER_WEEK
                in_game_day = IN_GAME_DAYS[in_game_day_index]
        else:
            # Even hour: round down to same hour
            rounded_time = real_time.replace(minute=0, second=0, microsecond=0)

        # Update in_game_hour based on rounded_time
        in_game_hour = rounded_time.hour

        return in_game_day, in_game_hour


    @staticmethod
    def get_hour_block(current_hour: int) -> str:
        """
        Determine hour block based on current in-game hour.
        
        Args:
            current_hour (int): current in-game hour (1-24).
        
        Returns:
            str: hour block ('night', 'morning', 'afternoon', 'evening').
        """
        try:
            if current_hour in [0, 2, 4]:
                return "night"
            elif current_hour in [6, 8, 10]:
                return "morning"
            elif current_hour in [12, 14, 16]:
                return "afternoon"
            elif current_hour in [18, 20, 22]:
                return "evening"
            else:
                return "invalid"
        except Exception as e:
            raise e


    @staticmethod
    def get_current_real_time() -> datetime:
        """
        Get current real-world local time.

        Returns:
            datetime: Current real-world local time with timezone.
        """
        return datetime.now(tz=LOCAL_TIMEZONE)


    @staticmethod
    def normalize_potion_type(potion_type: List[int]) -> List[int]:
        """
        Normalizes potion_type to sum to 100.
        """
        total = sum(potion_type)
        if total == 0:
            raise ValueError("Total of potion_type cannot be zero.")
        factor = 100 / total
        normalized = [int(x * factor) for x in potion_type]
        # Adjust for rounding errors
        difference = 100 - sum(normalized)
        if difference != 0:
            for i in range(len(normalized)):
                if normalized[i] + difference >= 0:
                    normalized[i] += difference
                    break
        logger.debug(f"Normalized potion_type from {potion_type} to {normalized}")
        return normalized
    

    @staticmethod
    def calculate_purchase_plan(wholesale_catalog: List[Barrel], current_inventory: Dict[str, int], gold: int, potion_capacity_units: int, ml_capacity_units: int) -> List[BarrelPurchase]:
        """
        Determines which barrels to purchase based on potion demands and current inventory.

        Args:
            wholesale_catalog (List[Barrel]): List of available barrels for purchase.
            current_inventory (Dict[str, int]): Current ML counts from global_inventory.
            gold (int): Current gold balance.
            potion_capacity_units (int): Current potion capacity units.
            ml_capacity_units (int): Current ML capacity units.

        Returns:
            List[BarrelPurchase]: List of barrels to purchase.
        """
        logger.debug("Calculating purchase plan based on current inventory and potion demands.")

        # Initialize capacities
        potion_capacity_limit = potion_capacity_units * POTION_CAPACITY_PER_UNIT
        ml_capacity_limit = ml_capacity_units * ML_CAPACITY_PER_UNIT
        total_potions = current_inventory.get('total_potions', 0)
        total_ml = current_inventory.get('total_ml', 0)

        available_potion_capacity = potion_capacity_limit - total_potions
        available_ml_capacity = ml_capacity_limit - total_ml

        # Compute in-game time
        real_time = Utils.get_current_real_time()
        in_game_day, in_game_hour = Utils.compute_in_game_time(real_time)
        hour_block = Utils.get_hour_block(in_game_hour)
        logger.debug(f"Computed In-Game Time - Day: {in_game_day}, Hour: {in_game_hour}, Block: {hour_block}")

        # Fetch potion demands
        day_potions = potion_coefficients.get(in_game_day, {}).get(hour_block, [])
        if not day_potions:
            logger.warning(f"No potion coefficients found for Day: {in_game_day}, Hour Block: {hour_block}. Returning empty purchase plan.")
            return []

        logger.debug(f"Potion demands for Day: {in_game_day}, Block: {hour_block}: {day_potions}")

        # Calculate ROI for each potion and sort potions by ROI descending
        for potion in day_potions:
            composition = potion['composition']
            price = potion['price']
            demand = potion['demand']
            # Estimate ROI as (price * demand) / total_ml_needed
            total_ml_needed = sum(composition)
            potion['roi'] = (price * demand) / total_ml_needed if total_ml_needed > 0 else 0

        sorted_potions = sorted(day_potions, key=lambda x: x['roi'], reverse=True)
        logger.debug(f"Potions sorted by ROI: {sorted_potions}")

        # Initialize purchase plan and tracking variables
        purchase_plan = []
        remaining_gold = gold
        remaining_ml_capacity = available_ml_capacity

        # Dictionary to keep track of ml required per color
        total_ml_required = {'red': 0, 'green': 0, 'blue': 0, 'dark': 0}

        # Loop through potions and calculate required ml
        for potion in sorted_potions:
            if remaining_ml_capacity <= 0 or remaining_gold <= 0:
                logger.debug("No remaining ML capacity or gold. Breaking out of potion loop.")
                break

            composition = potion['composition']
            potion_name = potion['name']
            price = potion['price']
            demand = potion['demand']

            # Determine how many potions we can make
            max_potions_by_capacity = available_potion_capacity
            ml_needed_per_potion = sum(composition)
            max_potions_by_ml = remaining_ml_capacity // ml_needed_per_potion
            potions_to_make = min(demand, max_potions_by_capacity, max_potions_by_ml)

            if potions_to_make <= 0:
                logger.debug(f"Cannot make any more of potion {potion_name}. Skipping.")
                continue

            logger.debug(f"Planning to make {potions_to_make} of {potion_name}.")

            # Update total_ml_required
            for idx, color in enumerate(['red', 'green', 'blue', 'dark']):
                ml_needed = composition[idx] * potions_to_make
                total_ml_required[color] += ml_needed

            # Update capacities
            remaining_ml_capacity -= ml_needed_per_potion * potions_to_make
            available_potion_capacity -= potions_to_make

        logger.debug(f"Total ML required per color: {total_ml_required}")

        # Now, determine which barrels to buy to fulfill total_ml_required
        # Create a list of barrel options per color
        barrels_by_color = {'red': [], 'green': [], 'blue': [], 'dark': []}
        for barrel in wholesale_catalog:
            color_idx = barrel.potion_type.index(1)
            color = ['red', 'green', 'blue', 'dark'][color_idx]
            barrels_by_color[color].append(barrel)

        # For each color, decide which barrels to buy
        for color, ml_needed in total_ml_required.items():
            if ml_needed <= 0:
                logger.debug(f"No ml needed for color {color}. Skipping.")
                continue

            barrels = sorted(barrels_by_color[color], key=lambda b: b.price / b.ml_per_barrel)
            ml_remaining = ml_needed

            for barrel in barrels:
                if ml_remaining <= 0 or remaining_gold <= 0:
                    logger.debug(f"No ml remaining needed for color {color} or no gold left. Breaking out of barrel loop.")
                    break

                max_barrels_affordable = remaining_gold // barrel.price
                max_barrels_available = barrel.quantity
                ml_per_barrel = barrel.ml_per_barrel

                barrels_needed = math.ceil(ml_remaining / ml_per_barrel)
                barrels_to_buy = min(barrels_needed, max_barrels_affordable, max_barrels_available)

                if barrels_to_buy <= 0:
                    logger.debug(f"Cannot buy any more barrels of SKU {barrel.sku}. Skipping.")
                    continue

                # Update ml_remaining and remaining_gold
                ml_provided = barrels_to_buy * ml_per_barrel
                ml_remaining -= ml_provided
                remaining_gold -= barrels_to_buy * barrel.price

                # Update purchase plan
                existing_purchase = next((p for p in purchase_plan if p.sku == barrel.sku), None)
                if existing_purchase:
                    existing_purchase.quantity += barrels_to_buy
                else:
                    purchase_plan.append(BarrelPurchase(sku=barrel.sku, quantity=barrels_to_buy))

                logger.info(f"Decided to buy {barrels_to_buy} of barrel SKU {barrel.sku} for color {color}.")
                logger.debug(f"Remaining ml needed for color {color}: {ml_remaining}. Remaining gold: {remaining_gold}.")

        logger.info(f"Final Purchase Plan: {purchase_plan}")
        return purchase_plan