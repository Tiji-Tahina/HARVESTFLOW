from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import farmer as farmer_crud
from app.database import get_db
from app.schemas.farmer import FarmerCreate, FarmerRead, FarmerUpdate

router = APIRouter(prefix="/farmers", tags=["farmers"])


@router.get("/", response_model=list[FarmerRead])
async def list_farmers(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await farmer_crud.get_farmers(db, skip=skip, limit=limit)


@router.get("/{farmer_id}", response_model=FarmerRead)
async def get_farmer(farmer_id: UUID, db=Depends(get_db)):
    farmer = await farmer_crud.get_farmer(db, farmer_id)
    if not farmer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return farmer


@router.post("/", response_model=FarmerRead, status_code=status.HTTP_201_CREATED)
async def create_farmer(farmer: FarmerCreate, db=Depends(get_db)):
    return await farmer_crud.create_farmer(db, farmer)


@router.put("/{farmer_id}", response_model=FarmerRead)
async def update_farmer(farmer_id: UUID, farmer: FarmerUpdate, db=Depends(get_db)):
    updated = await farmer_crud.update_farmer(db, farmer_id, farmer)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
    return updated


@router.delete("/{farmer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_farmer(farmer_id: UUID, db=Depends(get_db)):
    deleted = await farmer_crud.delete_farmer(db, farmer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")
