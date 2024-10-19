from typing import List, Dict


# Constants for capacity calculations
POTION_CAPACITY_PER_UNIT = 50       # Each potion capacity unit allows storage of 50 potions
ML_CAPACITY_PER_UNIT = 10000        # Each ML capacity unit allows storage of 10000 ml
CAPACITY_UNIT_COST = 1000           # Cost per capacity unit in gold

# Define days of week in Potion Exchange world
IN_GAME_DAYS = [
    "Hearthday",
    "Crownday",
    "Blesseday",
    "Soulday",
    "Edgeday",
    "Bloomday",
    "Aracanaday"
]

# Define in-game hours for each day (ticks every 2 hours)
DAYS_AND_HOURS: Dict[str, List[int]] = {
    "Hearthday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
    "Crownday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
    "Blesseday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
    "Soulday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
    "Edgeday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
    "Bloomday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22],
    "Aracanaday": [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
}


STRATEGY_PARAMETERS = {
    'PRICE_STRATEGY_SKIMMING': {
        'barrel_sizes': ['SMALL'],
        'allowed_barrels': ['SMALL_RED_BARREL', 'SMALL_GREEN_BARREL', 'SMALL_BLUE_BARREL'],
        'gold_threshold': 320,
        'ml_capacity_units': 1,
        'potion_capacity_units': 1,
        'offset_amount': 1,
        'ml_interval': 500,
    },
        'PRICE_STRATEGY_BALANCED': {
        'barrel_sizes': ['MEDIUM', 'SMALL'],
        'allowed_barrels': [
            'LARGE_DARK_BARREL', 'MEDIUM_RED_BARREL', 'SMALL_RED_BARREL',
            'MEDIUM_GREEN_BARREL', 'SMALL_GREEN_BARREL', 'MEDIUM_BLUE_BARREL', 'SMALL_BLUE_BARREL'
        ],
        'gold_threshold': 1070,
        'ml_capacity_units': 1,
        'potion_capacity_units': 1,
        'offset_amount': 1,
        'ml_interval': 1000,
    },
    'PRICE_STRATEGY_PENETRATION': {
        'barrel_sizes': ['MEDIUM', 'SMALL'],
        'allowed_barrels': [
            'LARGE_DARK_BARREL', 'MEDIUM_RED_BARREL', 'SMALL_RED_BARREL',
            'MEDIUM_GREEN_BARREL', 'SMALL_GREEN_BARREL', 'MEDIUM_BLUE_BARREL', 'SMALL_BLUE_BARREL'
        ],
        'gold_threshold': 1070,
        'ml_capacity_units': 2,
        'potion_capacity_units': 1,
        'offset_amount': 1,
        'ml_interval': 1000,
    },
    'PRICE_STRATEGY_TIERED': {
        'barrel_sizes': ['LARGE', 'MEDIUM'],
        'allowed_barrels': [
            'LARGE_DARK_BARREL', 'LARGE_RED_BARREL', 'MEDIUM_RED_BARREL',
            'LARGE_GREEN_BARREL', 'MEDIUM_GREEN_BARREL', 'LARGE_BLUE_BARREL', 'MEDIUM_BLUE_BARREL'
        ],
        'gold_threshold': 1850,
        'ml_capacity_units': 3,
        'potion_capacity_units': 2,
        'offset_amount': 1,
        'ml_interval': 2500,
    },
    'PRICE_STRATEGY_MAXIMIZING': {
        'barrel_sizes': ['LARGE', 'MEDIUM'],
        'allowed_barrels': [
            'LARGE_DARK_BARREL', 'LARGE_RED_BARREL', 'MEDIUM_RED_BARREL',
            'LARGE_GREEN_BARREL', 'MEDIUM_GREEN_BARREL', 'LARGE_BLUE_BARREL', 'MEDIUM_BLUE_BARREL'
        ],
        'gold_threshold': 4500,
        'ml_capacity_units': 4,
        'potion_capacity_units': 3,
        'offset_amount': 1,
        'ml_interval': 10000,
    }
}


BARREL_PURCHASE_PARAMETERS = {
    'PRICE_STRATEGY_SKIMMING': {
        'ml_capacity_unit': 1,
        'potion_capacity_unit': 1,
        'gold_threshold': 320,
        'preferred_barrels': ['SMALL_RED_BARREL', 'SMALL_GREEN_BARREL', 'SMALL_BLUE_BARREL'],
        'offset_amount': 1,
        'ml_interval': 500,
        'purchase_priority': ['BLUE_POTION', 'RED_POTION', 'GREEN_POTION'],
    },
        'PRICE_STRATEGY_BALANCED': {
        'ml_capacity_unit': 1,
        'potion_capacity_unit': 1,
        'gold_threshold': 1070,
        'preferred_barrels': [
            'LARGE_DARK_BARREL', 'MEDIUM_RED_BARREL', 'SMALL_RED_BARREL',
            'MEDIUM_GREEN_BARREL', 'SMALL_GREEN_BARREL', 'MEDIUM_BLUE_BARREL', 'SMALL_BLUE_BARREL'
        ],
        'offset_amount': 1,
        'ml_interval': 1000,
        'purchase_priority': ['BLUE_POTION', 'RED_POTION', 'GREEN_POTION'],
    },
    'PRICE_STRATEGY_PENETRATION': {
        'ml_capacity_unit': 2,
        'potion_capacity_unit': 1,
        'gold_threshold': 1070,
        'preferred_barrels': [
            'LARGE_DARK_BARREL', 'MEDIUM_RED_BARREL', 'SMALL_RED_BARREL',
            'MEDIUM_GREEN_BARREL', 'SMALL_GREEN_BARREL', 'MEDIUM_BLUE_BARREL', 'SMALL_BLUE_BARREL'
        ],
        'offset_amount': 1,
        'ml_interval': 500,
        'purchase_priority': ['DARK_POTION', 'BLUE_POTION', 'RED_POTION', 'GREEN_POTION'],
    },
    'PRICE_STRATEGY_TIERED': {
        'ml_capacity_unit': 3,
        'potion_capacity_unit': 2,
        'gold_threshold': 1850,
        'preferred_barrels': [
            'LARGE_DARK_BARREL', 'LARGE_RED_BARREL', 'MEDIUM_RED_BARREL',
            'LARGE_GREEN_BARREL', 'MEDIUM_GREEN_BARREL',
            'LARGE_BLUE_BARREL', 'MEDIUM_BLUE_BARREL'
        ],
        'offset_amount': 1,
        'ml_interval': 2500,
        'purchase_priority': ['DARK_POTION', 'BLUE_POTION', 'RED_POTION', 'GREEN_POTION'],
    },
    'PRICE_STRATEGY_DYNAMIC': {
        'ml_capacity_unit': 4,
        'potion_capacity_unit': 3,
        'gold_threshold': 2250,
        'preferred_barrels': [
            'LARGE_DARK_BARREL', 'LARGE_RED_BARREL', 'MEDIUM_RED_BARREL',
            'LARGE_GREEN_BARREL', 'MEDIUM_GREEN_BARREL',
            'LARGE_BLUE_BARREL', 'MEDIUM_BLUE_BARREL'
        ],
        'offset_amount': 1,
        'ml_interval': 2500,
        'purchase_priority': ['DARK_POTION', 'PURPLE_POTION', 'TEAL_POTION', 'BLUE_POTION', 'RED_POTION', 'GREEN_POTION'],
    },
    'PRICE_STRATEGY_MAXIMIZING': {
        'ml_capacity_unit': 5,
        'potion_capacity_unit': 4,
        'gold_threshold': 4500,
        'preferred_barrels': [
            'LARGE_DARK_BARREL', 'LARGE_RED_BARREL', 'MEDIUM_RED_BARREL',
            'LARGE_GREEN_BARREL', 'MEDIUM_GREEN_BARREL',
            'LARGE_BLUE_BARREL', 'MEDIUM_BLUE_BARREL'
        ],
        'offset_amount': 1,
        'ml_interval': 2500,
        'purchase_priority': ['DARK_POTION', 'PURPLE_POTION', 'TEAL_POTION', 'YELLOW_POTION', 'BLUE_POTION', 'RED_POTION', 'GREEN_POTION'],
    },
}


BARREL_DEFINITIONS = {
    'SMALL_RED_BARREL': {
        'sku': 'SMALL_RED_BARREL',
        'size': 'SMALL',
        'color': 'RED',
        'ml_per_barrel': 500,
        'price': 100,
        'potion_type': [1, 0, 0, 0]
    },
    'MEDIUM_RED_BARREL': {
        'sku': 'MEDIUM_RED_BARREL',
        'size': 'MEDIUM',
        'color': 'RED',
        'ml_per_barrel': 2500,
        'price': 250,
        'potion_type': [1, 0, 0, 0]
    },
    'LARGE_RED_BARREL': {
        'sku': 'LARGE_RED_BARREL',
        'size': 'LARGE',
        'color': 'RED',
        'ml_per_barrel': 10000,
        'price': 500,
        'potion_type': [1, 0, 0, 0]
    },
    'SMALL_GREEN_BARREL': {
        'sku': 'SMALL_GREEN_BARREL',
        'size': 'SMALL',
        'color': 'GREEN',
        'ml_per_barrel': 500,
        'price': 100,
        'potion_type': [0, 1, 0, 0]
    },
    'MEDIUM_GREEN_BARREL': {
        'sku': 'MEDIUM_GREEN_BARREL',
        'size': 'MEDIUM',
        'color': 'GREEN',
        'ml_per_barrel': 2500,
        'price': 250,
        'potion_type': [0, 1, 0, 0]
    },
    'LARGE_GREEN_BARREL': {
        'sku': 'LARGE_GREEN_BARREL',
        'size': 'LARGE',
        'color': 'GREEN',
        'ml_per_barrel': 10000,
        'price': 400,
        'potion_type': [0, 1, 0, 0]
    },
    'SMALL_BLUE_BARREL': {
        'sku': 'SMALL_BLUE_BARREL',
        'size': 'SMALL',
        'color': 'BLUE',
        'ml_per_barrel': 500,
        'price': 120,
        'potion_type': [0, 0, 1, 0]
    },
    'MEDIUM_BLUE_BARREL': {
        'sku': 'MEDIUM_BLUE_BARREL',
        'size': 'MEDIUM',
        'color': 'BLUE',
        'ml_per_barrel': 2500,
        'price': 300,
        'potion_type': [0, 0, 1, 0]
    },
    'LARGE_BLUE_BARREL': {
        'sku': 'LARGE_BLUE_BARREL',
        'size': 'LARGE',
        'color': 'BLUE',
        'ml_per_barrel': 10000,
        'price': 600,
        'potion_type': [0, 0, 1, 0]
    },
    'LARGE_DARK_BARREL': {
        'sku': 'LARGE_DARK_BARREL',
        'size': 'LARGE',
        'color': 'DARK',
        'ml_per_barrel': 10000,
        'price': 750,
        'potion_type': [0, 0, 0, 1]
    },
}

# TODO: Update max_potions_per_sku and bottling_ceiling once data analysis concludes findings.
BOTTLING_PARAMETERS = {
    'PRICE_STRATEGY_SKIMMING': {
        'ml_capacity_unit': 1,
        'potion_capacity_unit': 1,
        'max_potions_per_sku': 15,
        'bottling_ceiling': 15,
        'bottling_base': 5,
    },
        'PRICE_STRATEGY_BALANCED': {
        'ml_capacity_unit': 1,
        'potion_capacity_unit': 1,
        'max_potions_per_sku': 15,
        'bottling_ceiling': 15,
        'bottling_base': 5,
    },
    'PRICE_STRATEGY_PENETRATION': {
        'ml_capacity_unit': 2,
        'potion_capacity_unit': 1,
        'max_potions_per_sku': 15,
        'bottling_ceiling': 15,
        'bottling_base': 5,
    },
    'PRICE_STRATEGY_TIERED': {
        'ml_capacity_unit': 3,
        'potion_capacity_unit': 2,
        'max_potions_per_sku': 20,
        'bottling_ceiling': 20,
        'bottling_base': 5,
    },
    'PRICE_STRATEGY_DYNAMIC': {
        'ml_capacity_unit': 4,
        'potion_capacity_unit': 3,
        'max_potions_per_sku': 20,
        'bottling_ceiling': 20,
        'bottling_base': 5,
    },
    'PRICE_STRATEGY_MAXIMIZING': {
        'ml_capacity_unit': 5,
        'potion_capacity_unit': 4,
        'max_potions_per_sku': 25,
        'bottling_ceiling': 25,
        'bottling_base': 5,
    },
}


CAPACITY_PURCHASE_PARAMETERS = {
    'PRICE_STRATEGY_SKIMMING': {
        'ml_capacity_unit': 1,
        'potion_capacity_unit': 1,
        'purchase_conditions': [
            {'gold_threshold': 1420, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 0},
            {'gold_threshold': 1100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 0, 'potions_in_inventory': 15},
        ],
    },
    'PRICE_STRATEGY_BALANCED': {
        'ml_capacity_unit': 1,
        'potion_capacity_unit': 1,
        'purchase_conditions': [
            {'gold_threshold': 2900, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'ml_inventory_threshold': 7500},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'potions_in_inventory': 20},
        ],
    },
    'PRICE_STRATEGY_PENETRATION': {
        'ml_capacity_unit': 2,
        'potion_capacity_unit': 1,
        'purchase_conditions': [
            {'gold_threshold': 2900, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'ml_inventory_threshold': 7500},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'potions_in_inventory': 20},
        ],
    },
    'PRICE_STRATEGY_TIERED': {
        'ml_capacity_unit': 3,
        'potion_capacity_unit': 2,
        'purchase_conditions': [
            {'gold_threshold': 3600, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'ml_inventory_threshold': 7500},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'potions_in_inventory': 35},
        ],
    },
    'PRICE_STRATEGY_DYNAMIC': {
        'ml_capacity_unit': 4,
        'potion_capacity_unit': 3,
        'purchase_conditions': [
            {'gold_threshold': 4350, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1},
            {'gold_threshold': 2100, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'ml_inventory_threshold': 7500},
        ],
    },
    'PRICE_STRATEGY_MAXIMIZING': {
        'ml_capacity_unit': 5,
        'potion_capacity_unit': 4,
        'purchase_conditions': [
            {'gold_threshold': 8500, 'ml_units_to_purchase': 1, 'potion_units_to_purchase': 1, 'ml_inventory_percentage': 75, 'potions_inventory_percentage': 75},
            {'gold_threshold': 7500, 'potion_units_to_purchase': 1, 'potions_inventory_percentage': 75},
            {'gold_threshold': 7500, 'ml_units_to_purchase': 1, 'ml_inventory_percentage': 75},
        ],
    },
}


