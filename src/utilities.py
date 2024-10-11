import math
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Tuple
from typing import List, Dict
from pydantic import BaseModel
from potions import POTION_PRIORITIES, DEFAULT_POTIONS

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
        future_time = datetime.now(tz=LOCAL_TIMEZONE) + timedeltahours=(ticks_ahead*2)
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
    def calculate_desired_potion_quantities(potion_capacity_units: int, pricing_strategy: str, potion_priorities: List[Dict]) -> Dict[str, int]:
        """
        Calculates desired potion quantities based on capacity and pricing strategy.
        """
        desired_potions = {}
        total_capacity = potion_capacity_units * POTION_CAPACITY_PER_UNIT

        if pricing_strategy == "PRICE_STRATEGY_PREMIUM":
            # Focus on the first 3 potions excluding Dark Potions
            count = 0
            for potion in potion_priorities:
                if potion["name"] == "Dark Potion":
                    continue  # Exclude Dark Potion in Premium Strategy
                desired_potions[potion["name"]] = 15  # Aim for up to 15 units
                count += 1
                if count == 3:
                    break
        elif pricing_strategy == "PRICE_STATEGY_COMPETITIVE":
            # Focus on the first 5 potions
            for potion in potion_priorities[:5]:
                desired_potions[potion["name"]] = 15  # Aim for up to 15 units
        else:
            # Penetration Strategy: Divide capacity among 6 potions
            total_desired_potions = int(0.8 * total_capacity)
            quantity_per_potion = total_desired_potions // 6
            for potion in potion_priorities[:6]:
                desired_potions[potion["name"]] = quantity_per_potion

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

        logger.info(f"Total ml needed per color: {ml_needed}")
        return ml_needed
    

    @staticmethod
    def get_barrel_purchase_plan(ml_needed: Dict[str, int], current_ml: Dict[str, int], ml_capacity_limit: int, gold: int, pricing_strategy: str) -> List[Dict]:
        """
        Determines which barrels to purchase based on ml needed and constraints.
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

        for color_ml in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']:
            ml_shortfall = ml_needed.get(color_ml, 0) - current_ml.get(color_ml, 0)
            if ml_shortfall <= 0:
                continue

            # Exclude Dark Barrels during Premium Strategy
            if pricing_strategy == "PRICE_STRATEGY_PREMIUM" and color_ml == 'dark_ml':
                logger.info(f"Skipping Dark Barrels during Premium Strategy for {color_ml}")
                continue

            while ml_shortfall > 0 and gold - total_cost > 0:
                # Decide which barrel to buy
                possible_barrels = [sku for sku, details in barrel_prices.items() if details['color'] == color_ml]
                # Exclude Dark Barrels during Premium Strategy
                if pricing_strategy == "PRICE_STRATEGY_PREMIUM" and color_ml == 'dark_ml':
                    possible_barrels = []

                # Sort barrels by efficiency (ml per gold)
                possible_barrels.sort(key=lambda x: barrel_prices[x]['ml'] / barrel_prices[x]['price'], reverse=True)
                for barrel_sku in possible_barrels:
                    barrel = barrel_prices[barrel_sku]
                    if gold - total_cost >= barrel['price']:
                        # Check capacity limit
                        if total_ml_after_purchase[color_ml] + barrel['ml'] <= ml_capacity_limit:
                            purchase_plan.append({'sku': barrel_sku, 'quantity': 1})
                            total_cost += barrel['price']
                            total_ml_after_purchase[color_ml] += barrel['ml']
                            ml_shortfall -= barrel['ml']
                            logger.info(f"Added {barrel_sku} to purchase plan")
                            break
                else:
                    # Cannot afford any more barrels or capacity reached
                    break

        logger.info(f"Final barrel purchase plan: {purchase_plan}")
        return purchase_plan


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