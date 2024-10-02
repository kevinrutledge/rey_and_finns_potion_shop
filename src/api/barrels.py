import sqlalchemy
import logging
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator
from src.api import auth

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

# Mapping of potion mixtures to their categories
POTION_CATEGORIES = {
    (50, 0, 50, 0): 'purple',
    (50, 50, 0, 0): 'yellow',
    # TODO: Add more mixtures as needed
}

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

    def validate_fields(cls, values):
        ml_per_barrel = values.get('ml_per_barrel')
        price = values.get('price')
        quantity = values.get('quantity')
        potion_type = values.get('potion_type')

        for field_name, field_value in [('ml_per_barrel', ml_per_barrel), ('price', price), ('quantity', quantity)]:
            if field_value < 0:
                raise ValueError(f"{field_name} must be non-negative.")
        if len(potion_type) != 4:
            raise ValueError("potion_type must have exactly four elements.")

        return values


@router.post("/deliver/{order_id}", summary="Deliver Barrels", description="Process delivery of barrels.")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """
    Process delivery of barrels to inventory.
    """
    logger.debug(f"Initiating barrel delivery for order_id: {order_id} with barrels: {barrels_delivered}")

    try:
        with db.engine.begin() as connection:
            # Fetch current gold from inventory
            sql_select_gold = "SELECT gold FROM global_inventory;"
            result = connection.execute(sqlalchemy.text(sql_select_gold))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            current_gold = row['gold']
            logger.debug(f"Current gold before purchase: {current_gold}")

            total_ml_added = 0
            total_gold_spent = 0

            for barrel in barrels_delivered:
                # Determine potion category based on potion_type
                potion_key = tuple(barrel.potion_type)
                potion_category = POTION_CATEGORIES.get(potion_key)

                if potion_category is None:
                    logger.error(f"Unsupported potion mixture {barrel.potion_type} for SKU {barrel.sku}.")
                    raise HTTPException(status_code=400, detail=f"Unsupported potion mixture for SKU {barrel.sku}.")

                ml_added = barrel.ml_per_barrel * barrel.quantity
                gold_spent = barrel.price * barrel.quantity

                logger.debug(f"Barrel SKU: {barrel.sku}, Potion Category: {potion_category}, ML Added: {ml_added}, Gold Spent: {gold_spent}")

                # Check if sufficient gold is available
                if current_gold < gold_spent:
                    logger.error(f"Insufficient gold for purchasing {barrel.quantity} of {barrel.sku}. Required: {gold_spent}, Available: {current_gold}")
                    raise HTTPException(status_code=400, detail="Insufficient gold for purchase.")

                # Update ML in global_inventory
                sql_update_ml = sqlalchemy.text(f"""
                    UPDATE global_inventory
                    SET num_{potion_category}_ml = num_{potion_category}_ml + :ml_added
                """)
                connection.execute(sql_update_ml, {'ml_added': ml_added})
                logger.debug(f"Added {ml_added} ml to {potion_category} inventory.")

                # Update gold in global_inventory
                sql_update_gold = sqlalchemy.text("""
                    UPDATE global_inventory
                    SET gold = gold - :gold_spent
                """)
                connection.execute(sql_update_gold, {'gold_spent': gold_spent})
                logger.debug(f"Subtracted {gold_spent} gold from inventory.")

                # Accumulate totals
                total_ml_added += ml_added
                total_gold_spent += gold_spent

                # Update current_gold for subsequent iterations
                current_gold -= gold_spent

            logger.info(f"Successfully processed barrel delivery for order_id: {order_id}. Total ML Added: {total_ml_added}, Total Gold Spent: {total_gold_spent}")

        return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception(f"Database error during post_deliver_barrels for order_id: {order_id}")
        raise HTTPException(status_code=500, detail="Database error.")
    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise he
    except Exception:
        logger.exception(f"Unexpected error during post_deliver_barrels for order_id: {order_id}")
        raise HTTPException(status_code=500, detail="Internal Server Error.")


# Gets called once a day
@router.post("/plan", summary="Get Wholesale Purchase Plan", description="Generates purchase plan based on wholesale catalog.")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Generates wholesale purchase plan based on current inventory.
    """
    logger.debug(f"Generating wholesale purchase plan with catalog: {wholesale_catalog}")

    try:
        with db.engine.begin() as connection:
            # Fetch current inventory
            sql_select = """
                SELECT num_green_potions, gold 
                FROM global_inventory;
            """
            result = connection.execute(sqlalchemy.text(sql_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found in global_inventory table.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            current_gold = row['gold']
            logger.debug(f"Current inventory - Green Potions: {num_green_potions}, Gold: {current_gold}")

        purchase_plan = []

        # TODO: Make SQL tables for daily/weekly trends

        for barrel in wholesale_catalog:
            if barrel.sku == "SMALL_GREEN_BARREL":
                required_gold = barrel.price * barrel.quantity
                if num_green_potions < 10 and current_gold >= required_gold:
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    logger.debug(f"Added {barrel.sku} to purchase plan.")
                    break  # Assuming only one Small Green Barrel is needed

        logger.info(f"Wholesale purchase plan generated: {purchase_plan}")

        return purchase_plan

    except sqlalchemy.exc.SQLAlchemyError:
        logger.exception("Database error during get_wholesale_purchase_plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception:
        logger.exception("Unexpected error during get_wholesale_purchase_plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
