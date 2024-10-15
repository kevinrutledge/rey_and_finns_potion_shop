import sqlalchemy
import logging
from src import database as db
from src import utilities as ut
from sqlalchemy import bindparam, JSON
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from src.api import auth
from datetime import datetime
from enum import Enum


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
            # Get current in-game day and hour
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM in_game_time
                ORDER BY created_at DESC
                LIMIT 1;
            """
            logger.debug(f"Executing query to fetch latest in-game time: {query_game_time.strip()}")
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise ValueError("No in-game time found in database.")

            # Convert customers to list of dicts
            customers_json = [customer.dict() for customer in customers]

            # Prepare the SQL query with bind parameters
            insert_customer_visit_query = sqlalchemy.text("""
                INSERT INTO customer_visits (visit_id, customers, in_game_day, in_game_hour, visit_time)
                VALUES (:visit_id, :customers, :in_game_day, :in_game_hour, NOW())
            """).bindparams(bindparam('customers', type_=JSON))

            # Execute query without wrapping with sqlalchemy.text() again
            connection.execute(
                insert_customer_visit_query,
                {
                    "visit_id": visit_id,
                    "customers": customers_json,  # Pass as Python list
                    "in_game_day": current_in_game_day,
                    "in_game_hour": current_in_game_hour
                }
            )
            logger.info(f"Inserted customer_visit with visit_id: {visit_id}")

            # Insert each customer into customers table
            insert_customer_query = """
                INSERT INTO customers (visit_id, customer_name, character_class, level, in_game_day, in_game_hour)
                VALUES (:visit_id, :customer_name, :character_class, :level, :in_game_day, :in_game_hour)
            """
            for customer in customers:
                connection.execute(
                    sqlalchemy.text(insert_customer_query),
                    {
                        "visit_id": visit_id,
                        "customer_name": customer.customer_name,
                        "character_class": customer.character_class,
                        "level": customer.level,
                        "in_game_day": current_in_game_day,
                        "in_game_hour": current_in_game_hour
                    }
                )
                logger.debug(f"Inserted customer: {customer.customer_name}")

    except HTTPException as he:
        logger.error(f"HTTPException in post_visits: {he.detail}")
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
            # Get current in-game day and hour
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM in_game_time
                ORDER BY created_at DESC
                LIMIT 1;
            """
            logger.debug(f"Executing query to fetch latest in-game time: {query_game_time.strip()}")
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise ValueError("No in-game time found in database.")

            # Find existing customer
            find_customer_query = """
                SELECT customer_id FROM customers
                WHERE customer_name = :customer_name
                  AND character_class = :character_class
                  AND level = :level
                ORDER BY customer_id DESC
                LIMIT 1;
            """
            result = connection.execute(
                sqlalchemy.text(find_customer_query),
                {
                    "customer_name": new_cart.customer_name,
                    "character_class": new_cart.character_class,
                    "level": new_cart.level,
                },
            )
            customer = result.mappings().fetchone()
            if customer:
                customer_id = customer['customer_id']
                logger.debug(f"Found existing customer with customer_id={customer_id}")
            else:
                logger.error(f"Customer not found for name: {new_cart.customer_name}")
                raise HTTPException(status_code=404, detail="Customer not found.")

            insert_cart_query = """
                INSERT INTO carts (customer_id, in_game_day, in_game_hour, created_at)
                VALUES (:customer_id, :in_game_day, :in_game_hour, NOW())
                RETURNING cart_id;
            """
            cart_id = connection.execute(
                sqlalchemy.text(insert_cart_query),
                {
                    "customer_id": customer_id,
                    "in_game_day": current_in_game_day,
                    "in_game_hour": current_in_game_hour,
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
                    SET quantity = :quantity, line_item_total = :line_item_total, timestamp = NOW()
                    WHERE cart_item_id = :cart_item_id;
                """
                connection.execute(
                    sqlalchemy.text(update_cart_item_query),
                    {
                        "quantity": cart_item.quantity,
                        "line_item_total": total_cost,
                        "cart_item_id": existing_item["cart_item_id"],
                    },
                )
                logger.info(f"Updated cart_item_id={existing_item['cart_item_id']} with quantity={cart_item.quantity}.")
            else:
                # Insert new cart item
                insert_cart_item_query = """
                    INSERT INTO cart_items (cart_id, potion_id, quantity, price, line_item_total, timestamp)
                    VALUES (:cart_id, :potion_id, :quantity, :price, :line_item_total, NOW())
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
            # Get current in-game day and hour
            query_game_time = """
                SELECT in_game_day, in_game_hour
                FROM in_game_time
                ORDER BY created_at DESC
                LIMIT 1;
            """
            logger.debug(f"Executing query to fetch latest in-game time: {query_game_time.strip()}")
            result = connection.execute(sqlalchemy.text(query_game_time))
            row = result.mappings().fetchone()
            if row:
                current_in_game_day = row['in_game_day']
                current_in_game_hour = row['in_game_hour']
            else:
                logger.error("No in-game time found in database.")
                raise ValueError("No in-game time found in database.")

            # Fetch cart details
            fetch_cart_query = """
                SELECT ca.checked_out
                FROM carts ca
                WHERE ca.cart_id = :cart_id
                LIMIT 1;
            """
            result = connection.execute(sqlalchemy.text(fetch_cart_query), {"cart_id": cart_id})
            cart = result.mappings().fetchone()

            if not cart:
                logger.error(f"Cart with cart_id={cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart["checked_out"]:
                logger.error(f"Cart with cart_id={cart_id} has already been checked out.")
                raise HTTPException(status_code=400, detail="Cart has already been checked out.")

            # Fetch cart items
            fetch_cart_items_query = """
                SELECT ci.cart_item_id, ci.potion_id, ci.quantity, p.price 
                FROM cart_items ci
                JOIN potions p ON ci.potion_id = p.potion_id
                WHERE ci.cart_id = :cart_id;
            """
            result = connection.execute(sqlalchemy.text(fetch_cart_items_query), {"cart_id": cart_id})
            cart_items = result.mappings().fetchall()

            if not cart_items:
                logger.error(f"No items found in cart_id={cart_id}.")
                raise HTTPException(status_code=400, detail="Cart is empty.")

            total_potions_bought = 0
            total_gold_paid = 0

            # Process each cart item
            for item in cart_items:
                cart_item_id = item['cart_item_id']
                potion_id = item['potion_id']
                quantity = item['quantity']
                price = item['price']
                line_item_total = quantity * price

                # Update cart_items with price, line_item_total, in_game_day, in_game_hour
                update_cart_item_query = """
                    UPDATE cart_items
                    SET price = :price,
                        line_item_total = :line_item_total,
                        in_game_day = :in_game_day,
                        in_game_hour = :in_game_hour
                    WHERE cart_item_id = :cart_item_id;
                """
                connection.execute(
                    sqlalchemy.text(update_cart_item_query),
                    {
                        "price": price,
                        "line_item_total": line_item_total,
                        "in_game_day": current_in_game_day,
                        "in_game_hour": current_in_game_hour,
                        "cart_item_id": cart_item_id
                    }
                )

                total_potions_bought += quantity
                total_gold_paid += line_item_total

                # Deduct potions from inventory
                update_potion_query = """
                    UPDATE potions
                    SET current_quantity = current_quantity - :quantity
                    WHERE potion_id = :potion_id;
                """
                connection.execute(
                    sqlalchemy.text(update_potion_query),
                    {
                        "quantity": quantity,
                        "potion_id": potion_id
                    }
                )
                logger.debug(f"Processed cart item {cart_item_id} for potion {potion_id}")

            # Update cart as checked out
            update_cart_query = """
                UPDATE carts
                SET checked_out = TRUE,
                    checked_out_at = NOW(),
                    total_potions_bought = :total_potions_bought,
                    total_gold_paid = :total_gold_paid,
                    payment = :payment
                WHERE cart_id = :cart_id;
            """
            connection.execute(
                sqlalchemy.text(update_cart_query),
                {
                    "total_potions_bought": total_potions_bought,
                    "total_gold_paid": total_gold_paid,
                    "payment": cart_checkout.payment,
                    "cart_id": cart_id
                }
            )

            # Update global inventory
            update_global_inventory_query = """
                UPDATE global_inventory
                SET gold = gold + :total_gold_paid,
                    total_potions = total_potions - :total_potions_bought
                WHERE id = 1;
            """
            connection.execute(
                sqlalchemy.text(update_global_inventory_query),
                {
                    "total_gold_paid": total_gold_paid,
                    "total_potions_bought": total_potions_bought
                }
            )

            logger.info(f"Cart {cart_id} checked out successfully. Total potions: {total_potions_bought}, Total gold: {total_gold_paid}")

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
