import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from enum import Enum
from datetime import datetime

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
    try:
        with db.engine.begin() as connection:
            # Build base query
            logger.debug("Building base SQL query for searching orders.")
            base_query = sqlalchemy.select(
                [
                    sqlalchemy.column('ci.cart_item_id').label('line_item_id'),
                    sqlalchemy.column('p.sku').label('item_sku'),
                    sqlalchemy.column('c.customer_name'),
                    sqlalchemy.column('ci.line_item_total'),
                    sqlalchemy.column('c.created_at').label('timestamp')
                ]
            ).select_from(
                sqlalchemy.text('cart_items ci')
                .join('carts c', 'ci.cart_id = c.cart_id')
                .join('potions p', 'ci.potion_id = p.potion_id')
            ).where(
                sqlalchemy.text('c.checked_out = TRUE')
            )

            # Apply filters if provided
            filters = []
            params = {}
            if customer_name:
                filters.append(sqlalchemy.text("c.customer_name ILIKE :customer_name"))
                params['customer_name'] = f"%{customer_name}%"
            if potion_sku:
                filters.append(sqlalchemy.text("p.sku ILIKE :potion_sku"))
                params['potion_sku'] = f"%{potion_sku}%"
            if filters:
                logger.debug(f"Applying filters: {filters}")
                base_query = base_query.where(sqlalchemy.and_(*filters))

            # Apply sorting
            sort_column_map = {
                'customer_name': 'c.customer_name',
                'item_sku': 'p.sku',
                'line_item_total': 'ci.line_item_total',
                'timestamp': 'c.created_at'
            }
            sort_column = sort_column_map.get(sort_col.value, 'c.created_at')
            order_direction = sqlalchemy.asc if sort_order == 'asc' else sqlalchemy.desc
            logger.debug(f"Applying sorting by {sort_column} in {sort_order} order.")
            base_query = base_query.order_by(order_direction(sqlalchemy.text(sort_column)))

            # Apply pagination
            page_size = 5
            offset = (search_page - 1) * page_size
            logger.debug(f"Applying pagination - page_size: {page_size}, offset: {offset}")
            base_query = base_query.offset(offset).limit(page_size + 1)  # Fetch one extra to check for next page

            # Execute query
            logger.debug("Executing SQL query.")
            result = connection.execute(base_query, params)
            items = result.mappings().fetchall()
            logger.debug(f"Query returned {len(items)} items (including one extra for pagination check).")

            # Determine previous and next page
            previous_page = search_page - 1 if search_page > 1 else None
            next_page = search_page + 1 if len(items) > page_size else None

            # Prepare results
            results = []
            for item in items[:page_size]:
                results.append({
                    'line_item_id': item['line_item_id'],
                    'item_sku': item['item_sku'],
                    'customer_name': item['customer_name'],
                    'line_item_total': item['line_item_total'],
                    'timestamp': item['timestamp'].isoformat()
                })

            # Build response
            response = {
                'previous': str(previous_page) if previous_page else "",
                'next': str(next_page) if next_page else "",
                'results': results
            }

            logger.debug(f"Prepared response: {response}")
            logger.info(f"Search completed with {len(results)} results.")
            return response

    except Exception as e:
        logger.exception(f"Unhandled exception in search_orders: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    logger.info(f"Endpoint /carts/visits/{visit_id} called.")
    logger.debug(f"Visit ID: {visit_id}, Customers: {customers}")
    try:
        with db.engine.begin() as connection:
            # Insert visit record
            logger.debug("Inserting visit record into visits table.")
            connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO visits (visit_id, visit_time)
                    VALUES (:visit_id, NOW());
                    """
                ),
                {'visit_id': visit_id}
            )
            logger.info(f"Inserted visit with visit_id {visit_id}.")

            # Insert customer records
            for customer in customers:
                logger.debug(f"Inserting customer: {customer.dict()}")
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO customers (visit_id, customer_name, character_class, level)
                        VALUES (:visit_id, :customer_name, :character_class, :level);
                        """
                    ),
                    {
                        'visit_id': visit_id,
                        'customer_name': customer.customer_name,
                        'character_class': customer.character_class,
                        'level': customer.level
                    }
                )
                logger.info(f"Inserted customer {customer.customer_name} for visit_id {visit_id}.")

        logger.info("All customers for visit have been recorded successfully.")
        return {"success": True}

    except sqlalchemy.exc.IntegrityError as e:
        logger.exception(f"IntegrityError in post_visits: {e}")
        raise HTTPException(status_code=400, detail="Visit ID already exists.")
    except Exception as e:
        logger.exception(f"Unhandled exception in post_visits: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/")
