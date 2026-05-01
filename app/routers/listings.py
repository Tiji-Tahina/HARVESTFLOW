from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import listing as listing_crud
from app.database import get_db
from app.schemas.listing import ListingCreate, ListingDetail, ListingRead, ListingUpdate

router = APIRouter(prefix="/listings", tags=["listings"])


@router.get("/", response_model=list[ListingRead])
async def list_listings(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await listing_crud.get_listings(db, skip=skip, limit=limit)


@router.get("/{listing_id}", response_model=ListingDetail)
async def get_listing(listing_id: UUID, db=Depends(get_db)):
    listing = await listing_crud.get_listing(db, listing_id)
    if not listing:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return listing


@router.post("/", response_model=ListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(listing: ListingCreate, db=Depends(get_db)):
    return await listing_crud.create_listing(db, listing)


@router.put("/{listing_id}", response_model=ListingRead)
async def update_listing(listing_id: UUID, listing: ListingUpdate, db=Depends(get_db)):
    updated = await listing_crud.update_listing(db, listing_id, listing)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    return updated


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(listing_id: UUID, db=Depends(get_db)):
    deleted = await listing_crud.delete_listing(db, listing_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
