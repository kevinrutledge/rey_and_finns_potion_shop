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

class Barrel(BaseModel):
    sku: str
    ml_per_barrel: int
    potion_type: list[int]
    price: int
    quantity: int

    @validator('ml_per_barrel', 'price', 'quantity')
    def values_must_be_positive(cls, field_value, field):
        if field_value < 0:
            raise ValueError(f'{field.name} must be non-negative')
        return field_value

@router.post("/deliver/{order_id}", summary="Deliver Barrels", description="Process delivery of barrels.")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """
    Process delivery of barrels to inventory.
    """
    logger.debug("Barrels/deliver - in")
    logger.debug(f"Barrels delivered: {barrels_delivered}")
    logger.debug(f"Order Id: {order_id}")

    total_ml_added = 0
    total_gold_spent = 0

    try:
        with db.engine.begin() as connection:
            # Fetch current gold
            sql_fetch_gold = sqlalchemy.text("SELECT gold FROM global_inventory;")
            result = connection.execute(sql_fetch_gold)
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            current_gold = row['gold']
            logger.debug(f"Current Gold: {current_gold}")

            for barrel in barrels_delivered:
                if len(barrel.potion_type) != 4:
                    logger.error(f"Invalid potion_type length for SKU {barrel.sku}.")
                    raise HTTPException(status_code=400, detail=f"Invalid potion_type for SKU {barrel.sku}.")

                # Example handling for green potions; generalize as needed
                if barrel.potion_type == [0, 1, 0, 0]:
                    ml_added = barrel.ml_per_barrel * barrel.quantity
                    gold_spent = barrel.price * barrel.quantity

                    # Check if sufficient gold
                    if current_gold < gold_spent:
                        logger.error(f"Insufficient gold for purchasing {barrel.quantity} of {barrel.sku}. Required: {gold_spent}, Available: {current_gold}")
                        raise HTTPException(status_code=400, detail="Insufficient gold for purchase.")

                    # Update volume in global_inventory
                    sql_update_ml = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET num_green_ml = num_green_ml + :ml_added
                    """)
                    connection.execute(sql_update_ml, {'ml_added': ml_added})
                    logger.debug(f"Updated ML: Added {ml_added} ml to inventory for {barrel.sku}.")

                    # Update gold in global_inventory
                    sql_update_gold = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET gold = gold - :gold_spent
                    """)
                    connection.execute(sql_update_gold, {'gold_spent': gold_spent})
                    logger.debug(f"Updated Gold: Subtracted {gold_spent} gold for {barrel.sku}.")

                    # Accumulate totals
                    total_ml_added += ml_added
                    total_gold_spent += gold_spent

                    # Update current_gold
                    current_gold -= gold_spent

            logger.debug("Barrels/deliver - out")
            logger.debug(f"Total ML Added: {total_ml_added}")
            logger.debug(f"Total Gold Spent: {total_gold_spent}")

        return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during barrels/deliver")
        raise HTTPException(status_code=500, detail="Database error.")
    except HTTPException as he:
        # Re-raise HTTPExceptions to be handled by FastAPI
        raise he
    except Exception as e:
        logger.exception("Unexpected error during barrels/deliver")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

# Gets called once a day
@router.post("/plan", summary="Get Wholesale Purchase Plan", description="Generates purchase plan based on wholesale catalog.")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Generates wholesale purchase plan based on current inventory.
    """
    logger.debug("barrles/plan - in")
    logger.debug(f"Wholesale catalog: {wholesale_catalog}")

    try:
        with db.engine.begin() as connection:
            # Fetch both num_green_potions and gold from global_inventory
            sql_statement_select = """
                SELECT num_green_potions, gold 
                FROM global_inventory;
            """
            result = connection.execute(sqlalchemy.text(sql_statement_select))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            current_gold = row['gold']
            logger.debug(f"Number of Green Potions: {num_green_potions}")
            logger.debug(f"Current Gold: {current_gold}")

        purchase_plan = []

        # Check if num_green_potions is less than 10 and gold is greater than 100
        if num_green_potions < 10 and current_gold >= 100:
            for barrel in wholesale_catalog:
                if barrel.sku == "SMALL_GREEN_BARREL":
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    logger.debug(f"Added {barrel.sku} to purchase plan.")
                    break  # Assuming only one Small Green Barrel is needed

        logger.debug("barrels/plan - out")
        logger.debug(f"Purchase plan: {purchase_plan}")

        return purchase_plan

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during barrels/plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception as e:
        logger.exception("Unexpected error during barrels/plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