CATALOG_PARAMETERS = {
    'max_potions_in_catalog': 6,
    'default_potion_ceiling': 30,
    'catalog_fill_order': 'highest_quantity',  # 'potion_priority_order'
}


CAPACITY_UPGRADE_THRESHOLDS = {
    'PRICE_STRATEGY_SKIMMING': {
        'gold_thresholds': [1420, 1100],
        'potions_in_inventory_thresholds': [15],
        'ml_inventory_thresholds': [7500],
    },
    'PRICE_STRATEGY_BALANCED': {
        'gold_thresholds': [2900, 2100],
        'potions_in_inventory_thresholds': [20],
        'ml_inventory_thresholds': [7500],
    },
    'PRICE_STRATEGY_PENETRATION': {
        'gold_thresholds': [2900, 2100],
        'potions_in_inventory_thresholds': [20],
        'ml_inventory_thresholds': [7500],
    },
    'PRICE_STRATEGY_TIERED': {
        'gold_thresholds': [3600, 2100],
        'potions_in_inventory_thresholds': [35],
        'ml_inventory_thresholds': [7500],
    },
    'PRICE_STRATEGY_DYNAMIC': {
        'gold_thresholds': [4350, 2100],
        'potions_in_inventory_thresholds': [35],
        'ml_inventory_thresholds': [7500],
    },
    'PRICE_STRATEGY_MAXIMIZING': {
        'gold_thresholds': [8500, 7500, 5500],
        'potions_in_inventory_percentage': [75],
        'ml_inventory_percentage': [75],
    },
}


