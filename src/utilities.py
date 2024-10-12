import math
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple
from typing import List, Dict
from pydantic import BaseModel
from src.potions import POTION_PRIORITIES, DEFAULT_POTIONS

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
    def get_current_in_game_time() -> Tuple[str, int]:
        """
        Returns the current in-game day and hour.
        """
        real_time = datetime.now(tz=LOCAL_TIMEZONE)
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
    def get_future_in_game_time(ticks_ahead: int) -> Tuple[str, int]:
        """
        Returns the in-game day and hour ticks_ahead hours from now.
        """
        future_time = datetime.now(tz=LOCAL_TIMEZONE) + timedelta(hours=(ticks_ahead * 2))
        EPOCH = datetime(2024, 1, 1, 0, 0, 0, tzinfo=LOCAL_TIMEZONE)
        delta = future_time - EPOCH
        total_hours = int(delta.total_seconds() // 3600)

        in_game_day_index = (total_hours // 24) % DAYS_PER_WEEK
        in_game_day = IN_GAME_DAYS[in_game_day_index]
        in_game_hour = future_time.hour

        # Apply Even/Odd Rounding Logic
        if future_time.hour % 2 == 1:
            # Odd hour: round up to next hour
            rounded_time = (future_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
            # Check if day changes
            if rounded_time.day != future_time.day:
                in_game_day_index = (in_game_day_index + 1) % DAYS_PER_WEEK
                in_game_day = IN_GAME_DAYS[in_game_day_index]
        else:
            # Even hour: round down to same hour
            rounded_time = future_time.replace(minute=0, second=0, microsecond=0)

        # Update in_game_hour based on rounded_time
        in_game_hour = rounded_time.hour

        return in_game_day, in_game_hour


    @staticmethod
    def select_pricing_strategy(potion_capacity_units: int) -> str:
        """
        Determines the pricing strategy based on potion capacity units.
        """
        if potion_capacity_units == 1:
            strategy = "PRICE_STRATEGY_PREMIUM"
        elif potion_capacity_units == 2:
            strategy = "PRICE_STATEGY_COMPETITIVE"
        else:
            strategy = "PRICE_STRATEGY_PENETRATION"
        logger.info(f"Selected pricing strategy: {strategy}")
        return strategy


    @staticmethod
    def calculate_desired_potion_quantities(potion_capacity_units: int, current_potions: Dict[str, int], potion_priorities: List[Dict]) -> Dict[str, int]:
        desired_potions = {}
        total_capacity = potion_capacity_units * POTION_CAPACITY_PER_UNIT
        max_quantity_per_potion = 15 if potion_capacity_units == 1 else total_capacity // len(potion_priorities)
        increment = 5  # Increment by 5

        total_potions_current = sum(current_potions.values())
        capacity_remaining = total_capacity - total_potions_current

        num_potions_to_consider = 3 if potion_capacity_units == 1 else len(potion_priorities)

        # Initialize desired quantities with current quantities
        for potion in potion_priorities[:num_potions_to_consider]:
            potion_name = potion["name"]
            desired_potions[potion_name] = current_potions.get(potion_name, 0)

        # Iteratively increment desired quantities
        while capacity_remaining >= increment:
            for potion in potion_priorities[:num_potions_to_consider]:
                potion_name = potion["name"]
                current_desired = desired_potions[potion_name]
                if current_desired < max_quantity_per_potion:
                    desired_potions[potion_name] += increment
                    capacity_remaining -= increment
                    logger.debug(f"Potion: {potion_name}, Desired Qty: {desired_potions[potion_name]}, Capacity Remaining: {capacity_remaining}")
                    if capacity_remaining < increment:
                        break
                else:
                    logger.debug(f"Potion: {potion_name} reached max quantity per potion.")
            else:
                # If none of the potions can be incremented further, break
                break

        logger.info(f"Desired potion quantities: {desired_potions}")
        return desired_potions


    @staticmethod
    def calculate_ml_needed(desired_potions: Dict[str, int], current_potions: Dict[str, int]) -> Dict[str, int]:
        """
        Calculates total ml needed per color to meet desired potion quantities.
        """
        ml_needed = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
        potion_recipes = {p['name']: p for p in DEFAULT_POTIONS}

        for potion_name, desired_quantity in desired_potions.items():
            current_quantity = current_potions.get(potion_name, 0)
            quantity_needed = desired_quantity - current_quantity
            if quantity_needed > 0:
                recipe = potion_recipes[potion_name]
                for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']:
                    ml_needed[color] += recipe[color] * quantity_needed
                logger.debug(f"Potion: {potion_name}, Qty Needed: {quantity_needed}, ML Needed: {ml_needed}")

        logger.info(f"Total ml needed per color: {ml_needed}")
        return ml_needed
    

    @staticmethod
    def get_barrel_purchase_plan(ml_needed: Dict[str, int], current_ml: Dict[str, int], ml_capacity_limit: int, gold: int, ml_capacity_units: int) -> List[Dict]:
        """
        Determines which barrels to purchase based on ml needed and constraints.
        Simplified logic per user request.
        """
        barrel_prices = {
            'SMALL_RED_BARREL': {'ml': 500, 'price': 100, 'color': 'red_ml'},
            'MEDIUM_RED_BARREL': {'ml': 2500, 'price': 250, 'color': 'red_ml'},
            'LARGE_RED_BARREL': {'ml': 10000, 'price': 500, 'color': 'red_ml'},
            'SMALL_GREEN_BARREL': {'ml': 500, 'price': 100, 'color': 'green_ml'},
            'MEDIUM_GREEN_BARREL': {'ml': 2500, 'price': 250, 'color': 'green_ml'},
            'LARGE_GREEN_BARREL': {'ml': 10000, 'price': 400, 'color': 'green_ml'},
            'SMALL_BLUE_BARREL': {'ml': 500, 'price': 120, 'color': 'blue_ml'},
            'MEDIUM_BLUE_BARREL': {'ml': 2500, 'price': 300, 'color': 'blue_ml'},
            'LARGE_BLUE_BARREL': {'ml': 10000, 'price': 600, 'color': 'blue_ml'},
            'LARGE_DARK_BARREL': {'ml': 10000, 'price': 750, 'color': 'dark_ml'}
        }

        purchase_plan = []
        total_cost = 0
        total_ml_after_purchase = {color: current_ml.get(color, 0) for color in current_ml}

        colors_priority = ['red_ml', 'green_ml', 'blue_ml']
        if ml_capacity_units >= 4:
            colors_priority.append('dark_ml')

        for color_ml in colors_priority:
            ml_shortfall = ml_needed.get(color_ml, 0) - current_ml.get(color_ml, 0)
            if ml_shortfall <= 0:
                continue

            logger.debug(f"Processing color {color_ml}. ML Shortfall: {ml_shortfall}")

            # Exclude dark barrels when ml_capacity_units < 4
            if ml_capacity_units < 4 and color_ml == 'dark_ml':
                logger.info(f"Skipping Dark Barrels due to ml capacity units < 4")
                continue

            # Determine barrel sizes to consider
            barrel_sizes = []
            if ml_capacity_units < 4:
                # Only consider small and medium barrels
                barrel_sizes = ['MEDIUM', 'SMALL']
            else:
                # Can consider large barrels
                barrel_sizes = ['LARGE', 'MEDIUM', 'SMALL']

            # Build list of possible barrels for this color
            possible_barrels = [sku for sku in barrel_prices if barrel_prices[sku]['color'] == color_ml and any(size in sku for size in barrel_sizes)]

            # Prioritize larger barrels
            barrels_to_consider = sorted(possible_barrels, key=lambda x: barrel_prices[x]['ml'], reverse=True)

            for barrel_sku in barrels_to_consider:
                barrel = barrel_prices[barrel_sku]
                barrel_price = barrel['price']
                barrel_ml = barrel['ml']
                logger.debug(f"Considering barrel {barrel_sku}: Price {barrel_price}, ML {barrel_ml}")

                # Calculate maximum barrels we can buy based on ml shortfall and capacity
                max_barrels_needed = -(-ml_shortfall // barrel_ml)  # Ceiling division
                capacity_limit = (ml_capacity_limit - total_ml_after_purchase[color_ml]) // barrel_ml
                max_affordable_barrels = (gold - total_cost) // barrel_price
                quantity = min(max_barrels_needed, capacity_limit, max_affordable_barrels)

                if quantity > 0:
                    purchase_plan.append({'sku': barrel_sku, 'quantity': quantity})
                    total_cost += barrel_price * quantity
                    total_ml_after_purchase[color_ml] += barrel_ml * quantity
                    ml_shortfall -= barrel_ml * quantity
                    logger.info(f"Added {quantity} of {barrel_sku} to purchase plan. Total cost so far: {total_cost}")
                    # If we've met the ml needed or run out of gold, break
                    if ml_shortfall <= 0 or gold - total_cost <= 0:
                        break
                else:
                    logger.debug(f"Cannot afford barrel {barrel_sku} or capacity reached.")

            if gold - total_cost <= 0:
                logger.info("Gold depleted.")
                break

        logger.info(f"Final barrel purchase plan: {purchase_plan}")
        return purchase_plan
    

    @staticmethod
    def get_bottle_plan(current_ml: Dict[str, int], desired_potions: Dict[str, int], current_potions: Dict[str, int], potion_capacity_limit: int) -> List[Dict]:
        """
        Generates the bottle plan based on available ml, desired potion quantities, current potions, and capacity constraints.
        Returns a list of potions to bottle in the format required by the bottler API.
        """
        potions_to_bottle = []
        total_potions_after_bottling = sum(current_potions.values())

        ml_available = current_ml.copy()

        potion_recipes = {p['name']: p for p in DEFAULT_POTIONS}

        for potion_name, desired_quantity in desired_potions.items():
            current_quantity = current_potions.get(potion_name, 0)
            quantity_needed = desired_quantity - current_quantity

            if quantity_needed <= 0:
                continue  # No need to bottle this potion

            # Check if we have enough ml of each color
            recipe = potion_recipes[potion_name]
            required_ml = {color: recipe[color] * quantity_needed for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']}

            # Adjust quantity_needed based on ml availability
            max_quantity_possible = quantity_needed
            for color in required_ml:
                if recipe[color] > 0:
                    max_possible = ml_available[color] // recipe[color]
                    max_quantity_possible = min(max_quantity_possible, max_possible)

            if max_quantity_possible <= 0:
                continue  # Cannot bottle this potion due to ml constraints

            # Adjust quantity_needed based on potion capacity
            available_capacity = potion_capacity_limit - total_potions_after_bottling
            if available_capacity <= 0:
                break  # No capacity to bottle more potions

            quantity_to_bottle = min(max_quantity_possible, available_capacity, quantity_needed)

            # Recalculate required_ml for the adjusted quantity
            required_ml = {color: recipe[color] * quantity_to_bottle for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']}

            # Update ml_available and total_potions_after_bottling
            for color in required_ml:
                ml_available[color] -= required_ml[color]
            total_potions_after_bottling += quantity_to_bottle

            # Add to potions_to_bottle
            potions_to_bottle.append({
                'potion_type': [recipe['red_ml'], recipe['green_ml'], recipe['blue_ml'], recipe['dark_ml']],
                'quantity': quantity_to_bottle
            })

        return potions_to_bottle


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