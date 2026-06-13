from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.lead import Lead, LeadStatus
from app.models.user import User
from app.schemas.lead import LeadCreate, LeadUpdate, LeadResponse
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("/", response_model=PaginatedResponse[LeadResponse])
async def list_leads(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    status: Optional[LeadStatus] = None, branch_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user),
):
    query = select(Lead).where(Lead.is_deleted == False)
    if status:
        query = query.where(Lead.status == status)
    if branch_id:
        query = query.where(Lead.branch_id == branch_id)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    result = await db.execute(query.offset((page - 1) * page_size).limit(page_size))
    return PaginatedResponse(items=result.scalars().all(), total=total, page=page, page_size=page_size, pages=(total + page_size - 1) // page_size)


@router.post("/", response_model=LeadResponse, status_code=201)
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    return lead


@router.put("/{lead_id}", response_model=LeadResponse)
async def update_lead(lead_id: int, payload: LeadUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    r = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = r.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if payload.status == LeadStatus.WON:
        lead.converted_at = datetime.now(timezone.utc)
    for f, v in payload.model_dump(exclude_none=True).items():
        setattr(lead, f, v)
    await db.commit()
    await db.refresh(lead)
    return lead
