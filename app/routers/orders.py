from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import order as order_crud
from app.database import get_db
from app.schemas.order import OrderCreate, OrderDetail, OrderRead, OrderUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("/", response_model=list[OrderRead])
async def list_orders(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await order_crud.get_orders(db, skip=skip, limit=limit)


@router.get("/{order_id}", response_model=OrderDetail)
async def get_order(order_id: UUID, db=Depends(get_db)):
    order = await order_crud.get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return order


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def create_order(order: OrderCreate, db=Depends(get_db)):
    try:
        return await order_crud.create_order(db, order)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{order_id}", response_model=OrderRead)
async def update_order(order_id: UUID, order: OrderUpdate, db=Depends(get_db)):
    updated = await order_crud.update_order(db, order_id, order)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    return updated


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(order_id: UUID, db=Depends(get_db)):
    deleted = await order_crud.delete_order(db, order_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
