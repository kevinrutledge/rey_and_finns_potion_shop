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
        'price': 40,
        'description': 'Hypothesis: Restores vitality.',
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
        'price': 40,
        'description': 'Hypothesis: Grants wisdom.',
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
        'price': 40,
        'description': 'Hypothesis: Enhances strength.',
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
        'description': 'Hypothesis Shadow magic.',
        'current_quantity': 0
    },
    {
        'sku': 'CYAN_POTION',
        'name': 'Cyan Potion',
        'red_ml': 0,
        'green_ml': 50,
        'blue_ml': 50,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 50,
        'description': 'Hypothesis: Grants both vitality and wisdom.',
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
        'description': 'Hypothesis: Grants both strength and vitality.',
        'current_quantity': 0
    },
    {
        'sku': 'MAGENTA_POTION',
        'name': 'Magenta Potion',
        'red_ml': 50,
        'green_ml': 0,
        'blue_ml': 50,
        'dark_ml': 0,
        'total_ml': 100,
        'price': 50,
        'description': 'Hypothesis: Grants both strength and wisdom.',
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
        'description': 'Hypothesis: Grants both shadow and vitality.',
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
        'description': 'Hypothesis: Grants both shadow and wisdom.',
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
        'description': 'Hypothesis: Grants both shadow and strength.',
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
        'description': 'Hypothesis: Grants every property.',
        'current_quantity': 0
    },
]


"""
Pricing Strategies for Each In-Game Day

Each day contains different pricing strategies based on storage capacities:
1. PRICE_STRATEGY_PREMIUM (50 potions capacity)
2. PRICE_STRATEGY_COMPETITIVE (100 potions capacity)
3. PRICE_STRATEGY_PENETRATION (150+ potions capacity)

Each strategy includes a list of potions with their composition and adjusted prices.
"""
POTION_PRIORITIES = {
    "Hearthday": {
        "PRICE_STRATEGY_PREMIUM": [
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price": 50},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 35},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 45},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 45},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price" : 45},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price" : 40},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40}
        ]
    },

    "Crownday": {
        "PRICE_STRATEGY_PREMIUM": [
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 45},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 35},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 45},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 45},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 40},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40}
        ]
    },

    "Blesseday": {
        "PRICE_STRATEGY_PREMIUM": [
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 35},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 35},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 45},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 45},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 30},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 40},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40}
        ]
    },

    "Soulday": {
        "PRICE_STRATEGY_PREMIUM": [
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "price": 50},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 35},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 35},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "price" : 45},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 30},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "price" : 40},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "price" : 40}
        ]
    },

    "Edgeday": {
        "PRICE_STRATEGY_PREMIUM": [
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 35},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 45},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 45},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 45},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 40},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40}
        ]
    
    },
    "Bloomday": {
        "PRICE_STRATEGY_PREMIUM": [
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 50},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 35},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 45},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price" : 45},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 45},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [

            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price" : 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "price" : 40},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40}
        ]
    },

    "Aracanaday": {
        "night": [
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price": 50}
        ],
        "PRICE_STATEGY_COMPETITIVE": [
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 45},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 35},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 35},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price" : 45},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 45},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 45}
        ],
        "PRICE_STRATEGY_PENETRATION": [
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "price" : 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "price" : 30},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "price" : 30},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "price" : 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "price" : 40},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "price" : 40}
        ]
    },
}
