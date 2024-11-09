import sqlalchemy
import logging
import json
import base64
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from enum import Enum
from datetime import datetime
from src.api import auth
from src import database as db
from src.utilities import CartManager, TimeManager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

class CartItem(BaseModel):
    quantity: int

class CartCheckout(BaseModel):
    payment: str

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: List[Customer]):
    """Record customers visiting the shop."""
    try:
        with db.engine.begin() as conn:
            customers_dicts = [customer.dict() for customer in customers]

            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            
            CartManager.record_customer_visit(
                conn, 
                visit_id, 
                customers_dicts, 
                time_id
            )
            
            logger.info(f"Recorded visit for {len(customers)} customers")
            return {"success": True}
            
    except Exception as e:
        logger.error(f"Failed to record customer visit: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to record visit")

@router.post("/")
def create_cart(new_cart: Customer):
    """Create new cart for customer."""
    try:
        with db.engine.begin() as conn:
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            
            visit_id = conn.execute(
                sqlalchemy.text("""
                    SELECT visit_id 
                    FROM customer_visits 
                    ORDER BY created_at DESC 
                    LIMIT 1
                    """
                )
            ).scalar_one()
            
            cart_id = CartManager.create_cart(
                conn, 
                new_cart.dict(), 
                time_id,
                visit_id
            )
            
            logger.info(f"Created cart {cart_id} for customer {new_cart.customer_name}")
            return {"cart_id": cart_id}
            
    except Exception as e:
        logger.error(f"Failed to create cart: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create cart")

@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """Add or update item quantity in cart."""
    try:
        with db.engine.begin() as conn:
            cart = CartManager.validate_cart_status(conn, cart_id)
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            
            CartManager.update_cart_item(
                conn, 
                cart_id, 
                item_sku, 
                cart_item.quantity,
                time_id,
                cart['visit_id']
            )
            
            logger.info(
                f"Updated cart {cart_id} - item: {item_sku}, "
                f"quantity: {cart_item.quantity}"
            )
            return {"success": True}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update cart item: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update item")

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """Process cart checkout."""
    try:
        with db.engine.begin() as conn:
            cart = CartManager.validate_cart_status(conn, cart_id)
            current_time = TimeManager.get_current_time(conn)
            time_id = current_time['time_id']
            
            result = CartManager.process_checkout(
                conn,
                cart_id,
                cart_checkout.payment,
                time_id
            )
            
            logger.info(
                f"Completed checkout - cart: {cart_id}, "
                f"total: {result['total_gold_paid']}"
            )

            return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process checkout: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to checkout")

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
        # Determine sort column
        if sort_col is search_sort_options.customer_name:
            order_by = "cu.customer_name"
        elif sort_col is search_sort_options.item_sku:
            order_by = "p.sku"
        elif sort_col is search_sort_options.line_item_total:
            order_by = "ci.line_total"
        elif sort_col is search_sort_options.timestamp:
            order_by = "c.checked_out_at"
        else:
            raise ValueError(f"Invalid sort column: {sort_col}")

        # Build base query
        query = """
            SELECT
                ci.item_id as line_item_id,
                p.sku as item_sku,
                cu.customer_name,
                ci.line_total as line_item_total,
                c.checked_out_at as timestamp
            FROM cart_items ci
            JOIN carts c ON ci.cart_id = c.cart_id
            JOIN customers cu ON c.customer_id = cu.customer_id
            JOIN potions p ON ci.potion_id = p.potion_id
            WHERE c.checked_out = true
        """

        params = {"limit": 6}  # Get extra item for pagination check
        current_sort_order = sort_order

        # Handle pagination cursor
        if search_page:
            try:
                cursor_data = json.loads(base64.b64decode(search_page))
                cursor_value = cursor_data["cursor_value"]
                is_previous = cursor_data.get("direction") == "previous"

                # Convert timestamp string to datetime if needed
                if sort_col is search_sort_options.timestamp and cursor_value:
                    cursor_value = datetime.fromisoformat(cursor_value)

                # Adjust operator and sort order for direction
                if is_previous:
                    operator = "<" if sort_order is search_sort_order.asc else ">"
                    current_sort_order = (search_sort_order.asc 
                                        if sort_order is search_sort_order.desc 
                                        else search_sort_order.desc)
                else:
                    operator = "<" if sort_order is search_sort_order.desc else ">"

                query += f" AND {order_by} {operator} :cursor_value"
                params["cursor_value"] = cursor_value

            except Exception as e:
                logger.error(f"Invalid cursor format: {e}")
                raise HTTPException(status_code=400, detail="Invalid cursor format")

        # Add filters
        if customer_name:
            query += " AND LOWER(cu.customer_name) LIKE LOWER(:customer_name)"
            params["customer_name"] = f"%{customer_name}%"
        if potion_sku:
            query += " AND LOWER(p.sku) LIKE LOWER(:potion_sku)"
            params["potion_sku"] = f"%{potion_sku}%"

        # Add sorting
        query += f" ORDER BY {order_by} {current_sort_order.value}"
        query += " LIMIT :limit"

        # Execute query
        with db.engine.begin() as conn:
            results = list(conn.execute(
                sqlalchemy.text(query),
                params
            ).mappings().all())

        # Handle previous page order
        if search_page and cursor_data.get("direction") == "previous":
            results = results[::-1]

        # Check for next page
        has_next = len(results) > 5
        results = results[:5]

        # Format results
        formatted_results = [
            {
                "line_item_id": row["line_item_id"],
                "item_sku": row["item_sku"],
                "customer_name": row["customer_name"],
                "line_item_total": row["line_item_total"],
                "timestamp": row["timestamp"].isoformat()
            }
            for row in results
        ]

        # Generate cursors
        previous_cursor = ""
        next_cursor = ""

        if formatted_results:
            # Generate previous cursor if not at start
            if search_page or has_next:
                previous_cursor = base64.b64encode(json.dumps({
                    "cursor_value": formatted_results[0][sort_col.value],
                    "direction": "previous"
                }).encode('utf-8')).decode('utf-8')

            # Generate next cursor if more results exist
            if has_next:
                next_cursor = base64.b64encode(json.dumps({
                    "cursor_value": formatted_results[-1][sort_col.value],
                    "direction": "next"
                }).encode('utf-8')).decode('utf-8')

        return {
            "results": formatted_results,
            "previous": previous_cursor,
            "next": next_cursor
        }

    except ValueError as e:
        logger.error(f"Invalid search parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search orders")