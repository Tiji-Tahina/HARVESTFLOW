from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.crud import product as product_crud
from app.database import get_db
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=list[ProductRead])
async def list_products(skip: int = 0, limit: int = 100, db=Depends(get_db)):
    return await product_crud.get_products(db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: UUID, db=Depends(get_db)):
    product = await product_crud.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db=Depends(get_db)):
    return await product_crud.create_product(db, product)


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(product_id: UUID, product: ProductUpdate, db=Depends(get_db)):
    updated = await product_crud.update_product(db, product_id, product)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return updated


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: UUID, db=Depends(get_db)):
    deleted = await product_crud.delete_product(db, product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
