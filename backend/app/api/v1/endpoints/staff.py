from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.staff import Staff
from app.models.user import User, UserRole

router = APIRouter()


@router.get("/")
async def list_staff(
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Staff).where(Staff.is_deleted == False)
    if branch_id:
        query = query.where(Staff.branch_id == branch_id)
    result = await db.execute(query)
    return result.scalars().all()
