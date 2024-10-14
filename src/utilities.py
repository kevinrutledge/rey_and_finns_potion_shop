import math
import sqlalchemy
import logging
from src import database as db
from src import game_constants as gc
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple
from typing import List, Dict
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Game time adjustment constants
TICK_HOURS = 2
TICKS_AHEAD = 3
GAME_TIME_OFFSET = timedelta(hours=TICK_HOURS * TICKS_AHEAD)

LOCAL_TIMEZONE = ZoneInfo("America/Los_Angeles")

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
        Returns current in-game day and hour.
        """
        try:
            with db.engine.begin() as connection:
                query = """
                    SELECT in_game_day, in_game_hour
                    FROM in_game_time
                    ORDER BY created_at DESC
                    LIMIT 1;
                """
                logger.debug(f"Executing query to fetch latest in-game time: {query.strip()}")
                result = connection.execute(sqlalchemy.text(query))
                row = result.mappings().fetchone()
                if row:
                    in_game_day = row['in_game_day']
                    in_game_hour = row['in_game_hour']
                    logger.debug(f"Fetched in-game time from DB: Day: {in_game_day}, Hour: {in_game_hour}")
                    return in_game_day, in_game_hour
                else:
                    logger.error("No in-game time found in database.")
                    raise ValueError("No in-game time found in database.")
        except Exception as e:
            logger.exception(f"Exception in get_latest_in_game_time_from_db: {e}")
            raise
    

    @staticmethod
    def get_future_in_game_time(ticks_ahead: int) -> Tuple[str, int]:
        """
        Returns in-game day and hour ticks_ahead hours from now.
        """
        total_ticks_ahead = TICKS_AHEAD + ticks_ahead
        future_time = datetime.now(tz=LOCAL_TIMEZONE) + timedelta(hours=TICK_HOURS * total_ticks_ahead)
        EPOCH = datetime(2024, 1, 1, 0, 0, 0, tzinfo=LOCAL_TIMEZONE)
        delta = future_time - EPOCH
        total_hours = int(delta.total_seconds() // 3600)
        in_game_day_index = (total_hours // 24) % gc.DAYS_PER_WEEK
        in_game_day = gc.IN_GAME_DAYS[in_game_day_index]

        # Apply Even/Odd Rounding Logic
        if future_time.hour % 2 == 1:
            # Odd hour: round up to next even hour
            rounded_time = (future_time + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        else:
            # Even hour: round down to same hour
            rounded_time = future_time.replace(minute=0, second=0, microsecond=0)

        # Update in-game hour
        in_game_hour = rounded_time.hour

        # Check if day changes due to rounding
        if rounded_time.date() != future_time.date():
            in_game_day_index = (in_game_day_index + 1) % gc.DAYS_PER_WEEK
            in_game_day = gc.IN_GAME_DAYS[in_game_day_index]
            logger.debug(f"Day changed after rounding. New In-Game Day Index: {in_game_day_index}, In-Game Day: {in_game_day}")

        return in_game_day, in_game_hour


    @staticmethod
    def select_pricing_strategy(potion_capacity_units):
        """
        Selects pricing strategy based on potion capacity units.
        """
        if potion_capacity_units <= 1:
            return "PRICE_STRATEGY_SKIMMING"
        elif potion_capacity_units <= 2:
            return "PRICE_STRATEGY_PENETRATION"
        elif potion_capacity_units <= 4:
            return "PRICE_STRATEGY_TIERED"
        else:
            return "PRICE_STRATEGY_DYNAMIC"


    @staticmethod
    def calculate_desired_potion_quantities(
        potion_capacity_units: int,
        current_potions: Dict[str, int],
        potion_priorities: List[Dict],
        pricing_strategy: str
    ) -> Dict[str, int]:
        """
        Calculates desired potion quantities based on capacity and pricing strategy.
        """
        desired_potions = {}
        total_capacity = potion_capacity_units * gc.POTION_CAPACITY_PER_UNIT
        total_potions_current = sum(current_potions.values())
        capacity_remaining = total_capacity - total_potions_current

        # Determine number of potions to consider based on strategy
        if pricing_strategy == "PRICE_STRATEGY_SKIMMING":
            num_potions_to_consider = 3
        elif pricing_strategy == "PRICE_STRATEGY_PENETRATION":
            num_potions_to_consider = 5
        else:
            num_potions_to_consider = len(potion_priorities)

        potions_to_consider = potion_priorities[:num_potions_to_consider]

        # Initialize desired quantities with current quantities
        for potion in potions_to_consider:
            potion_name = potion["name"]
            desired_potions[potion_name] = current_potions.get(potion_name, 0)

        # Increment desired quantities in increments of 5
        increment = 5
        while capacity_remaining >= increment:
            for potion in potions_to_consider:
                potion_name = potion["name"]
                desired_potions[potion_name] += increment
                capacity_remaining -= increment
                logger.debug(f"Potion: {potion_name}, Desired Qty: {desired_potions[potion_name]}, Capacity Remaining: {capacity_remaining}")
                if capacity_remaining < increment:
                    break
            else:
                continue
            break

        logger.info(f"Desired potion quantities: {desired_potions}")
        return desired_potions


    @staticmethod
    def calculate_ml_needed(
        desired_potions: Dict[str, int],
        current_potions: Dict[str, int],
        potion_recipes: Dict[str, Dict]
    ) -> Dict[str, int]:
        """
        Calculates total ml needed per color to meet desired potion quantities.
        """
        ml_needed = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}

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
    def get_barrel_purchase_plan(
        ml_needed: Dict[str, int],
        current_ml: Dict[str, int],
        ml_capacity_limit: int,
        gold: int,
        ml_capacity_units: int,
        wholesale_catalog: List[Barrel],
        pricing_strategy: str
    ) -> List[Dict]:
        """
        Determines which barrels to purchase based on ml needed and constraints.
        """
        purchase_plan = []
        total_cost = 0
        total_ml_after_purchase = {color: current_ml.get(color, 0) for color in current_ml}

        # Build mapping of available barrels from wholesale catalog
        barrel_options = {}
        for barrel in wholesale_catalog:
            barrel_options[barrel.sku] = {
                'ml': barrel.ml_per_barrel,
                'price': barrel.price,
                'color': Utils.get_color_from_potion_type(barrel.potion_type),
                'quantity_available': barrel.quantity
            }

        # Define colors to consider based on capacity units
        colors_priority = ['red_ml', 'green_ml', 'blue_ml']
        if ml_capacity_units >= 4 and pricing_strategy != "PRICE_STRATEGY_SKIMMING":
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
            if pricing_strategy == "PRICE_STRATEGY_SKIMMING":
                barrel_sizes = ['SMALL']
            elif pricing_strategy == "PRICE_STRATEGY_PENETRATION":
                barrel_sizes = ['MEDIUM', 'SMALL']
            else:
                barrel_sizes = ['LARGE', 'MEDIUM', 'SMALL']

            # Build list of possible barrels for this color
            possible_barrels = [
                sku for sku, details in barrel_options.items()
                if details['color'] == color_ml and any(size in sku for size in barrel_sizes)
            ]

            # Prioritize barrels by size (ml per price)
            barrels_to_consider = sorted(possible_barrels, key=lambda x: barrel_options[x]['ml'] / barrel_options[x]['price'], reverse=True)

            for barrel_sku in barrels_to_consider:
                barrel = barrel_options[barrel_sku]
                barrel_price = barrel['price']
                barrel_ml = barrel['ml']
                quantity_available = barrel['quantity_available']

                logger.debug(f"Considering barrel {barrel_sku}: Price {barrel_price}, ML {barrel_ml}, Available: {quantity_available}")

                # Calculate maximum barrels we can buy based on ml shortfall and capacity
                max_barrels_needed = -(-ml_shortfall // barrel_ml)  # Ceiling division
                capacity_limit = (ml_capacity_limit - total_ml_after_purchase[color_ml]) // barrel_ml
                max_affordable_barrels = (gold - total_cost) // barrel_price
                quantity = min(max_barrels_needed, capacity_limit, max_affordable_barrels, quantity_available)

                if quantity > 0:
                    purchase_plan.append({'sku': barrel_sku, 'quantity': quantity})
                    total_cost += barrel_price * quantity
                    total_ml_after_purchase[color_ml] += barrel_ml * quantity
                    ml_shortfall -= barrel_ml * quantity
                    logger.info(f"Added {quantity} of {barrel_sku} to purchase plan. Total cost so far: {total_cost}")
                    # If we've met ml needed or run out of gold, break
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
    def get_bottle_plan(
        current_ml: Dict[str, int],
        desired_potions: Dict[str, int],
        current_potions: Dict[str, int],
        potion_capacity_limit: int,
        potion_recipes: Dict[str, Dict]
    ) -> List[Dict]:
        """
        Generates bottle plan based on available ml, desired potion quantities, current potions, and capacity constraints.
        Returns list of potions to bottle in format required by bottler API.
        """
        potions_to_bottle = []
        total_potions_after_bottling = sum(current_potions.values())

        ml_available = current_ml.copy()

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
                    possible = ml_available[color] // recipe[color]
                    max_quantity_possible = min(max_quantity_possible, possible)

            if max_quantity_possible <= 0:
                continue  # Cannot bottle this potion due to ml constraints

            # Adjust quantity_needed based on potion capacity
            available_capacity = potion_capacity_limit - total_potions_after_bottling
            if available_capacity <= 0:
                break  # No capacity to bottle more potions

            quantity_to_bottle = min(max_quantity_possible, available_capacity, quantity_needed)

            # Recalculate required_ml for adjusted quantity
            required_ml = {color: recipe[color] * quantity_to_bottle for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']}

            # Update ml_available and total_potions_after_bottling
            for color in required_ml:
                ml_available[color] -= required_ml[color]
            total_potions_after_bottling += quantity_to_bottle

            # Add to potions_to_bottle
            potions_to_bottle.append({
                'potion_type': Utils.normalize_potion_type([
                    recipe['red_ml'],
                    recipe['green_ml'],
                    recipe['blue_ml'],
                    recipe['dark_ml']
                ]),
                'quantity': quantity_to_bottle
            })

            logger.info(f"Planned to bottle {quantity_to_bottle} of {potion_name}.")

        logger.info(f"Final bottle plan: {potions_to_bottle}")
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
        # logger.debug(f"Normalized potion_type from {potion_type} to {normalized}")
        return normalized
    

    @staticmethod
    def get_color_from_potion_type(potion_type: List[int]) -> str:
        """
        Returns color_ml string based on potion_type.
        """
        colors = ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']
        for idx, val in enumerate(potion_type):
            if val == 1:
                return colors[idx]
        raise ValueError("Invalid potion_type in barrel.")