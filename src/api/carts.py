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
    logger.info("Starting search_orders endpoint.")
    logger.debug(f"Received parameters - customer_name: '{customer_name}', potion_sku: '{potion_sku}', search_page: {search_page}, sort_col: '{sort_col}', sort_order: '{sort_order}'")
    try:
        with db.engine.begin() as connection:
            # Build base query
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

            # Filters
            filters = []
            params = {}
            if customer_name:
                filters.append(sqlalchemy.text("c.customer_name ILIKE :customer_name"))
                params['customer_name'] = f"%{customer_name}%"
            if potion_sku:
                filters.append(sqlalchemy.text("p.sku ILIKE :potion_sku"))
                params['potion_sku'] = f"%{potion_sku}%"
            if filters:
                base_query = base_query.where(and_(*filters))
                logger.debug(f"Applied filters: {filters}")

            # Sorting
            sort_column_map = {
                'customer_name': 'c.customer_name',
                'item_sku': 'p.sku',
                'line_item_total': 'ci.line_item_total',
                'timestamp': 'c.created_at'
            }
            sort_column = sort_column_map.get(sort_col.value, 'c.created_at')
            order_direction = asc if sort_order == 'asc' else desc
            base_query = base_query.order_by(order_direction(text(sort_column)))
            logger.debug(f"Sorting by {sort_column} in {sort_order} order")

            # Pagination
            page_size = 5
            offset = (search_page - 1) * page_size
            base_query = base_query.offset(offset).limit(page_size + 1)
            logger.debug(f"Pagination - page_size: {page_size}, offset: {offset}")

            # Execute query
            result = connection.execute(base_query, params)
            items = result.mappings().fetchall()
            logger.debug(f"Query returned {len(items)} items (including one extra for pagination check)")

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

            logger.info(f"Search returned {len(results)} results.")
            logger.debug(f"Response: {response}")
            logger.info("Ending search_orders endpoint.")
            return response

    except Exception as e:
        logger.error(f"Error in search_orders: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    logger.info(f"Starting post_visits endpoint for visit_id {visit_id}.")
    logger.debug(f"Received customers: {[customer.dict() for customer in customers]}")
    for customer in customers:
        logger.info(f"Customer visited: {customer.customer_name}, Class: {customer.character_class}, Level: {customer.level}")
    logger.info("Ending post_visits endpoint.")
    return {"success": True}


@router.post("/")
def create_cart(new_cart: Customer):
    """
    Create new cart for customer.
    """
    logger.info(f"Starting create_cart endpoint for customer {new_cart.customer_name}.")
    logger.debug(f"Received new_cart data: {new_cart.dict()}")
    try:
        with db.engine.begin() as connection:
            # Insert new cart into carts table
            result = connection.execute(
                sqlalchemy.text(
                    """
                    INSERT INTO carts (customer_name, character_class, level, checked_out, created_at)
                    VALUES (:customer_name, :character_class, :level, FALSE, :created_at)
                    RETURNING cart_id;
                    """
                ),
                {
                    'customer_name': new_cart.customer_name,
                    'character_class': new_cart.character_class,
                    'level': new_cart.level,
                    'created_at': datetime.utcnow()
                }
            )
            cart_id_row = result.mappings().fetchone()
            if cart_id_row is None:
                logger.error("Failed to create cart.")
                raise HTTPException(status_code=500, detail="Failed to create cart.")
            cart_id = cart_id_row['cart_id']
            logger.info(f"Created cart with cart_id {cart_id} for customer {new_cart.customer_name}.")
            logger.debug(f"Returning cart_id: {cart_id}")
            logger.info("Ending create_cart endpoint.")
            return {"cart_id": cart_id}
    except Exception as e:
        logger.error(f"Error in create_cart: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """
    Add or update item quantity in cart.
    """
    logger.info(f"Starting set_item_quantity endpoint for cart_id {cart_id}, item_sku {item_sku}.")
    logger.debug(f"Received cart_item data: {cart_item.dict()}")
    try:
        with db.engine.begin() as connection:
            # Check if cart exists and is not checked out
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT checked_out FROM carts WHERE cart_id = :cart_id;"
                ),
                {'cart_id': cart_id}
            )
            cart_row = result.mappings().fetchone()
            if cart_row is None:
                logger.error(f"Cart {cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart_row['checked_out']:
                logger.error(f"Cart {cart_id} is already checked out.")
                raise HTTPException(status_code=400, detail="Cart is already checked out.")

            # Get potion_id from item_sku
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT potion_id, price FROM potions WHERE sku = :sku;"
                ),
                {'sku': item_sku}
            )
            potion_row = result.mappings().fetchone()
            if potion_row is None:
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
            if cart_item_row is not None:
                logger.debug(f"Cart item exists, updating cart_item_id: {cart_item_row['cart_item_id']}")
                # Update existing cart item
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
                logger.debug("Cart item does not exist, inserting new cart item.")
                # Insert new cart item
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

            logger.info("Ending set_item_quantity endpoint.")
            logger.debug("Returning success response: {'success': True}")
            return {"success": True}
    except HTTPException as e:
        # Re-raise HTTPExceptions
        logger.error(f"HTTPException in set_item_quantity: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error in set_item_quantity: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """
    Checkout cart.
    """
    logger.info(f"Starting checkout endpoint for cart_id {cart_id}.")
    logger.debug(f"Received cart_checkout data: {cart_checkout.dict()}")
    try:
        with db.engine.begin() as connection:
            # Check if cart exists and is not checked out
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT checked_out FROM carts WHERE cart_id = :cart_id;"
                ),
                {'cart_id': cart_id}
            )
            cart_row = result.mappings().fetchone()
            if cart_row is None:
                logger.error(f"Cart {cart_id} does not exist.")
                raise HTTPException(status_code=404, detail="Cart not found.")
            if cart_row['checked_out']:
                logger.error(f"Cart {cart_id} is already checked out.")
                raise HTTPException(status_code=400, detail="Cart is already checked out.")

            # Get cart items
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
            if not cart_items:
                logger.error(f"No items in cart {cart_id} to checkout.")
                raise HTTPException(status_code=400, detail="Cart is empty.")
            logger.debug(f"Retrieved {len(cart_items)} cart items.")

            total_potions_bought = 0
            total_gold_paid = 0

            # Check stock availability and compute totals
            for item in cart_items:
                logger.debug(f"Processing cart item: {dict(item)}")
                if item['quantity'] > item['potion_stock']:
                    logger.error(f"Not enough stock for potion_id {item['potion_id']}. Requested {item['quantity']}, available {item['potion_stock']}.")
                    raise HTTPException(status_code=400, detail=f"Not enough stock for item {item['potion_id']}.")
                total_potions_bought += item['quantity']
                total_gold_paid += item['line_item_total']

            logger.debug(f"Total potions bought: {total_potions_bought}, Total gold paid: {total_gold_paid}")

            # Update potions stock
            for item in cart_items:
                new_quantity = item['potion_stock'] - item['quantity']
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
            result = connection.execute(
                sqlalchemy.text(
                    "SELECT gold FROM global_inventory WHERE id = 1;"
                )
            )
            global_row = result.mappings().fetchone()
            if global_row is None:
                logger.error("Global inventory record not found.")
                raise HTTPException(status_code=500, detail="Global inventory record not found.")
            gold = global_row['gold']
            new_gold = gold + total_gold_paid
            connection.execute(
                sqlalchemy.text(
                    "UPDATE global_inventory SET gold = :new_gold WHERE id = 1;"
                ),
                {'new_gold': new_gold}
            )
            logger.info(f"Updated gold in global inventory to {new_gold}.")

            # Mark cart as checked out and update totals
            connection.execute(
                sqlalchemy.text(
                    """
                    UPDATE carts
                    SET checked_out = TRUE,
                        total_potions_bought = :total_potions_bought,
                        total_gold_paid = :total_gold_paid
                    WHERE cart_id = :cart_id;
                    """
                ),
                {
                    'total_potions_bought': total_potions_bought,
                    'total_gold_paid': total_gold_paid,
                    'cart_id': cart_id
                }
            )
            logger.info(f"Checked out cart {cart_id}.")

            logger.info("Ending checkout endpoint.")
            logger.debug(f"Returning checkout response: {{'total_potions_bought': {total_potions_bought}, 'total_gold_paid': {total_gold_paid}}}")
            return {"total_potions_bought": total_potions_bought, "total_gold_paid": total_gold_paid}
    except HTTPException as e:
        # Re-raise HTTPExceptions
        logger.error(f"HTTPException in checkout: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"Error in checkout: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
