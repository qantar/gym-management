from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.branch import Branch
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/")
async def list_branches(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Branch).where(Branch.is_deleted == False))
    return result.scalars().all()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_branch(
    payload: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.SUPER_ADMIN, UserRole.OWNER)),
):
    branch = Branch(**payload)
    db.add(branch)
    await db.commit()
    await db.refresh(branch)
    return branch
