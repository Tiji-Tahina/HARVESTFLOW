from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import transporter as transporter_crud
from app.database import get_db
from app.schemas.transporter import (
    TransporterCreate,
    TransporterRead,
    TransporterUpdate,
)

router = APIRouter(prefix="/transporters", tags=["transporters"])


@router.get("/", response_model=list[TransporterRead])
async def list_transporters(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await transporter_crud.get_transporters(db, skip=skip, limit=limit)


@router.get("/{transporter_id}", response_model=TransporterRead)
async def get_transporter(transporter_id: UUID, db=Depends(get_db)):
    transporter = await transporter_crud.get_transporter(db, transporter_id)
    if not transporter:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transporter not found")
    return transporter


@router.post("/", response_model=TransporterRead, status_code=status.HTTP_201_CREATED)
async def create_transporter(transporter: TransporterCreate, db=Depends(get_db)):
    return await transporter_crud.create_transporter(db, transporter)


@router.put("/{transporter_id}", response_model=TransporterRead)
async def update_transporter(
    transporter_id: UUID, transporter: TransporterUpdate, db=Depends(get_db)
):
    updated = await transporter_crud.update_transporter(db, transporter_id, transporter)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transporter not found")
    return updated


@router.delete("/{transporter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transporter(transporter_id: UUID, db=Depends(get_db)):
    deleted = await transporter_crud.delete_transporter(db, transporter_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transporter not found")
