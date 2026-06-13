from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional
import uuid

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.member import Member, MemberStatus
from app.models.user import User
from app.schemas.member import MemberCreate, MemberUpdate, MemberResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


def generate_member_id() -> str:
    return f"M-{str(uuid.uuid4())[:8].upper()}"


@router.get("/", response_model=PaginatedResponse[MemberResponse])
async def list_members(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[MemberStatus] = None,
    branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Member).where(Member.is_deleted == False)
    if search:
        query = query.where(or_(
            Member.first_name.ilike(f"%{search}%"),
            Member.last_name.ilike(f"%{search}%"),
            Member.phone.ilike(f"%{search}%"),
            Member.member_id.ilike(f"%{search}%"),
        ))
    if status:
        query = query.where(Member.status == status)
    if branch_id:
        query = query.where(Member.branch_id == branch_id)

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar()

    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items, total=total, page=page,
        page_size=page_size, pages=(total + page_size - 1) // page_size,
    )


@router.post("/", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def create_member(
    payload: MemberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member = Member(**payload.model_dump(), member_id=generate_member_id(), qr_code=str(uuid.uuid4()))
    db.add(member)
    await db.commit()
    await db.refresh(member)
    return member


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(member_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Member).where(Member.id == member_id, Member.is_deleted == False))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member


@router.put("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: int, payload: MemberUpdate,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Member).where(Member.id == member_id, Member.is_deleted == False))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(member, field, value)
    await db.commit()
    await db.refresh(member)
    return member


@router.delete("/{member_id}")
async def delete_member(member_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Member).where(Member.id == member_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    member.is_deleted = True
    await db.commit()
    return {"message": "Member deleted"}
