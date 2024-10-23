import logging
import math
from src import potion_config as pc
from typing import Tuple
from typing import List, Dict

logger = logging.getLogger(__name__)

class Utilities:
    @staticmethod
    def get_future_in_game_time(
        current_in_game_day: str,
        current_in_game_hour: int,
        ticks_ahead: int
    ) -> Tuple[str, int]:
        """
        Calculate future in-game time after certain number of ticks.
        """
        try:
            # Validate current_in_game_day
            if current_in_game_day not in pc.IN_GAME_DAYS:
                logger.error(f"Invalid in-game day: {current_in_game_day}")
                raise ValueError(f"Invalid in-game day: {current_in_game_day}")

            # Validate in_game_hour
            hours_in_day = pc.DAYS_AND_HOURS[current_in_game_day]
            if current_in_game_hour not in hours_in_day:
                logger.error(f"Invalid in-game hour: {current_in_game_hour} for day {current_in_game_day}")
                raise ValueError(f"Invalid in-game hour: {current_in_game_hour} for day {current_in_game_day}")

            # Get indices for day and hour
            day_index = pc.IN_GAME_DAYS.index(current_in_game_day)
            hour_index = hours_in_day.index(current_in_game_hour)

            # Calculate total ticks, current tick, and future tick number
            ticks_per_day = len(hours_in_day)
            total_ticks = len(pc.IN_GAME_DAYS) * ticks_per_day
            current_tick_number = day_index * ticks_per_day + hour_index
            future_tick_number = (current_tick_number + ticks_ahead) % total_ticks

            # Determine future day and hour indices
            future_day_index = future_tick_number // ticks_per_day
            future_hour_index = future_tick_number % ticks_per_day

            # Get future day and hour
            future_day = pc.IN_GAME_DAYS[future_day_index]
            future_hour = pc.DAYS_AND_HOURS[future_day][future_hour_index]
        
        except Exception as e:
            logger.exception(f"Exception in get_current_in_game_time: {e}")
            raise

        return future_day, future_hour
    

    @staticmethod
    def normalize_potion_type(potion_type: List[int]) -> List[int]:
        """
        Normalizes potion_type to sum to 100.
        """
        try:
            total = sum(potion_type)
            if total == 0:
                logger.error("Total of potion_type cannot be zero.")
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
        except Exception as e:
            logger.exception(f"Exception in normalize_potion_type: {e}")
            raise
    

    @staticmethod
    def get_color_from_potion_type(potion_type: List[int]) -> str:
        """
        Returns color_ml string based on potion_type.
        """
        try:
            colors = ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']
            for idx, val in enumerate(potion_type):
                if val == 1:
                    color = colors[idx]
                    logger.debug(f"Potion type {potion_type} corresponds to color {color}")
                    return colors[idx]
            logger.error(f"Invalid potion_type in barrel: {potion_type}")
            raise ValueError("Invalid potion_type in barrel.")
        except Exception as e:
            logger.exception(f"Exception in get_color_from_potion_type: {e}")
            raise


    @staticmethod
    def get_potion_details(sku: str) -> Dict:
        """
        Returns potion details based on SKU.
        """
        potion = pc.POTION_DEFINITIONS.get(sku)
        if potion is None:
            logger.debug(f"Potion details for SKU {sku} not found in POTION_DEFINITIONS")
            return {}
        return potion


