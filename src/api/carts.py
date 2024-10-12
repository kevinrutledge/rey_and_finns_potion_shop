import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.api import auth
from datetime import datetime
from enum import Enum
import traceback
import json


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

class CartItem(BaseModel):
    quantity: int

class CartCheckout(BaseModel):
    payment: str


@router.get("/search/", tags=["search"])
def search_orders(

    customer_name: str = "",
    potion_sku: str = "",
    search_page: int = 1,
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
    logger.info("Endpoint /carts/search/ called.")
    logger.debug(
        f"Parameters received - customer_name: '{customer_name}', "
        f"potion_sku: '{potion_sku}', search_page: {search_page}, "
        f"sort_col: '{sort_col}', sort_order: '{sort_order}'"
    )


@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited shop today?
    """
    logger.info(f"Post Visits called with {len(customers)} customers.")
    logger.debug(f"Customers data: {customers}")

    try:
        with db.engine.begin() as connection:
            # Insert into customer_visits table with customers JSON
            in_game_day, in_game_hour = ut.Utils.get_current_in_game_time()
            customers_json = json.dumps([customer.dict() for customer in customers])
            logger.debug(f"Storing customers in customer_visits.")

            insert_visit_query = """
                INSERT INTO customer_visits (visit_time, customers, in_game_day, in_game_hour)
                VALUES (:visit_time, :customers, :in_game_day, :in_game_hour)
                RETURNING visit_id;
            """
            result = connection.execute(
                sqlalchemy.text(insert_visit_query),
                {
                    "visit_time": datetime.now(tz=ut.LOCAL_TIMEZONE),
                    "customers": customers_json,
                    "in_game_day": in_game_day,
                    "in_game_hour": in_game_hour,
                },
            )
            visit_id = result.scalar()
            logger.debug(f"Inserted visit with visit_id={visit_id}")

    except HTTPException as he:
        logger.error(f"HTTPException in post_visits: {he.detail}")
        logger.debug(traceback.format_exc())
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in post_visits: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    logger.info(f"Successfully recorded visit_id={visit_id} with {len(customers)} customers.")
    return {"success": True, "visit_id": visit_id}


@router.post("/")
def create_cart(new_cart: Customer):
    """
    Create new cart for customer.
    """
    logger.info(f"Create Cart called for customer '{new_cart.customer_name}'.")
    logger.debug(f"Customer data: {new_cart}")

    try:
        with db.engine.begin() as connection:
            # Insert a new visit into customer_visits
            in_game_day, in_game_hour = ut.Utils.get_current_in_game_time()
            insert_visit_query = """
                INSERT INTO customer_visits (visit_time, customers, in_game_day, in_game_hour)
                VALUES (:visit_time, :customers, :in_game_day, :in_game_hour)
                RETURNING visit_id;
            """
            visit_id = connection.execute(
                sqlalchemy.text(insert_visit_query),
                {
                    "visit_time": datetime.now(tz=ut.LOCAL_TIMEZONE),
                    "customers": json.dumps([]),  # Initialize with empty customers list
                    "in_game_day": in_game_day,
                    "in_game_hour": in_game_hour,
                },
            ).scalar()
            logger.debug(f"Inserted visit with visit_id={visit_id}")

            # Insert customer with visit_id
            insert_customer_query = """
                INSERT INTO customers (customer_name, character_class, level, visit_id)
                VALUES (:customer_name, :character_class, :level, :visit_id)
                RETURNING customer_id;
            """
            result = connection.execute(
                sqlalchemy.text(insert_customer_query),
                {
                    "customer_name": new_cart.customer_name,
                    "character_class": new_cart.character_class,
                    "level": new_cart.level,
                    "visit_id": visit_id,
                },
            )
            customer_id = result.scalar()
            logger.debug(f"Inserted customer with customer_id={customer_id}")

            # Insert new cart into carts table
            insert_cart_query = """
                INSERT INTO carts (customer_id, in_game_day, in_game_hour, created_at)
                VALUES (:customer_id, :in_game_day, :in_game_hour, :created_at)
                RETURNING cart_id;
            """
            cart_id = connection.execute(
                sqlalchemy.text(insert_cart_query),
                {
                    "customer_id": customer_id,
                    "in_game_day": in_game_day,
                    "in_game_hour": in_game_hour,
                    "created_at": datetime.now(tz=ut.LOCAL_TIMEZONE),
                },
            ).scalar()
            logger.debug(f"Inserted cart with cart_id={cart_id}")

        logger.info(f"Successfully created cart_id={cart_id} for customer_id={customer_id}.")
        return {"cart_id": cart_id}

    except Exception as e:
        logger.exception(f"Unhandled exception in create_cart: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Add or update item quantity in cart.
    """
    logger.info(f"Set Item Quantity called for cart_id={cart_id}, item_sku='{item_sku}', quantity={cart_item.quantity}.")
    logger.debug(f"CartItem data: {cart_item}")

    if cart_item.quantity < 1 or cart_item.quantity > 10000:
        logger.error("Quantity must be between 1 and 10,000.")
        raise HTTPException(status_code=400, detail="Quantity must be between 1 and 10,000.")

    try:
        with db.engine.begin() as connection:
            # Check if cart exists and is not checked out
            check_cart_query = """
                SELECT checked_out FROM carts WHERE cart_id = :cart_id;
            """
            result = connection.execute(
                sqlalchemy.text(check_cart_query),
                {"cart_id": cart_id},
            )
            cart = result.mappings().fetchone()
            if not cart:
                logger.error(f"Cart with cart_id={cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart["checked_out"]:
                logger.error(f"Cannot modify checked-out cart with cart_id={cart_id}.")
                raise HTTPException(status_code=400, detail="Cannot modify checked-out cart.")

            # Fetch potion_id from potions table using SKU
            fetch_potion_query = """
                SELECT potion_id, price, current_quantity
                FROM potions
                WHERE sku = :sku
                LIMIT 1;
            """
            result = connection.execute(
                sqlalchemy.text(fetch_potion_query),
                {"sku": item_sku},
            )
            potion = result.mappings().fetchone()
            if not potion:
                logger.error(f"Potion with SKU '{item_sku}' does not exist.")
                raise HTTPException(status_code=404, detail="Potion not found.")

            potion_id = potion["potion_id"]
            price = potion["price"]
            current_quantity = potion["current_quantity"]

            logger.debug(f"Fetched potion_id={potion_id}, price={price}, current_quantity={current_quantity}.")

            # Check if potion is already in cart
            check_cart_item_query = """
                SELECT cart_item_id, quantity FROM cart_items
                WHERE cart_id = :cart_id AND potion_id = :potion_id;
            """
            result = connection.execute(
                sqlalchemy.text(check_cart_item_query),
                {"cart_id": cart_id, "potion_id": potion_id},
            )
            existing_item = result.mappings().fetchone()

            # Calculate total cost and validate inventory
            total_cost = price * cart_item.quantity
            if cart_item.quantity > current_quantity:
                logger.error("Requested quantity exceeds available inventory.")
                raise HTTPException(status_code=400, detail="Requested quantity exceeds available inventory.")

            if existing_item:
                # Update existing cart item
                update_cart_item_query = """
                    UPDATE cart_items
                    SET quantity = :quantity, line_item_total = :line_item_total, timestamp = :timestamp
                    WHERE cart_item_id = :cart_item_id;
                """
                connection.execute(
                    sqlalchemy.text(update_cart_item_query),
                    {
                        "quantity": cart_item.quantity,
                        "line_item_total": total_cost,
                        "timestamp": ut.Utils.get_current_in_game_time(),
                        "cart_item_id": existing_item["cart_item_id"],
                    },
                )
                logger.info(f"Updated cart_item_id={existing_item['cart_item_id']} with quantity={cart_item.quantity}.")
            else:
                # Insert new cart item
                insert_cart_item_query = """
                    INSERT INTO cart_items (cart_id, potion_id, quantity, price, line_item_total, timestamp)
                    VALUES (:cart_id, :potion_id, :quantity, :price, :line_item_total, :timestamp)
                    RETURNING cart_item_id;
                """
                cart_item_id = connection.execute(
                    sqlalchemy.text(insert_cart_item_query),
                    {
                        "cart_id": cart_id,
                        "potion_id": potion_id,
                        "quantity": cart_item.quantity,
                        "price": price,
                        "line_item_total": total_cost,
                        "timestamp": ut.Utils.get_current_in_game_time(),
                    },
                ).scalar()
                logger.info(f"Inserted new cart_item_id={cart_item_id} with quantity={cart_item.quantity}.")

    except HTTPException as he:
        logger.error(f"HTTPException in set_item_quantity: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in set_item_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    logger.info(f"Successfully set quantity for item_sku='{item_sku}' in cart_id={cart_id}.")
    return {"success": True}


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Checkout cart.
    """
    logger.info(f"Checkout called for cart_id={cart_id} with payment method='{cart_checkout.payment}'.")
    logger.debug(f"CartCheckout data: {cart_checkout}")

    try:
        with db.engine.begin() as connection:
            # Fetch cart details
            fetch_cart_query = """
                SELECT 
                    ca.checked_out, 
                    ca.total_potions_bought, 
                    ca.total_gold_paid 
                FROM carts ca
                WHERE ca.cart_id = :cart_id
                LIMIT 1;
            """
            result = connection.execute(
                sqlalchemy.text(fetch_cart_query),
                {"cart_id": cart_id},
            )
            cart = result.mappings().fetchone()
            if not cart:
                logger.error(f"Cart with cart_id={cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart["checked_out"]:
                logger.error(f"Cart with cart_id={cart_id} has already been checked out.")
                raise HTTPException(status_code=400, detail="Cart has already been checked out.")

            # Fetch cart items
            fetch_cart_items_query = """
                SELECT 
                    ci.potion_id, 
                    ci.quantity, 
                    ci.line_item_total, 
                    p.price 
                FROM cart_items ci
                JOIN potions p ON ci.potion_id = p.potion_id
                WHERE ci.cart_id = :cart_id;
            """
            result = connection.execute(
                sqlalchemy.text(fetch_cart_items_query),
                {"cart_id": cart_id},
            )
            cart_items = result.mappings().fetchall()

            if not cart_items:
                logger.error(f"No items found in cart_id={cart_id}.")
                raise HTTPException(status_code=400, detail="Cart is empty.")

            total_potions_bought = 0
            total_gold_paid = 0

            # Verify inventory and calculate totals
            for item in cart_items:
                potion_id = item["potion_id"]
                quantity = item["quantity"]
                line_item_total = item["line_item_total"]
                price = item["price"]

                # Fetch potion inventory
                fetch_potion_query = """
                    SELECT current_quantity 
                    FROM potions 
                    WHERE potion_id = :potion_id
                    LIMIT 1;
                """
                result = connection.execute(
                    sqlalchemy.text(fetch_potion_query),
                    {"potion_id": potion_id},
                )
                potion = result.mappings().fetchone()
                if not potion:
                    logger.error(f"Potion with potion_id={potion_id} not found.")
                    raise HTTPException(status_code=404, detail="Potion not found.")

                current_quantity = potion["current_quantity"]
                if quantity > current_quantity:
                    logger.error(f"Insufficient inventory for potion_id={potion_id}. Requested: {quantity}, Available: {current_quantity}.")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient inventory for potion_id={potion_id}.",
                    )

                total_potions_bought += quantity
                total_gold_paid += line_item_total

            # Update inventory and gold
            for item in cart_items:
                potion_id = item["potion_id"]
                quantity = item["quantity"]

                # Deduct potion quantity
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = current_quantity - :quantity
                    WHERE potion_id = :potion_id;
                """
                connection.execute(
                    sqlalchemy.text(update_potion_query),
                    {"quantity": quantity, "potion_id": potion_id},
                )
                logger.debug(f"Deducted {quantity} from potion_id={potion_id}.")

            # Update global_inventory gold and total_potions
            update_global_inventory_query = """
                UPDATE global_inventory
                SET 
                    gold = gold + :total_gold_paid,
                    total_potions = total_potions - :total_potions_bought
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_global_inventory_query),
                {
                    "total_gold_paid": total_gold_paid,
                    "total_potions_bought": total_potions_bought
                },
            )
            logger.debug(f"Added {total_gold_paid} gold and subtracted {total_potions_bought} potions to global_inventory.")

            # Mark cart as checked out
            mark_cart_checked_out_query = """
                UPDATE carts
                SET 
                    checked_out = TRUE,
                    checked_out_at = :checked_out_at,
                    total_potions_bought = :total_potions_bought,
                    total_gold_paid = :total_gold_paid,
                    payment = :payment
                WHERE cart_id = :cart_id;
            """
            connection.execute(
                sqlalchemy.text(mark_cart_checked_out_query),
                {
                    "checked_out_at": ut.Utils.get_current_in_game_time(),
                    "total_potions_bought": total_potions_bought,
                    "total_gold_paid": total_gold_paid,
                    "payment": cart_checkout.payment,
                    "cart_id": cart_id,
                },
            )
            logger.info(f"Marked cart_id={cart_id} as checked out.")

        response = {
            "total_potions_bought": total_potions_bought,
            "total_gold_paid": total_gold_paid,
        }

    except HTTPException as he:
        logger.error(f"HTTPException in checkout: {he.detail}")
        raise he
    except Exception as e:
        logger.exception(f"Unhandled exception in checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

    logger.info(f"Checkout response: {response}")
    return response