DEFAULT_POTIONS = [
    {
        'sku': 'GREEN_POTION',
        'name': 'Green Potion',
        'red_ml': 0,
        'green_ml': 100,
        'blue_ml': 0,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'BLUE_POTION',
        'name': 'Blue Potion',
        'red_ml': 0,
        'green_ml': 0,
        'blue_ml': 100,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 55,
        'current_quantity': 0
    },
    {
        'sku': 'RED_POTION',
        'name': 'Red Potion',
        'red_ml': 100,
        'green_ml': 0,
        'blue_ml': 0,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'TEAL_POTION',
        'name': 'Teal Potion',
        'red_ml': 0,
        'green_ml': 50,
        'blue_ml': 50,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 50,
        'current_quantity': 0
    },
    {
        'sku': 'YELLOW_POTION',
        'name': 'Yellow Potion',
        'red_ml': 50,
        'green_ml': 50,
        'blue_ml': 0,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'DARK_POTION',
        'name': 'Dark Potion',
        'red_ml': 0,
        'green_ml': 0,
        'blue_ml': 0,
        'dark_ml': 100,
        'total_ml': 100,
        'price': 40,
        'current_quantity': 0
    },
    {
        'sku': 'PURPLE_POTION',
        'name': 'Purple Potion',
        'red_ml': 50,
        'green_ml': 0,
        'blue_ml': 50,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 50,
        'current_quantity': 0
    },
    {
        'sku': 'ORANGE_POTION',
        'name': 'Orange Potion',
        'red_ml': 75,
        'green_ml': 0,
        'blue_ml': 25,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
        {
        'sku': 'MAGENTA_POTION',
        'name': 'Magenta Potion',
        'red_ml': 75,
        'green_ml': 0,
        'blue_ml': 25,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'LIME_POTION',
        'name': 'Lime Potion',
        'red_ml': 25,
        'green_ml': 75,
        'blue_ml': 0,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'VIOLET_POTION',
        'name': 'Violet Potion',
        'red_ml': 25,
        'green_ml': 0,
        'blue_ml': 75,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'SPRING_GREEN_POTION',
        'name': 'Spring Green Potion',
        'red_ml': 0,
        'green_ml': 75,
        'blue_ml': 25,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'SKY_BLUE_POTION',
        'name': 'Sky Blue Potion',
        'red_ml': 0,
        'green_ml': 25,
        'blue_ml': 75,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 45,
        'current_quantity': 0
    },
    {
        'sku': 'DARK_GREEN_POTION',
        'name': 'Dark Green Potion',
        'red_ml': 0,
        'green_ml': 50,
        'blue_ml': 0,
        'dark_ml': 50,
        'total_ml': 100,
        'price': 50,
        'current_quantity': 0
    },
    {
        'sku': 'DARK_BLUE_POTION',
        'name': 'Dark Blue Potion',
        'red_ml': 0,
        'green_ml': 0,
        'blue_ml': 50,
        'dark_ml': 50,
        'total_ml': 100,
        'price': 50,
        'current_quantity': 0
    },
    {
        'sku': 'DARK_RED_POTION',
        'name': 'Dark Red Potion',
        'red_ml': 50,
        'green_ml': 0,
        'blue_ml': 0,
        'dark_ml': 50,
        'total_ml': 100,
        'price': 50,
        'current_quantity': 0
    },
    {
        'sku': 'DARK_BROWN_POTION',
        'name': 'Dark Brown Potion',
        'red_ml': 25,
        'green_ml': 25,
        'blue_ml': 25,
        'dark_ml': 25,
        'total_ml': 100,
        'price': 50,
        'current_quantity': 0
    },
]


POTION_DEFINITIONS = {potion['sku']: potion for potion in DEFAULT_POTIONS}


POTION_PRIORITIES = {
    "Hearthday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 50, "sales_mix": 0.35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 50, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price": 50, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 50, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 50, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 30, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ]
    },
    "Crownday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40, "sales_mix": 0.35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 60, "sales_mix": 0.35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 60, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 50, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 50, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price": 50, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ]
    },
    "Blesseday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 60, "sales_mix": 0.35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 45, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 50, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 50, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 45, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 50, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ]
    },
    "Soulday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55, "sales_mix": 0.35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45, "sales_mix": 0.35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 45, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45, "sales_mix": 0.15}
        ]
    },
    "Edgeday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45, "sales_mix": 0.50},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55, "sales_mix": 0.50}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45, "sales_mix": 0.35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55, "sales_mix": 0.35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45, "sales_mix": 0.35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55, "sales_mix": 0.35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ]
    },
    "Bloomday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 45, "sales_mix": 0.35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45, "sales_mix": 0.30},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 45, "sales_mix": 0.25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55, "sales_mix": 0.15},
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 45, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ]
    },
    "Aracanaday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45, "sales_mix": 0.35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 45, "sales_mix": 0.35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 45, "sales_mix": 0.30}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 40, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25, "sales_mix": 0.15},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35, "sales_mix": 0.15},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35, "sales_mix": 0.15}
        ]
    }
}
