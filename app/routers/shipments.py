from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import shipment as shipment_crud
from app.database import get_db
from app.schemas.shipment import (
    ShipmentCreate,
    ShipmentDetail,
    ShipmentRead,
    ShipmentUpdate,
)

router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("/", response_model=list[ShipmentRead])
async def list_shipments(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await shipment_crud.get_shipments(db, skip=skip, limit=limit)


@router.get("/{shipment_id}", response_model=ShipmentDetail)
async def get_shipment(shipment_id: UUID, db=Depends(get_db)):
    shipment = await shipment_crud.get_shipment(db, shipment_id)
    if not shipment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return shipment


@router.get("/order/{order_id}", response_model=ShipmentDetail)
async def get_shipment_by_order(order_id: UUID, db=Depends(get_db)):
    shipment = await shipment_crud.get_shipment_by_order_id(db, order_id)
    if not shipment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No shipment found for this order",
        )
    return shipment


@router.post("/", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
async def create_shipment(shipment: ShipmentCreate, db=Depends(get_db)):
    return await shipment_crud.create_shipment(db, shipment)


@router.put("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(shipment_id: UUID, shipment: ShipmentUpdate, db=Depends(get_db)):
    updated = await shipment_crud.update_shipment(db, shipment_id, shipment)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
    return updated


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(shipment_id: UUID, db=Depends(get_db)):
    deleted = await shipment_crud.delete_shipment(db, shipment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shipment not found")
