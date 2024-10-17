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

# Defined default potions
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
        'price': 65,
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
        'price': 50,
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


"""
Pricing Strategies for Each In-Game Day

Each day contains different pricing strategies based on storage capacities:
1. PRICE_STRATEGY_SKIMMING (50 potions and 10000 ml capacity)
2. PRICE_STRATEGY_PENETRATION (50 - 100 potions and 10000 - 20000 ml capacity)
3. PRICE_STRATEGY_TIERED (100 - 200 potions and 20000 - 40000 ml capacity)
3. PRICE_STRATEGY_DYNAMIC (200 potions or more and 40000 or more ml capacity)

Each strategy includes list of potions with their composition and adjusted prices.
"""
POTION_PRIORITIES = {
    "Hearthday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 50},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 50},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price": 50},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 50},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 50}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 30},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 40},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 40},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ]
    },
    "Crownday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 60},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 60},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 50},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 50},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price": 50}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 40},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 40},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ]
    },
    "Blesseday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 60},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 45},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 40},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 50},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 50}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price": 45},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 40},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 50}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ]
    },
    "Soulday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 45},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 45},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 30},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price": 45}
        ]
    },
    "Edgeday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 55}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 45},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 55},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ]
    },
    "Bloomday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 40},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price": 50},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 40}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 35},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 35},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 45},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 45},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 40},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 40},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35},
            {"sku": "YELLOW_POTION", "composition": [50, 50, 0, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ]
    },
    "Aracanaday": {
        "PRICE_STRATEGY_SKIMMING": [
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price": 45},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price": 45},
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 45},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 35},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 35},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 45},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 45},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_TIERED": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 40},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 30},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 30},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 40},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 40},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 40}
        ],
        "PRICE_STRATEGY_DYNAMIC": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ],
        "PRICE_STRATEGY_MAXIMIZING": [
            {"sku": "BLUE_POTION", "composition": [0, 0, 100, 0], "price" : 35},
            {"sku": "GREEN_POTION", "composition": [0, 100, 0, 0], "price" : 25},
            {"sku": "RED_POTION", "composition": [100, 0, 0, 0], "price" : 25},
            {"sku": "TEAL_POTION", "composition": [0, 50, 50, 0], "price" : 35},
            {"sku": "PURPLE_POTION", "composition": [50, 0, 50, 0], "price" : 35},
            {"sku": "DARK_POTION", "composition": [0, 0, 0, 100], "price" : 35}
        ]
    }
}
