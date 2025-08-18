from fastapi import APIRouter
from fastapi import Query, Depends
from sqlalchemy.orm import Session
from app.database import get_db_session
from app.database.models.price_models import PriceHistoryModel
from app.schemas.price_schemas import PriceHistoryResponse, PriceHistory

router = APIRouter()

@router.get("/")
async def get_price_data(
    limit: int = Query(50, ge=1, le=1000, description="Number of price entries to return"),
    db: Session = Depends(get_db_session)
):
    prices = (
        db.query(PriceHistoryModel)
        .order_by(PriceHistoryModel.timestamp.desc())
        .limit(limit)
        .all()
    )

    return [PriceHistoryResponse(price=PriceHistory.from_orm(price)) for price in prices]