class PotionShopLogic:
    @staticmethod
    def determine_pricing_strategy(
        gold: int,
        ml_capacity_units: int,
        potion_capacity_units: int
    ) -> str:
        """
        Determine current pricing strategy based on gold, ml capacity units, and potion capacity units.
        Returns one of pricing strategy strings.
        """
        logger.info(f"Determining pricing strategy with gold={gold}, ml_capacity_units={ml_capacity_units}, potion_capacity_units={potion_capacity_units}")
        try:
            if ml_capacity_units == 1 and potion_capacity_units == 1 and gold < 250:
                strategy = 'PRICE_STRATEGY_SKIMMING'
            elif ml_capacity_units == 1 and potion_capacity_units == 1:
                strategy = 'PRICE_STRATEGY_BALANCED'
            elif ml_capacity_units <= 2 and potion_capacity_units <= 1:
                strategy = 'PRICE_STRATEGY_PENETRATION'
            elif ml_capacity_units <= 3 and potion_capacity_units <= 2:
                strategy = 'PRICE_STRATEGY_TIERED'
            elif ml_capacity_units <= 4 and potion_capacity_units <= 3:
                strategy = 'PRICE_STRATEGY_DYNAMIC'
            elif ml_capacity_units >= 5 and potion_capacity_units >= 4:
                strategy = 'PRICE_STRATEGY_MAXIMIZING'
            else:
                logger.error(f"Invalid capacity units: ml_capacity_units={ml_capacity_units}, potion_capacity_units={potion_capacity_units}")
                strategy = 'PRICE_STRATEGY_SKIMMING'  # Default strategy
            logger.info(f"Determined pricing strategy: {strategy}")
            return strategy
        except Exception as e:
            logger.exception(f"Exception in determine_pricing_strategy: {e}")
            raise


    @staticmethod
    def get_potion_priorities(
        current_day: str,
        current_strategy: str,
        potion_priorities: dict
    ) -> List[Dict]:
        """
        Retrieve potion priorities for given day and strategy.
        """
        logger.info(f"Retrieving potion priorities for day={current_day} and strategy={current_strategy}")
        try:
            if current_day not in potion_priorities:
                logger.error(f"Invalid day: {current_day}")
                raise ValueError(f"Invalid day: {current_day}")
            day_priorities = potion_priorities[current_day]
            if current_strategy not in day_priorities:
                logger.error(f"Strategy {current_strategy} not available for day {current_day}")
                raise ValueError(f"Strategy {current_strategy} not available for day {current_day}")
            strategy_priorities = day_priorities[current_strategy]
            logger.debug(f"Potion priorities: {strategy_priorities}")
            return strategy_priorities
        except Exception as e:
            logger.exception(f"Exception in get_potion_priorities: {e}")
            raise


    @staticmethod
    def calculate_potion_bottling_plan(
        current_strategy: str,
        potion_priorities: List[Dict],
        potion_inventory: Dict[str, int],
        potion_capacity_units: int,
        ml_inventory: Dict[str, int],
        ml_capacity_units: int,
        gold: int,
        adjust_for_ml_inventory: bool = True
    ) -> Dict[str, int]:
        """
        Calculate how many of each potion to bottle for upcoming tick.
        Returns dict mapping SKU to number of potions to bottle.
        """
        logger.info(f"Calculating potion bottling plan for strategy {current_strategy}")
        logger.debug(f"Potion priorities: {potion_priorities}")
        logger.debug(f"Potion inventory: {potion_inventory}")
        logger.debug(f"ML inventory: {ml_inventory}")
        logger.debug(f"Potion capacity units: {potion_capacity_units}")
        logger.debug(f"ML capacity units: {ml_capacity_units}")
        logger.debug(f"Gold: {gold}")
        logger.debug(f"Adjust for ml_inventory: {adjust_for_ml_inventory}")

        try:
            bottling_params = pc.BOTTLING_PARAMETERS[current_strategy]
            max_potions_per_sku = bottling_params['max_potions_per_sku']
            bottling_ceiling = bottling_params['bottling_ceiling']
            bottling_base = bottling_params['bottling_base']

            # Calculate total capacities
            total_potion_capacity = potion_capacity_units * pc.POTION_CAPACITY_PER_UNIT
            total_ml_capacity = ml_capacity_units * pc.ML_CAPACITY_PER_UNIT
            logger.debug(f"Total potion capacity: {total_potion_capacity}")
            logger.debug(f"Total ml capacity: {total_ml_capacity}")

            # Total potions in inventory
            total_potions_in_inventory = sum(potion_inventory.values())
            logger.debug(f"Total potions in inventory: {total_potions_in_inventory}")

            # Determine vacant potion slots
            priority_skus = [p['sku'] for p in potion_priorities]
            potions_not_in_priorities = {sku: qty for sku, qty in potion_inventory.items() if sku not in priority_skus}
            total_potions_not_in_priorities = sum(potions_not_in_priorities.values())
            logger.debug(f"Potions not in priorities: {potions_not_in_priorities}")
            logger.debug(f"Total potions not in priorities: {total_potions_not_in_priorities}")

            vacant_potion_slots = total_potion_capacity - total_potions_not_in_priorities
            if vacant_potion_slots < 0:
                vacant_potion_slots = 0
            logger.debug(f"Vacant potion slots: {vacant_potion_slots}")

            # Prepare potion definitions mapping
            potion_ml_requirements = {}
            for potion_def in pc.DEFAULT_POTIONS:
                sku = potion_def['sku']
                potion_ml_requirements[sku] = {
                    'red_ml': potion_def.get('red_ml', 0),
                    'green_ml': potion_def.get('green_ml', 0),
                    'blue_ml': potion_def.get('blue_ml', 0),
                    'dark_ml': potion_def.get('dark_ml', 0),
                }

            # Calculate desired quantities based on sales_mix
            potion_plans = []
            total_needed_potions = 0
            for index, potion in enumerate(potion_priorities):
                sku = potion['sku']
                sales_mix = potion['sales_mix']
                desired_quantity = int(sales_mix * vacant_potion_slots)
                existing_quantity = potion_inventory.get(sku, 0)
                needed_quantity = desired_quantity - existing_quantity
                if needed_quantity < 0:
                    needed_quantity = 0
                potion_plans.append({
                    'sku': sku,
                    'needed_quantity': needed_quantity,
                    'sales_mix': sales_mix,
                    'priority': index,
                    'composition': potion['composition'],
                    'existing_quantity': existing_quantity,
                    'adjusted_quantity': 0  # Will be updated after adjustments
                })
                total_needed_potions += needed_quantity
                logger.debug(f"Potion {sku}: desired_quantity={desired_quantity}, existing_quantity={existing_quantity}, needed_quantity={needed_quantity}")

            # Adjust quantities based on bottling_base
            for potion in potion_plans:
                needed_quantity = potion['needed_quantity']
                if needed_quantity < bottling_base:
                    adjusted_quantity = 0
                else:
                    adjusted_quantity = (needed_quantity // bottling_base) * bottling_base
                # Ensure not to exceed bottling_ceiling per SKU
                adjusted_quantity = min(adjusted_quantity, bottling_ceiling)
                potion['adjusted_quantity'] = adjusted_quantity
                logger.debug(f"Potion {potion['sku']}: Adjusted needed quantity from {needed_quantity} to {adjusted_quantity}")

            # If adjust_for_ml_inventory is False, skip ml_inventory adjustments
            if not adjust_for_ml_inventory:
                logger.debug("Skipping ml_inventory adjustments as per adjust_for_ml_inventory=False")
                # Prepare final bottling plan without adjusting for ml_inventory
                bottling_plan = {potion['sku']: potion['adjusted_quantity'] for potion in potion_plans if potion['adjusted_quantity'] > 0}
                logger.info(f"Bottling plan (without ml adjustments): {bottling_plan}")
                return bottling_plan

            # Proceed with ml_inventory adjustments as before
            # Calculate total ml needed per color using POTION_DEFINITIONS
            ml_needed = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            for potion in potion_plans:
                sku = potion['sku']
                adjusted_quantity = potion['adjusted_quantity']
                potion_def = pc.POTION_DEFINITIONS[sku]
                for color in ['dark_ml', 'red_ml', 'green_ml', 'blue_ml']:
                    ml_needed[color] += adjusted_quantity * potion_def.get(color, 0)

            logger.debug(f"Total ml needed per color before adjustments: {ml_needed}")

            # Check ml inventory and adjust quantities if necessary
            color_potion_usage = {'red_ml': [], 'green_ml': [], 'blue_ml': [], 'dark_ml': []}
            for potion in potion_plans:
                sku = potion['sku']
                composition = potion['composition']  # [red, green, blue, dark]
                for idx, color in enumerate(['red_ml', 'green_ml', 'blue_ml', 'dark_ml']):
                    if composition[idx] > 0:
                        color_potion_usage[color].append(potion)

            for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']:
                ml_needed_color = ml_needed[color]
                ml_available = ml_inventory.get(color, 0)
                if ml_needed_color <= ml_available:
                    continue
                else:
                    ml_shortfall = ml_needed_color - ml_available
                    logger.warning(f"Insufficient {color}: needed {ml_needed_color}, available {ml_available}, shortfall {ml_shortfall}")
                    # Potions that use this color
                    potions_using_color = color_potion_usage[color]
                    # Sort potions by lower priority (higher index), lower sales_mix
                    potions_using_color.sort(key=lambda x: (x['priority'], -x['sales_mix']))
                    # Adjust quantities
                    for potion in potions_using_color:
                        sku = potion['sku']
                        adjusted_quantity = potion['adjusted_quantity']
                        if adjusted_quantity == 0:
                            continue
                        ml_per_potion_color = potion_ml_requirements[sku][color]
                        total_ml_for_potion_color = adjusted_quantity * ml_per_potion_color
                        # Determine how many potions to reduce
                        ml_to_reduce = min(total_ml_for_potion_color, ml_shortfall)
                        potions_to_reduce = int((ml_to_reduce + ml_per_potion_color - 1) // ml_per_potion_color)  # Round up
                        if potions_to_reduce > adjusted_quantity:
                            potions_to_reduce = adjusted_quantity
                        adjusted_quantity_new = adjusted_quantity - potions_to_reduce
                        potion['adjusted_quantity'] = adjusted_quantity_new
                        logger.debug(f"Adjusted {sku} adjusted_quantity from {adjusted_quantity} to {adjusted_quantity_new} due to insufficient {color}")
                        # Update ml_needed
                        ml_needed[color] -= (adjusted_quantity - adjusted_quantity_new) * ml_per_potion_color
                        ml_shortfall -= (adjusted_quantity - adjusted_quantity_new) * ml_per_potion_color
                        if ml_shortfall <= 0:
                            break

            # Recalculate total adjusted quantity
            total_adjusted_quantity = sum(potion['adjusted_quantity'] for potion in potion_plans)
            logger.debug(f"Total adjusted quantity after ml adjustments: {total_adjusted_quantity}")

            # Check if total adjusted quantity exceeds vacant potion slots
            if total_adjusted_quantity > vacant_potion_slots:
                logger.warning(f"Total adjusted quantity {total_adjusted_quantity} exceeds vacant potion slots {vacant_potion_slots}")
                excess_potions = total_adjusted_quantity - vacant_potion_slots
                # Sort potions by lower priority (higher index), lower sales_mix
                potion_plans.sort(key=lambda x: (x['priority'], -x['sales_mix']))
                for potion in potion_plans:
                    adjusted_quantity = potion['adjusted_quantity']
                    if adjusted_quantity == 0:
                        continue
                    # Reduce adjusted_quantity
                    potions_to_reduce = min(adjusted_quantity, excess_potions)
                    adjusted_quantity_new = adjusted_quantity - potions_to_reduce
                    potion['adjusted_quantity'] = adjusted_quantity_new
                    logger.debug(f"Adjusted {potion['sku']} adjusted_quantity from {adjusted_quantity} to {adjusted_quantity_new} due to potion capacity limit")
                    excess_potions -= (adjusted_quantity - adjusted_quantity_new)
                    if excess_potions <= 0:
                        break

            # Prepare final bottling plan
            bottling_plan = {potion['sku']: potion['adjusted_quantity'] for potion in potion_plans if potion['adjusted_quantity'] > 0}

            logger.info(f"Bottling plan: {bottling_plan}")
            return bottling_plan

        except Exception as e:
            logger.exception(f"Exception in calculate_potion_bottling_plan: {e}")
            raise


    @staticmethod
    def decide_barrels_to_purchase(
        current_strategy: str,
        potion_priorities: List[Dict],
        ml_inventory: Dict[str, int],
        ml_capacity_units: int,
        gold: int,
        future_potion_needs: Dict[str, int],
        wholesale_catalog: List[Dict]
    ) -> List[Dict]:
        """
        Decide which barrels to purchase.
        Returns list of barrel purchase orders, each with SKU and quantity.
        """
        logger.info(f"Deciding barrels to purchase with strategy={current_strategy}, gold={gold}, ml_capacity_units={ml_capacity_units}")
        logger.debug(f"Potion priorities: {potion_priorities}")
        logger.debug(f"ML inventory: {ml_inventory}")
        logger.debug(f"Future potion needs: {future_potion_needs}")
        logger.debug(f"Wholesale catalog: {wholesale_catalog}")

        try:
            barrel_purchase_orders = []
            total_ml_capacity = ml_capacity_units * pc.ML_CAPACITY_PER_UNIT
            available_ml_capacity = total_ml_capacity - sum(ml_inventory.values())

            # Calculate total ml needed per color
            ml_needed = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
            for sku, qty in future_potion_needs.items():
                potion_def = pc.POTION_DEFINITIONS[sku]
                for color in ['dark_ml', 'red_ml', 'green_ml', 'blue_ml']:
                    ml_needed[color] += potion_def.get(color, 0) * qty
            # Scale up by 2.5x
            for color in ml_needed:
                ml_needed[color] = int(ml_needed[color] * 2.5)
                ml_needed[color] -= ml_inventory.get(color, 0)
                if ml_needed[color] < 0:
                    ml_needed[color] = 0

            logger.debug(f"ML needed per color after scaling: {ml_needed}")

            # Prepare barrel information
            barrel_info = {}
            for barrel in wholesale_catalog:
                color = Utilities.get_color_from_potion_type(barrel['potion_type'])
                barrel_info.setdefault(color, []).append({
                    'sku': barrel['sku'],
                    'ml_per_barrel': barrel['ml_per_barrel'],
                    'price': barrel['price'],
                    'quantity': barrel['quantity']
                })

            # Process each color
            for color in ['dark_ml', 'red_ml', 'green_ml', 'blue_ml']:
                ml_needed_for_color = ml_needed[color]
                if ml_needed_for_color <= 0:
                    continue

                if color not in barrel_info:
                    logger.warning(f"No barrels available for color {color}")
                    continue

                # Sort barrels by size descending
                barrels = sorted(barrel_info[color], key=lambda x: x['ml_per_barrel'], reverse=True)
                for barrel in barrels:
                    if gold <= 0 or available_ml_capacity <= 0 or ml_needed_for_color <= 0:
                        break

                    needed_barrels = math.ceil(ml_needed_for_color / barrel['ml_per_barrel'])

                    max_barrels = min(
                        barrel['quantity'],
                        needed_barrels,
                        gold // barrel['price'],
                        available_ml_capacity // barrel['ml_per_barrel']
                    )

                    if max_barrels <= 0:
                        continue

                    total_price = max_barrels * barrel['price']
                    if total_price > gold:
                        max_barrels = gold // barrel['price']
                        total_price = max_barrels * barrel['price']

                    if max_barrels <= 0:
                        continue

                    # Update purchase orders
                    barrel_purchase_orders.append({'sku': barrel['sku'], 'quantity': max_barrels})
                    logger.info(f"Added {max_barrels} of {barrel['sku']} to purchase orders for color {color}")

                    # Update counters
                    gold -= total_price
                    available_ml_capacity -= max_barrels * barrel['ml_per_barrel']
                    ml_needed_for_color -= max_barrels * barrel['ml_per_barrel']
                    barrel['quantity'] -= max_barrels

            return barrel_purchase_orders

        except Exception as e:
            logger.exception(f"Exception in decide_barrels_to_purchase: {e}")
            raise


    @staticmethod
    def should_purchase_capacity_upgrade(
        current_strategy: str,
        gold: int,
        potion_inventory: Dict[str, int],
        ml_inventory: Dict[str, int],
        ml_capacity_units: int,
        potion_capacity_units: int
    ) -> Dict[str, int]:
        """
        Determine if capacity upgrades are needed.
        Returns dict with 'ml_capacity_units' and 'potion_capacity_units' to purchase.
        """
        logger.info("Starting should_purchase_capacity_upgrade")
        logger.debug(f"Inputs - Strategy: {current_strategy}, Gold: {gold}, Potion Inventory: {potion_inventory}, "
                     f"ML Inventory: {ml_inventory}, ML Capacity Units: {ml_capacity_units}, "
                     f"Potion Capacity Units: {potion_capacity_units}")

        # Initialize return dict
        capacity_to_purchase = {'ml_capacity': 0, 'potion_capacity': 0}

        try:
            # Get purchase parameters for current strategy
            purchase_params = pc.CAPACITY_PURCHASE_PARAMETERS[current_strategy]
            purchase_conditions = purchase_params.get('purchase_conditions', [])
            logger.debug(f"Purchase conditions for strategy {current_strategy}: {purchase_conditions}")

            # Total potions and ml in inventory
            total_potions_in_inventory = sum(potion_inventory.values())
            logger.debug(f"Total potions in inventory: {total_potions_in_inventory}")
            total_ml_in_inventory = sum(ml_inventory.values())
            logger.debug(f"Total ml in inventory: {total_ml_in_inventory}")

            # Calculate potion and ml capacity limit
            potion_capacity_limit = potion_capacity_units * pc.POTION_CAPACITY_PER_UNIT
            logger.debug(f"Potion capacity limit: {potion_capacity_limit}")
            ml_capacity_limit = ml_capacity_units * pc.ML_CAPACITY_PER_UNIT
            logger.debug(f"ML capacity limit: {ml_capacity_limit}")

            # Evaluate each purchase condition
            for condition in purchase_conditions:
                condition_met = True
                logger.debug(f"Evaluating condition: {condition}")

                # Check gold threshold
                gold_threshold = condition.get('gold_threshold', 0)
                if gold < gold_threshold:
                    logger.debug(f"Condition not met: gold {gold} is less than gold threshold {gold_threshold}")
                    condition_met = False

                # Check potions in inventory threshold
                potions_in_inventory_threshold = condition.get('potions_in_inventory', None)
                if potions_in_inventory_threshold is not None:
                    if total_potions_in_inventory < potions_in_inventory_threshold:
                        logger.debug(f"Condition not met: potions in inventory {total_potions_in_inventory} "
                                     f"is less than threshold {potions_in_inventory_threshold}")
                        condition_met = False

                # Check ml inventory threshold
                ml_inventory_threshold = condition.get('ml_inventory_threshold', None)
                if ml_inventory_threshold is not None:
                    if total_ml_in_inventory < ml_inventory_threshold:
                        logger.debug(f"Condition not met: ml inventory {total_ml_in_inventory} "
                                     f"is less than threshold {ml_inventory_threshold}")
                        condition_met = False

                # Check potions in inventory percentage
                potions_inventory_percentage = condition.get('potions_inventory_percentage', None)
                if potions_inventory_percentage is not None:
                    potions_percentage = (total_potions_in_inventory / potion_capacity_limit) * 100
                    if potions_percentage < potions_inventory_percentage:
                        logger.debug(f"Condition not met: potions inventory percentage {potions_percentage}% "
                                     f"is less than threshold {potions_inventory_percentage}%")
                        condition_met = False

                # Check ml inventory percentage
                ml_inventory_percentage = condition.get('ml_inventory_percentage', None)
                if ml_inventory_percentage is not None:
                    ml_percentage = (total_ml_in_inventory / ml_capacity_limit) * 100
                    if ml_percentage < ml_inventory_percentage:
                        logger.debug(f"Condition not met: ml inventory percentage {ml_percentage}% "
                                     f"is less than threshold {ml_inventory_percentage}%")
                        condition_met = False

                if condition_met:
                    # Decide on capacity units to purchase
                    capacity_to_purchase['ml_capacity'] += condition.get('ml_units_to_purchase', 0)
                    capacity_to_purchase['potion_capacity'] += condition.get('potion_units_to_purchase', 0)
                    logger.info(f"Condition met: {condition}. Deciding to purchase capacity units: {capacity_to_purchase}")
                    # Since conditions are ordered, break after first condition met
                    break
                else:
                    logger.debug(f"Condition not met: {condition}")

            logger.info(f"Decided to purchase capacity units: {capacity_to_purchase}")
            logger.debug(f"Output - Capacity to purchase: {capacity_to_purchase}")
            return capacity_to_purchase

        except Exception as e:
            logger.exception(f"Exception in should_purchase_capacity_upgrade: {e}")
            raise


    @staticmethod
    def update_catalog(
        potion_priorities: List[Dict],
        potion_inventory: Dict[str, int],
        max_catalog_size: int = 6
    ) -> List[Dict]:
        """
        Update catalog with potions to sell.
        Returns list of potions to include in catalog.
        """
        logger.info("Starting update_catalog")
        logger.debug(f"Potion priorities: {potion_priorities}")
        logger.debug(f"Potion inventory: {potion_inventory}")
        logger.debug(f"Max catalog size: {max_catalog_size}")

        try:
            catalog = []
            included_skus = set()
            
            # Include potions from potion_priorities if they are in inventory
            for potion in potion_priorities:
                sku = potion.get('sku')
                quantity = potion_inventory.get(sku, 0)
                if quantity > 0:
                    catalog.append({
                        'sku': sku,
                        'composition': potion.get('composition'),
                        'price': potion.get('price'),
                        'sales_mix': potion.get('sales_mix'),
                        'quantity': quantity
                    })
                    included_skus.add(sku)
                    logger.debug(f"Added {sku} to catalog from priorities")
                else:
                    logger.debug(f"Skipped {sku} from priorities due to zero quantity")
            
            # Fill remaining slots with potions not in potion_priorities
            if len(catalog) < max_catalog_size:
                # Get potions not in potion_priorities and sort by quantity
                remaining_potions = [
                    {'sku': sku, 'quantity': qty}
                    for sku, qty in potion_inventory.items()
                    if sku not in included_skus and qty > 0
                ]
                remaining_potions.sort(key=lambda x: x['quantity'], reverse=True)
                
                for remaining_potion in remaining_potions:
                    if len(catalog) >= max_catalog_size:
                        break
                    sku = remaining_potion['sku']
                    quantity = remaining_potion['quantity']

                    default_potion = Utilities.get_potion_details(sku)
                    if default_potion:
                        catalog.append({
                            'sku': sku,
                            'composition': [
                                default_potion['red_ml'],
                                default_potion['green_ml'],
                                default_potion['blue_ml'],
                                default_potion['dark_ml']
                            ],
                            'price': default_potion['price'],
                            'sales_mix': 0,
                            'quantity': quantity
                        })
                        included_skus.add(sku)
                        logger.debug(f"Added {sku} to catalog from inventory")

            logger.info("Catalog update completed successfully")
            logger.debug(f"Final catalog: {catalog}")
            return catalog

        except Exception as e:
            logger.exception(f"Exception in update_catalog: {e}")
            raise


    @staticmethod
    def perform_bottling(
        bottling_plan: Dict[str, int],
        ml_inventory: Dict[str, int],
        potion_inventory: Dict[str, int],
        ml_capacity_units: int,
        potion_capacity_units: int,
        potion_definitions: Dict[str, Dict]
    ) -> Tuple[Dict[str, int], Dict[str, int]]:
        """
        Perform bottling according to plan.
        Updates ml inventory and potion inventory.
        Returns updated ml_inventory and potion_inventory.
        """
        logger.info("Starting perform_bottling")
        logger.debug(f"Bottling plan: {bottling_plan}")
        logger.debug(f"Initial ml_inventory: {ml_inventory}")
        logger.debug(f"Initial potion_inventory: {potion_inventory}")
        logger.debug(f"ML capacity units: {ml_capacity_units}")
        logger.debug(f"Potion capacity units: {potion_capacity_units}")
        
        try:
            # Calculate total capacities
            total_potion_capacity = potion_capacity_units * pc.POTION_CAPACITY_PER_UNIT
            total_ml_capacity = ml_capacity_units * pc.ML_CAPACITY_PER_UNIT
            logger.debug(f"Total potion capacity: {total_potion_capacity}")
            logger.debug(f"Total ml capacity: {total_ml_capacity}")
            
            # Calculate current capacities used
            current_potion_count = sum(potion_inventory.values())
            current_ml_used = sum(ml_inventory.values())
            logger.debug(f"Current potion count: {current_potion_count}")
            logger.debug(f"Current ml used: {current_ml_used}")
            
            # Check for capacity overflows
            if current_potion_count > total_potion_capacity:
                logger.warning("Current potion inventory exceeds total potion capacity!")
                # Adjust potion inventory to capacity limit
                excess_potions = current_potion_count - total_potion_capacity
                logger.debug(f"Excess potions to remove: {excess_potions}")
                # Logic to remove excess potions if necessary
                
            if current_ml_used > total_ml_capacity:
                logger.warning("Current ml inventory exceeds total ml capacity!")
                # Adjust ml inventory to capacity limit
                excess_ml = current_ml_used - total_ml_capacity
                logger.debug(f"Excess ml to remove: {excess_ml}")
                # Logic to remove excess ml if necessary
            
            # Perform bottling
            for sku, quantity_to_bottle in bottling_plan.items():
                logger.debug(f"Bottling {quantity_to_bottle} units of {sku}")
                potion_def = pc.POTION_DEFINITIONS.get(sku)
                if not potion_def:
                    logger.error(f"Potion definition for {sku} not found!")
                    continue  # Skip if potion definition is missing

                # Calculate total ml required for this potion
                total_red_ml_needed = potion_def.get('red_ml', 0) * quantity_to_bottle
                total_green_ml_needed = potion_def.get('green_ml', 0) * quantity_to_bottle
                total_blue_ml_needed = potion_def.get('blue_ml', 0) * quantity_to_bottle
                total_dark_ml_needed = potion_def.get('dark_ml', 0) * quantity_to_bottle
                
                # Check if enough ml is available
                ml_shortage = False
                for color_ml_needed, color in [
                    (total_red_ml_needed, 'red_ml'),
                    (total_green_ml_needed, 'green_ml'),
                    (total_blue_ml_needed, 'blue_ml'),
                    (total_dark_ml_needed, 'dark_ml'),
                ]:
                    ml_available = ml_inventory.get(color, 0)
                    if ml_available < color_ml_needed:
                        logger.error(f"Not enough {color} to bottle {sku}. Needed: {color_ml_needed}, Available: {ml_available}")
                        ml_shortage = True
                        break  # Stop processing this potion due to ml shortage
                if ml_shortage:
                    continue  # Move to next potion in plan
                
                # Update ml_inventory by deducting used ml
                ml_inventory['red_ml'] = ml_inventory.get('red_ml', 0) - total_red_ml_needed
                ml_inventory['green_ml'] = ml_inventory.get('green_ml', 0) - total_green_ml_needed
                ml_inventory['blue_ml'] = ml_inventory.get('blue_ml', 0) - total_blue_ml_needed
                ml_inventory['dark_ml'] = ml_inventory.get('dark_ml', 0) - total_dark_ml_needed
                
                logger.debug(f"Updated ml_inventory after bottling {sku}: {ml_inventory}")
                
                # Update potion_inventory by adding bottled potions
                potion_inventory[sku] = potion_inventory.get(sku, 0) + quantity_to_bottle
                logger.debug(f"Updated potion_inventory after bottling {sku}: {potion_inventory}")
                
                # Update current capacities used
                current_potion_count += quantity_to_bottle
                current_ml_used -= (total_red_ml_needed + total_green_ml_needed + total_blue_ml_needed + total_dark_ml_needed)
                
                # Check for capacity overflows after bottling
                if current_potion_count > total_potion_capacity:
                    logger.error(f"Potion capacity exceeded after bottling {sku}. Aborting bottling process.")
                    raise Exception("Potion capacity exceeded.")
                if current_ml_used < 0:
                    logger.error(f"ML inventory negative after bottling {sku}. Aborting bottling process.")
                    raise Exception("ML inventory negative.")
            
            logger.info("Bottling process completed successfully.")
            logger.debug(f"Final ml_inventory: {ml_inventory}")
            logger.debug(f"Final potion_inventory: {potion_inventory}")
            return ml_inventory, potion_inventory
        
        except Exception as e:
            logger.exception(f"Exception in perform_bottling: {e}")
            raise
        
    
    @staticmethod
    def calculate_ml_needed_for_bottling_plan(
        bottling_plan: Dict[str, int],
        potion_definitions: Dict[str, Dict]
    ) -> Dict[str, int]:
        """
        Calculate total ml of each color needed for bottling plan.
        Returns dict mapping color to ml needed.
        """
        logger.info(f"Calculating ml needed for bottling plan: {bottling_plan}")
        ml_needed = {'red_ml': 0, 'green_ml': 0, 'blue_ml': 0, 'dark_ml': 0}
        try:
            for sku, quantity in bottling_plan.items():
                potion_def = pc.POTION_DEFINITIONS.get(sku)
                if not potion_def:
                    logger.error(f"Potion definition for SKU {sku} not found.")
                    continue

                logger.debug(f"Calculating ml needed for SKU {sku}, quantity {quantity}")
                for color in ['red_ml', 'green_ml', 'blue_ml', 'dark_ml']:
                    ml_needed[color] += potion_def.get(color, 0) * quantity

            logger.info(f"Total ml needed: {ml_needed}")
            return ml_needed
        except Exception as e:
            logger.exception(f"Exception in calculate_ml_needed_for_bottling_plan: {e}")
            raise