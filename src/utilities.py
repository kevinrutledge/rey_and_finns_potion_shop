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

        # Sort potions by demand descending
        sorted_potions = sorted(day_potions, key=lambda x: x['demand'], reverse=True)

        purchase_plan = []
        remaining_gold = gold
        remaining_potion_capacity = available_potion_capacity
        remaining_ml_capacity = available_ml_capacity

        for potion in sorted_potions:
            potion_name = potion['name']
            composition = potion['composition']  # [r, g, b, d]
            demand = potion['demand']
            price = potion['price']

            logger.debug(f"Evaluating potion: {potion_name} with demand {demand}, price {price}")

            # Determine which barrels contribute to this potion's potion_type
            dominant_color_index = composition.index(max(composition))
            color_map = {0: 'red', 1: 'green', 2: 'blue', 3: 'dark'}
            dominant_color = color_map.get(dominant_color_index, 'unknown')
            logger.debug(f"Dominant color for potion {potion_name}: {dominant_color}")

            # Filter barrels matching dominant color
            matching_barrels = [b for b in wholesale_catalog if b.potion_type[dominant_color_index] == 1]

            if not matching_barrels:
                logger.warning(f"No matching barrels found for dominant color {dominant_color} of potion {potion_name}. Skipping.")
                continue  # No available barrels for this potion's dominant color

            # Sort matching barrels by size ascending (Mini to Large) for flexibility
            size_order = ['MINI', 'SMALL', 'MEDIUM', 'LARGE']
            matching_barrels.sort(key=lambda b: size_order.index(b.sku.split('_')[0]) if b.sku.split('_')[0] in size_order else 4)

            for barrel in matching_barrels:
                barrel_sku = barrel.sku
                barrel_ml = barrel.ml_per_barrel
                barrel_price = barrel.price
                barrel_quantity_available = barrel.quantity

                logger.debug(f"Considering barrel SKU {barrel_sku} with {barrel_ml} ml and price {barrel_price}.")

                # Determine max barrels based on available gold and inventory capacity
                max_affordable = remaining_gold // barrel_price if barrel_price > 0 else 0
                max_by_gold = min(max_affordable, barrel_quantity_available)

                max_by_capacity_ml = remaining_ml_capacity // (barrel_ml)
                max_by_capacity_potions = remaining_potion_capacity  # Assuming each ml contributes to one potion

                feasible_barrels = min(max_by_gold, max_by_capacity_ml, max_by_capacity_potions)

                if feasible_barrels <= 0:
                    logger.debug(f"No feasible barrels to purchase for SKU {barrel_sku}.")
                    continue

                # Add to purchase plan
                purchase_plan.append(BarrelPurchase(sku=barrel_sku, quantity=feasible_barrels))
                logger.info(f"Planned to purchase {feasible_barrels} barrels of SKU {barrel_sku}.")

                # Update remaining capacities and gold
                total_cost = feasible_barrels * barrel_price
                remaining_gold -= total_cost
                remaining_ml_capacity -= feasible_barrels * barrel_ml
                remaining_potion_capacity -= feasible_barrels  # Assuming each barrel adds ml equivalent to one potion

                logger.debug(f"Updated Remaining Capacities - Potion: {remaining_potion_capacity}, ML: {remaining_ml_capacity}, Gold: {remaining_gold}")

                # Break if no more capacity or gold
                if remaining_potion_capacity <= 0 or remaining_gold < min([b.price for b in matching_barrels if b.price > 0], default=0):
                    logger.debug("No more capacity or insufficient gold to purchase additional barrels. Stopping purchase plan calculation.")
                    break

        logger.info(f"Generated purchase plan: {purchase_plan}")
        return purchase_plan