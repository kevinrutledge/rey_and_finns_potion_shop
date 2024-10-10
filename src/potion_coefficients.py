# Defined default potions
DEFAULT_POTIONS = [
    {
        'sku': 'GREEN_POTION',
        'name': 'Elixir of Vitality',
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
        'name': 'Elixir of Wisdom',
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
        'name': 'Elixir of Strength',
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
        'sku': 'SHADOW_ELIXIR',
        'name': 'Shadow Elixir',
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
        'name': 'Cyan Elixir',
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
        'name': 'Sunburst Elixir',
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
        'name': 'Magenta Elixir',
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
        'sku': 'VERDANT_SHADOW_ELIXIR',
        'name': 'Verdant Shadow Elixir',
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
        'sku': 'AZURE_SHADOW_ELIXIR',
        'name': 'Azure Shadow Elixir',
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
        'sku': 'CRIMSON_SHADOW_ELIXIR',
        'name': 'Crimson Shadow Elixir',
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
        'sku': 'OBSIDIAN_ELIXIR',
        'name': 'Obsidian Elixir',
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
Potion Coefficients for Each In-Game Day and Hour Block

Each day is divided into four hour blocks:
1. Hours 2, 4, 6
2. Hours 8, 10, 12
3. Hours 14, 16, 18
4. Hours 20, 22, 24

Each hour block contains list of potions with their composition,
demand coefficients, and prices.
"""
potion_coefficients = {
    # Hearthday
    "Hearthday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
    },

    # Crownday
    "Crownday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
    },

    # Blessday
    "Blesseday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
    },

    # Soulday
    "Soulday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "demand": 15,  "price": 50},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "demand": 15,  "price": 50},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "demand": 15,  "price": 50},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Dark Blue Potion", "composition": [0, 0, 50, 50], "demand": 15,  "price": 50},
            {"name": "Dark Red Potion", "composition": [50, 0, 0, 50], "demand": 15,  "price": 50}
        ],
    },

    # Edgeday
    "Edgeday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 15,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 20,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 15,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 20,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 15,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 20,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 15,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 20,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
    
    # Bloomday
    },
    "Bloomday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Yellow Potion", "composition": [50, 50, 0, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
    },

    # Aracanday
    "Aracanaday": {
        "night": [
            # Define potions for hours 0, 2, 4
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "morning": [
            # Define potions for hours 6, 8, 10
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "afternoon": [
            # Define potions for hours 12, 14, 16
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
        "evening": [
            # Define potions for hours 18, 20, 22
            {"name": "Blue Potion", "composition": [0, 0, 100, 0], "demand": 15,  "price": 50},
            {"name": "Green Potion", "composition": [0, 100, 0, 0], "demand": 20,  "price": 40},
            {"name": "Red Potion", "composition": [100, 0, 0, 0], "demand": 20,  "price": 40},
            {"name": "Cyan Potion", "composition": [0, 50, 50, 0], "demand": 15,  "price": 50},
            {"name": "Magenta Potion", "composition": [50, 0, 50, 0], "demand": 15,  "price": 50},
            {"name": "Dark Potion", "composition": [0, 0, 0, 100], "demand": 15,  "price": 50}
        ],
    },
}
