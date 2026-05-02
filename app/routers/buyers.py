from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import buyer as buyer_crud
from app.database import get_db
from app.schemas.buyer import BuyerCreate, BuyerDetail, BuyerRead, BuyerUpdate

router = APIRouter(prefix="/buyers", tags=["buyers"])


@router.get("/", response_model=list[BuyerRead])
async def list_buyers(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await buyer_crud.get_buyers(db, skip=skip, limit=limit)


@router.get("/{buyer_id}", response_model=BuyerDetail)
async def get_buyer(buyer_id: UUID, db=Depends(get_db)):
    buyer = await buyer_crud.get_buyer(db, buyer_id)
    if not buyer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer not found")
    return buyer


@router.post("/", response_model=BuyerRead, status_code=status.HTTP_201_CREATED)
async def create_buyer(buyer: BuyerCreate, db=Depends(get_db)):
    return await buyer_crud.create_buyer(db, buyer)


@router.put("/{buyer_id}", response_model=BuyerRead)
async def update_buyer(buyer_id: UUID, buyer: BuyerUpdate, db=Depends(get_db)):
    updated = await buyer_crud.update_buyer(db, buyer_id, buyer)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer not found")
    return updated


@router.delete("/{buyer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_buyer(buyer_id: UUID, db=Depends(get_db)):
    deleted = await buyer_crud.delete_buyer(db, buyer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Buyer not found")
