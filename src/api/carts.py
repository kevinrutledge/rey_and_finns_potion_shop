import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel, validator
from src.api import auth
from enum import Enum

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

carts = {}
cart_items = {}

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

    @validator('customer_name')
    def validate_customer_name(cls, customer_name_value):
        if not customer_name_value.strip():
            raise ValueError('Customer name must not be empty')
        return customer_name_value

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    logger.debug("carts/search/ - in")
    logger.debug(f"Customer Name: {customer_name}") 
    logger.debug(f"Potion SKU: {potion_sku}")
    logger.debug(f"Search Page: {search_page}")
    logger.debug(f"Sort Col: {sort_col}")
    logger.debug(f"Sort Order: {sort_order}")

    try:
        # TODO: Implement actual search logic with filtering, sorting, and pagination
        results = [
            {
                    "line_item_id": 1,
                    "item_sku": "1 oblivion potion",
                    "customer_name": "Scaramouche",
                    "line_item_total": 50,
                    "timestamp": "2021-01-01T00:00:00Z",
                }
        ]
    
        # Pagination logic
        previous = ""
        next_page = ""

        logger.debug("carts/search/ - out")
        logger.debug(f"Results: {results}")
        logger.debug(f"Previous: {previous}")
        logger.debug(f"Next: {next_page}")

        return {
            "previous": previous,
            "next": next_page,
            "results": results,
        }

    except Exception as e:
        logger.exception("Error during carts/search")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

    @validator('customer_name')
    def validate_customer_name(cls, name_value):
        if not name_value.strip():
            raise ValueError('Customer name must not be empty')
        return name_value

    @validator('level')
    def level_must_be_positive(cls, level_value):
        if level_value < 1:
            raise ValueError('Level must be at least 1')
        return level_value

@router.post("/visits/{visit_id}", summary="Post Visits", description="Record customers who visited shop.")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Record which customers visited the shop today.
    """
    logger.debug("carts/visits/{visit_id} - in")
    logger.debug(f"Visit ID: {visit_id}")
    logger.debug(f"Customers: {customers}")

    try:
        # TODO: Implement logic to record visits
        logger.debug("carts/visits/{visit_id} - out")
        return {"status": "OK"}

    except Exception as e:
        logger.exception("Error during carts/visits")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

@router.post("/", summary="Create Cart", description="Create new cart for customer.")
def create_cart(new_cart: Customer):
    """ """
    logger.debug("carts/ Create Cart - in")
    logger.debug(f"New Cart: {new_cart}")

    try:
        cart_id = len(carts) + 1
        carts[cart_id] = new_cart
        cart_items[cart_id] = {}

        logger.debug("carts/Create Cart - out")
        logger.debug(f"Cart ID: {cart_id}")

        return {"cart_id": cart_id}

    except Exception as e:
        logger.exception("Error during carts/create_cart")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


class CartItem(BaseModel):
    quantity: int

    @validator('quantity')
    def quantity_must_be_positive(cls, quantity_value):
        if quantity_value < 1:
            raise ValueError('Quantity must be at least 1')
        return quantity_value


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Set quantity of an item in cart.
    """
    logger.debug("carts/{cart_id}/items/{item_sku} - in")
    logger.debug(f"Cart Id: {cart_id}")
    logger.debug(f"Item SKU: {item_sku}")
    logger.debug(f"Cart Item: {cart_item}")

    try:
        if cart_id in carts:
            cart_items[cart_id][item_sku] = cart_item.quantity
            logger.debug("carts/{cart_id}/items/{item_sku} - out")
            logger.debug(f"Cart_items[{cart_id}][{item_sku}]: {cart_items[cart_id][item_sku]}")
            return {"status": "OK"}
        else:
            logger.error(f"Cart {cart_id} not found.")
            raise HTTPException(status_code=404, detail="Cart not found.")

    except Exception as e:
        logger.exception("Error during carts/set_item_quantity")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


class CartCheckout(BaseModel):
    payment: str

    @validator('payment')
    def payment_must_not_be_empty(cls, payment_value):
        if not payment_value.strip():
            raise ValueError('Payment method must not be empty')
        return payment_value

@router.post("/{cart_id}/checkout", summary="Set Item Quantity", description="Set quantity of specific item in cart.")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
   Checkout cart.
    """
    logger.debug("carts/cart_id/checkout - in")
    logger.debug(f"Cart Id: {cart_id}")
    logger.debug(f"Cart Checkout: {cart_checkout}")

    try:
        if cart_id in carts:
            total_potions_bought = 0
            total_gold_paid = 0

            with db.engine.begin() as connection:
                # Fetch number of green potions from global inventory
                sql_select = "SELECT num_green_potions FROM global_inventory;"
                result = connection.execute(sqlalchemy.text(sql_select))
                row = result.mappings().one_or_none()

                if row is None:
                    logger.error("No inventory record found.")
                    raise HTTPException(status_code=500, detail="Inventory record not found.")

                num_green_potions = row['num_green_potions']
                logger.debug(f"Number of Green Potions in Inventory: {num_green_potions}")

                # Calculate totals based on cart items
                for sku, quantity in cart_items[cart_id].items():
                    if sku == "GREEN_POTION_0":
                        total_potions_bought += quantity
                        total_gold_paid += quantity * 50

                logger.debug(f"Total Potions Bought: {total_potions_bought}")
                logger.debug(f"Total Gold Paid: {total_gold_paid}")

                # Check if enough potions are available
                if total_potions_bought <= num_green_potions:
                    # Update potions in inventory
                    sql_update_potions = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET num_green_potions = num_green_potions - :total_potions_bought
                    """)
                    connection.execute(sql_update_potions, {'total_potions_bought': total_potions_bought})
                    logger.debug(f"Updated Potions: Subtracted {total_potions_bought} green potions.")

                    # Update gold in inventory
                    sql_update_gold = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET gold = gold + :total_gold_paid
                    """)
                    connection.execute(sql_update_gold, {'total_gold_paid': total_gold_paid})
                    logger.debug(f"Updated Gold: Added {total_gold_paid} gold to inventory.")

                    logger.debug("carts/{cart_id}/checkout - out")
                    logger.debug(f"Total Potions Bought: {total_potions_bought}")
                    logger.debug(f"Total Gold Paid: {total_gold_paid}")

                    return {
                        "total_potions_bought": total_potions_bought,
                        "total_gold_paid": total_gold_paid
                    }
                else:
                    logger.error("Not enough potions in inventory.")
                    raise HTTPException(status_code=400, detail="Not enough potions in inventory.")
        else:
            logger.error(f"Cart {cart_id} not found.")
            raise HTTPException(status_code=404, detail="Cart not found.")

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during carts/checkout")
        raise HTTPException(status_code=500, detail="Database error.")
    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise he
    except Exception as e:
        logger.exception("Unexpected error during carts/checkout")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
