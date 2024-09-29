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

    try:
        with db.engine.begin() as connection:
            for barrel in barrels_delivered:
                if barrel.potion_type == [0, 1, 0, 0]:
                    ml_added = barrel.ml_per_barrel * barrel.quantity
                    gold_spent = barrel.price * barrel.quantity

                    # Update volume in global_inventory
                    sql_statement_ml = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET num_green_ml = num_green_ml + :ml_added
                    """)
                    connection.execute(sql_statement_ml, {'ml_added': ml_added})
                    logger.debug(f"Updated ML: Added {ml_added} ml to inventory.")

                    # Update gold in global_inventory
                    sql_statement_gold = sqlalchemy.text("""
                        UPDATE global_inventory
                        SET gold = gold - :gold_spent
                    """)
                    connection.execute(sql_statement_gold, {'gold_spent': gold_spent})
                    logger.debug(f"Updated Gold: Subtracted {gold_spent} gold from inventory.")

            logger.debug("Barrels/deliver - out")
            logger.debug(f"Total Volume Added: {ml_added if 'ml_added' in locals() else 0}")
            logger.debug(f"Total Gold Spent: {gold_spent if 'gold_spent' in locals() else 0}")

        return {"status": "OK"}

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during barrels/deliver")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception as e:
        logger.exception("Unexpected error during barrels/deliver")
        raise HTTPException(status_code=500, detail="Internal Server Error.")

# Gets called once a day
@router.post("/plan", summary="Get Wholesale Purchase Plan", description="Generates a purchase plan based on wholesale catalog.")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """
    Generates wholesale purchase plan based on current inventory.
    """
    logger.debug("barrles/plan - in")
    logger.debug(f"Wholesale catalog: {wholesale_catalog}")

    try:
        with db.engine.begin() as connection:
            result = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory;"))
            row = result.mappings().one_or_none()

            if row is None:
                logger.error("No inventory record found.")
                raise HTTPException(status_code=500, detail="Inventory record not found.")

            num_green_potions = row['num_green_potions']
            logger.debug(f"Number of Green Potions: {num_green_potions}")

        purchase_plan = []

        if num_green_potions < 10:
            for barrel in wholesale_catalog:
                if barrel.sku == "SMALL_GREEN_BARREL":
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1
                    })
                    logger.debug(f"Added {barrel.sku} to purchase plan.")
                    break

        logger.debug("barrels/plan - out")
        logger.debug(f"Purchase plan: {purchase_plan}")

        return purchase_plan

    except sqlalchemy.exc.SQLAlchemyError as db_err:
        logger.exception("Database error during barrels/plan")
        raise HTTPException(status_code=500, detail="Database error.")
    except Exception as e:
        logger.exception("Unexpected error during barrels/plan")
        raise HTTPException(status_code=500, detail="Internal Server Error.")