def create_cart(new_cart: Customer):
    """
    Create new cart for customer.
    """
    logger.info(f"Endpoint /carts/ called to create new cart for customer: {new_cart.customer_name}")
    logger.debug(f"Customer Details: {new_cart.dict()}")
    try:
        with db.engine.begin() as connection:
            # Find customer_id based on customer details
            logger.debug("Retrieving customer_id from customers table.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT customer_id FROM customers
                    WHERE customer_name = :customer_name
                    AND character_class = :character_class
                    AND level = :level
                    """
                ),
                {
                    'customer_name': new_cart.customer_name,
                    'character_class': new_cart.character_class,
                    'level': new_cart.level
                }
            )
            customer_row = result.mappings().fetchone()
            if not customer_row:
                logger.error("Customer not found in current visit.")
                raise HTTPException(status_code=404, detail="Customer not found in current visit.")
            customer_id = customer_row['customer_id']
            logger.debug(f"Retrieved customer_id: {customer_id}")

            # Insert new cart into carts table linked to customer_id
            logger.debug("Inserting new cart into carts table.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO carts (customer_id, checked_out, created_at)
                    VALUES (:customer_id, FALSE, :created_at)
                    RETURNING cart_id;
                    """
                ),
                {
                    'customer_id': customer_id,
                    'created_at': datetime.utcnow()
                }
            )
            cart_id_row = result.mappings().fetchone()
            if not cart_id_row:
                logger.error("Failed to create cart.")
                raise HTTPException(status_code=500, detail="Failed to create cart.")
            cart_id = cart_id_row['cart_id']
            logger.info(f"Created cart with cart_id {cart_id} for customer_id {customer_id}.")

            logger.debug(f"Returning cart_id: {cart_id}")
            return {"cart_id": cart_id}

    except HTTPException as e:
        logger.error(f"HTTPException in create_cart: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in create_cart: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Add or update item quantity in cart.
    """
    logger.info(f"Endpoint /carts/{cart_id}/items/{item_sku} called to set item quantity.")
    logger.debug(f"Cart ID: {cart_id}, Item SKU: {item_sku}, Cart Item Details: {cart_item.dict()}")
    try:
        with db.engine.begin() as connection:
            # Check if cart exists and is not checked out
            logger.debug("Verifying cart existence and checkout status.")
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT checked_out FROM carts WHERE cart_id = :cart_id;"
                ),
                {'cart_id': cart_id}
            )
            cart_row = result.mappings().fetchone()
            if not cart_row:
                logger.error(f"Cart {cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart_row['checked_out']:
                logger.error(f"Cart {cart_id} is already checked out.")
                raise HTTPException(status_code=400, detail="Cart is already checked out.")

            # Get potion_id and price from potions table
            logger.debug("Retrieving potion_id and price from potions table.")
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT potion_id, price FROM potions WHERE sku = :sku;"
                ),
                {'sku': item_sku}
            )
            potion_row = result.mappings().fetchone()
            if not potion_row:
                logger.error(f"Potion with SKU {item_sku} does not exist.")
                raise HTTPException(status_code=404, detail="Item SKU not found.")
            potion_id = potion_row['potion_id']
            price = potion_row['price']
            logger.debug(f"Retrieved potion_id: {potion_id}, price: {price}")

            # Calculate line_item_total
            quantity = cart_item.quantity
            if quantity < 0:
                logger.error("Quantity cannot be negative.")
                raise HTTPException(status_code=400, detail="Quantity cannot be negative.")
            line_item_total = price * quantity
            logger.debug(f"Calculated line_item_total: {line_item_total}")

            # Check if item already exists in cart_items
            logger.debug("Checking if item already exists in cart_items.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT cart_item_id FROM cart_items
                    WHERE cart_id = :cart_id AND potion_id = :potion_id;
                    """
                ),
                {'cart_id': cart_id, 'potion_id': potion_id}
            )
            cart_item_row = result.mappings().fetchone()

            if cart_item_row:
                # Update existing cart item
                logger.debug(f"Cart item exists with cart_item_id: {cart_item_row['cart_item_id']}. Updating quantity.")
                connection.execute(
                    sqlalchemy.text(
                        """
                        UPDATE cart_items
                        SET quantity = :quantity, price = :price, line_item_total = :line_item_total
                        WHERE cart_item_id = :cart_item_id;
                        """
                    ),
                    {
                        'quantity': quantity,
                        'price': price,
                        'line_item_total': line_item_total,
                        'cart_item_id': cart_item_row['cart_item_id']
                    }
                )
                logger.info(f"Updated cart item in cart {cart_id} for potion {item_sku} with quantity {quantity}.")
            else:
                # Insert new cart item
                logger.debug("Cart item does not exist. Inserting new cart item.")
                connection.execute(
                    sqlalchemy.text(
                        """
                        INSERT INTO cart_items (cart_id, potion_id, quantity, price, line_item_total)
                        VALUES (:cart_id, :potion_id, :quantity, :price, :line_item_total);
                        """
                    ),
                    {
                        'cart_id': cart_id,
                        'potion_id': potion_id,
                        'quantity': quantity,
                        'price': price,
                        'line_item_total': line_item_total
                    }
                )
                logger.info(f"Added cart item to cart {cart_id} for potion {item_sku} with quantity {quantity}.")

        logger.info("Item quantity set successfully.")
        logger.debug("Returning response: {'success': True}")
        return {"success": True}

    except HTTPException as e:
        logger.error(f"HTTPException in set_item_quantity: {e.detail}")
        raise e
    except Exception as e:
        logger.exception(f"Unhandled exception in set_item_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Checkout cart.
    """
    logger.info(f"Endpoint /carts/{cart_id}/checkout called.")
    logger.debug(f"Cart ID: {cart_id}, Checkout Details: {cart_checkout.dict()}")
    try:
        with db.engine.begin() as connection:
            # Check if cart exists and is not checked out
            logger.debug("Verifying cart existence and checkout status.")
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT checked_out FROM carts WHERE cart_id = :cart_id;"
                ),
                {'cart_id': cart_id}
            )
            cart_row = result.mappings().fetchone()
            if not cart_row:
                logger.error(f"Cart {cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart_row['checked_out']:
                logger.error(f"Cart {cart_id} is already checked out.")
                raise HTTPException(status_code=400, detail="Cart is already checked out.")

            # Get cart items
            logger.debug("Retrieving cart items from cart_items table.")
            result = connection.execute(
                sqlalchemy.text(
                    """
                    SELECT ci.cart_item_id, ci.quantity, ci.price, ci.line_item_total,
                           p.potion_id, p.current_quantity AS potion_stock
                    FROM cart_items ci
                    JOIN potions p ON ci.potion_id = p.potion_id
                    WHERE ci.cart_id = :cart_id;
                    """
                ),
                {'cart_id': cart_id}
            )
            cart_items = result.mappings().fetchall()
            logger.debug(f"Retrieved {len(cart_items)} cart items.")

            if not cart_items:
                logger.error(f"No items in cart {cart_id} to checkout.")
                raise HTTPException(status_code=400, detail="Cart is empty.")

            total_potions_bought = 0
            total_gold_paid = 0

            # Check stock availability and compute totals
            for item in cart_items:
                logger.debug(f"Processing cart item: {item}")
                if item['quantity'] > item['potion_stock']:
                    logger.error(
                        f"Not enough stock for potion_id {item['potion_id']}. "
                        f"Requested: {item['quantity']}, Available: {item['potion_stock']}."
                    )
                    raise HTTPException(
                        status_code=400,
                        detail=f"Not enough stock for item {item['potion_id']}.",
                    )
                total_potions_bought += item['quantity']
                total_gold_paid += item['line_item_total']

            logger.debug(
                f"Total potions bought: {total_potions_bought}, Total gold paid: {total_gold_paid}"
            )

            # Update potions stock
            for item in cart_items:
                new_quantity = item['potion_stock'] - item['quantity']
                logger.debug(
                    f"Updating potion_id {item['potion_id']} stock to {new_quantity}."
                )
                connection.execute(
                    sqlalchemy.text(
                        """
                        UPDATE potions
                        SET current_quantity = :new_quantity
                        WHERE potion_id = :potion_id;
                        """
                    ),
                    {'new_quantity': new_quantity, 'potion_id': item['potion_id']}
                )
                logger.info(f"Updated stock for potion_id {item['potion_id']} to {new_quantity}.")

            # Update gold in global_inventory
            logger.debug("Updating gold in global_inventory.")
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT gold FROM global_inventory WHERE id = 1;"
                )
            )
            global_row = result.mappings().fetchone()
            if not global_row:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")
            gold = global_row['gold']
            new_gold = gold + total_gold_paid
            logger.debug(f"Updating gold from {gold} to {new_gold}.")
            connection.execute(
                sqlalchemy.text(
                    "UPDATE global_inventory SET gold = :new_gold WHERE id = 1;"
                ),
                {'new_gold': new_gold}
            )
            logger.info(f"Updated gold in global inventory to {new_gold}.")

            # Mark cart as checked out, update totals, and store payment method
            logger.debug("Marking cart as checked out and updating totals.")
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE carts
                    SET checked_out = TRUE,
                        total_potions_bought = :total_potions_bought,
                        total_gold_paid = :total_gold_paid,
                        payment = :payment
                    WHERE cart_id = :cart_id;
                    """
                ),
                {
                    'total_potions_bought': total_potions_bought,
                    'total_gold_paid': total_gold_paid,
                    'payment': cart_checkout.payment,
                    'cart_id': cart_id
                }
            )
            logger.info(
                f"Checked out cart {cart_id}. Total potions bought: {total_potions_bought}, "
                f"Total gold paid: {total_gold_paid}."
            )

        logger.info("Checkout completed successfully.")
        logger.debug(
            f"Returning response: {{'total_potions_bought': {total_potions_bought}, 'total_gold_paid': {total_gold_paid}}}"
        )
        return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
    
    except HTTPException as e:
        # Re-raise HTTPExceptions
        logger.error(f"HTTPException in checkout: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error in checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
