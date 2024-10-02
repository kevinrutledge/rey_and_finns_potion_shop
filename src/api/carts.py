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

class SearchSortOptions(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class SearchSortOrder(str, Enum):
    asc = "asc"
    desc = "desc"

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

class CartItem(BaseModel):
    quantity: int


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
    try:
        logger.debug(
            f"Search parameters - customer_name: '{customer_name}', potion_sku: '{potion_sku}', "
            f"search_page: '{search_page}', sort_col: '{sort_col}', sort_order: '{sort_order}'"
        )
        
        # TODO: Implement actual search logic with filtering, sorting, and pagination
        # For now, returning a mock response
        results = [
            {
                "line_item_id": 1,
                "item_sku": "1_oblivion_potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ]
        logger.info(f"Search results: {results}")
    
        # Pagination logic (mock)
        previous = ""
        next_page = ""
    
        return {
            "previous": previous,
            "next": next_page,
            "results": results,
        }
    
    except Exception:
        logger.exception("Error during search_orders")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.post("/visits/{visit_id}", summary="Post Visits", description="Record customers who visited shop.")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Record which customers visited the shop today.
    """
    try:
        logger.debug(f"Recording visits for visit_id: {visit_id} with customers: {customers}")
    
        # TODO: Implement logic to record visits in the database
        # Currently, this is a stub implementation
    
        logger.info(f"Recorded {len(customers)} customers for visit_id: {visit_id}")
    
        return {"status": "OK"}
    
    except Exception:
        logger.exception(f"Error during post_visits for visit_id: {visit_id}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.post("/", summary="Create Cart", description="Create new cart for customer.")
def create_cart(new_cart: Customer):
    """
    Create a new cart for a specific customer.
    """
    try:
        cart_id = len(carts) + 1
        carts[cart_id] = new_cart
        cart_items[cart_id] = {}
    
        logger.info(f"Created new cart with cart_id: {cart_id} for customer: {new_cart.customer_name}")
    
        return {"cart_id": cart_id}
    
    except Exception:
        logger.exception("Error during create_cart")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Set quantity of an item in cart.
    """
    try:
        logger.debug(f"Setting item '{item_sku}' with quantity {cart_item.quantity} in cart_id: {cart_id}")
    
        if cart_id in carts:
            cart_items[cart_id][item_sku] = cart_item.quantity
            logger.info(f"Updated cart_id: {cart_id} with item_sku: {item_sku}, quantity: {cart_item.quantity}")
            return {"status": "OK"}
        else:
            logger.error(f"Cart {cart_id} not found when trying to set item '{item_sku}'.")
            raise HTTPException(status_code=404, detail="Cart not found.")
    
    except Exception:
        logger.exception(f"Error during set_item_quantity for cart_id: {cart_id}, item_sku: {item_sku}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


@router.post("/{cart_id}/checkout", summary="Set Item Quantity", description="Set quantity of specific item in cart.")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
   Checkout cart.
    """
    try:
        logger.debug(f"Initiating checkout for cart_id: {cart_id} with payment method: {cart_checkout.payment}")
    
        if cart_id in carts:
            total_potions_bought = 0
            total_gold_paid = 0
    
            with db.engine.begin() as connection:
                # Fetch number of green potions from global inventory
                sql_select = "SELECT num_green_potions FROM global_inventory;"
                result = connection.execute(sqlalchemy.text(sql_select))
                row = result.mappings().one_or_none()
    
                if row is None:
                    logger.error("No inventory record found in global_inventory table.")
                    raise HTTPException(status_code=500, detail="Inventory record not found.")
    
                num_green_potions = row['num_green_potions']
                logger.debug(f"Number of Green Potions in Inventory: {num_green_potions}")
    
                # Calculate totals based on cart items
                for sku, quantity in cart_items[cart_id].items():
                    if sku == "GREEN_POTION_0":
                        total_potions_bought += quantity
                        total_gold_paid += quantity * 50
                        logger.debug(f"Adding {quantity} Green Potions, costing {quantity * 50} gold.")
    
                logger.info(f"Cart {cart_id} - Total Potions Bought: {total_potions_bought}, Total Gold Paid: {total_gold_paid}")
    
                # Check if enough potions are available
                if total_potions_bought <= num_green_potions:
                    # Update potions in inventory
                    sql_update_potions = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET num_green_potions = num_green_potions - :total_potions_bought
                    """)
                    connection.execute(sql_update_potions, {'total_potions_bought': total_potions_bought})
                    logger.debug(f"Subtracted {total_potions_bought} Green Potions from inventory.")
    
                    # Update gold in inventory
                    sql_update_gold = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET gold = gold + :total_gold_paid
                    """)
                    connection.execute(sql_update_gold, {'total_gold_paid': total_gold_paid})
                    logger.debug(f"Added {total_gold_paid} gold to inventory.")
    
                    logger.info(f"Checkout successful for cart_id: {cart_id}")
    
                    return {
                        "total_potions_bought": total_potions_bought,
                        "total_gold_paid": total_gold_paid
                    }
                else:
                    logger.error(f"Not enough Green Potions in inventory for cart_id: {cart_id}. Requested: {total_potions_bought}, Available: {num_green_potions}")
                    raise HTTPException(status_code=400, detail="Not enough potions in inventory.")
        else:
            logger.error(f"Cart {cart_id} not found during checkout.")
            raise HTTPException(status_code=404, detail="Cart not found.")
    
    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception(f"Database error during checkout for cart_id: {cart_id}")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception(f"Unexpected error during checkout for cart_id: {cart_id}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
