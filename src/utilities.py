import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple
from typing import List, Dict
from src.models import Barrel, BarrelPurchase, BarrelDelivery

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

    # Constants for capacity calculations
    POTION_CAPACITY_PER_UNIT = 50      # Each potion capacity unit allows storage of 50 potions
    ML_CAPACITY_PER_UNIT = 10000        # Each ML capacity unit allows storage of 10,000 ml
    CAPACITY_UNIT_COST = 1000           # Cost per capacity unit in gold

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

    @staticmethod
    def get_current_real_time() -> datetime:
        """
        Get the current real-world local time.

        Returns:
            datetime: Current real-world local time with timezone.
        """
        return datetime.now(tz=Utils.LOCAL_TIMEZONE)
    
    @staticmethod
    def get_dominant_color(potion_type: List[int]) -> str:
        """
        Determines the dominant color based on potion_type list.
        Returns 'mixed' if multiple colors are present.
        """
        color_map = {0: 'red', 1: 'green', 2: 'blue', 3: 'dark'}
        dominant_colors = [color_map[i] for i, amount in enumerate(potion_type) if amount > 0]
        if len(dominant_colors) == 1:
            return dominant_colors[0]
        elif len(dominant_colors) > 1:
            return 'mixed'
        else:
            return 'unknown'
    
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

        # Determine current capacity limits
        potion_capacity_limit = potion_capacity_units * POTION_CAPACITY_PER_UNIT
        ml_capacity_limit = ml_capacity_units * ML_CAPACITY_PER_UNIT
        logger.debug(f"Current Potion Capacity Limit: {potion_capacity_limit}, ML Capacity Limit: {ml_capacity_limit}")

        # Determine current total potions and ML
        total_potions = current_inventory.get('total_potions', 0)
        total_ml = current_inventory.get('total_ml', 0)
        logger.debug(f"Current Total Potions: {total_potions}, Current Total ML: {total_ml}")

        # Determine available capacities
        available_potion_capacity = potion_capacity_limit - total_potions
        available_ml_capacity = ml_capacity_limit - total_ml
        logger.debug(f"Available Potion Capacity: {available_potion_capacity}, Available ML Capacity: {available_ml_capacity}")

        # Get current in-game time
        real_time = Utils.get_current_real_time()
        in_game_day, in_game_hour = Utils.compute_in_game_time(real_time)
        hour_block = Utils.get_hour_block(in_game_hour)
        logger.debug(f"Computed In-Game Time - Day: {in_game_day}, Hour: {in_game_hour}, Block: {hour_block}")

        # Fetch potion demands for the current day and hour block
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

            # Find corresponding barrel in wholesale_catalog
            matching_barrels = [barrel for barrel in wholesale_catalog if barrel.potion_type == composition]
            if not matching_barrels:
                logger.debug(f"No matching barrels found for potion: {potion_name}. Skipping.")
                continue  # No available barrels for this potion

            barrel = matching_barrels[0]  # Assuming one barrel per potion type
            logger.debug(f"Found matching barrel: SKU {barrel.sku} for potion {potion_name}")

            # Determine how many barrels to buy based on demand and available capacity
            max_potions_based = math.floor((demand / 100) * potion_capacity_limit)
            max_potions_based = min(max_potions_based, remaining_potion_capacity)
            logger.debug(f"Max potions based on demand: {max_potions_based}")

            # Determine how many barrels based on ML availability
            ml_required_per_barrel = barrel.ml_per_barrel
            if ml_required_per_barrel == 0:
                logger.debug(f"Barrel SKU {barrel.sku} has 0 ML per barrel. Skipping.")
                continue  # Avoid division by zero

            max_barrels_ml = math.floor(remaining_ml_capacity / ml_required_per_barrel)
            logger.debug(f"Max barrels based on ML availability: {max_barrels_ml}")

            # Determine the feasible number of barrels to purchase
            feasible_barrels = min(max_potions_based, max_barrels_ml)
            if feasible_barrels <= 0:
                logger.debug(f"No feasible barrels to purchase for potion: {potion_name}. Skipping.")
                continue

            # Determine cost
            total_cost = feasible_barrels * barrel.price
            if total_cost > remaining_gold:
                feasible_barrels = math.floor(remaining_gold / barrel.price)
                total_cost = feasible_barrels * barrel.price
                logger.debug(f"Adjusted feasible barrels based on gold availability: {feasible_barrels}, Total Cost: {total_cost}")

            if feasible_barrels <= 0:
                logger.debug(f"Insufficient gold to purchase any barrels for potion: {potion_name}. Skipping.")
                continue

            # Add to purchase plan
            purchase_plan.append(BarrelPurchase(sku=barrel.sku, quantity=feasible_barrels))
            logger.info(f"Planned to purchase {feasible_barrels} barrels of SKU {barrel.sku} for potion {potion_name}")

            # Update remaining capacities and gold
            remaining_potion_capacity -= feasible_barrels
            remaining_ml_capacity -= feasible_barrels * ml_required_per_barrel
            remaining_gold -= feasible_barrels * barrel.price

            logger.debug(f"Updated Remaining Capacities - Potion: {remaining_potion_capacity}, ML: {remaining_ml_capacity}, Gold: {remaining_gold}")

            # Break if no more capacity or gold
            if remaining_potion_capacity <= 0 or remaining_gold < min([b.price for b in wholesale_catalog]):
                logger.debug("No more capacity or insufficient gold to purchase additional barrels. Stopping purchase plan calculation.")
                break

        logger.info(f"Generated purchase plan: {purchase_plan}")
        return purchase_plan