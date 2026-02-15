"""
Klasör işlemleri - BLUEPRINT endpoints/folders.
CRUD: Hiyerarşik klasör yapısı (parent_id); kullanıcıya özel.
"""
from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, delete as sql_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.db import get_db
from app.models import Folder, User, Video

router = APIRouter()


class FolderCreate(BaseModel):
    name: str
    parent_id: UUID | None = None


class FolderUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[UUID] = None


class FolderResponse(BaseModel):
    id: UUID
    parent_id: UUID | None
    name: str
    user_id: UUID
    created_at: str

    class Config:
        from_attributes = True


def _serialize_folder(f: Folder) -> FolderResponse:
    return FolderResponse(
        id=f.id,
        parent_id=f.parent_id,
        name=f.name,
        user_id=f.user_id,
        created_at=f.created_at.isoformat() if f.created_at else "",
    )


async def _get_user_folder(db: AsyncSession, folder_id: UUID, user_id: UUID) -> Folder | None:
    """Kullanıcıya ait klasörü getir."""
    result = await db.execute(
        select(Folder).where(Folder.id == folder_id, Folder.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _get_descendant_folder_ids(db: AsyncSession, folder_id: UUID, user_id: UUID) -> list[UUID]:
    """Bir klasörün tüm alt klasör ID'lerini recursive olarak getir."""
    descendants = []
    
    async def collect_children(parent_id: UUID):
        result = await db.execute(
            select(Folder.id).where(
                Folder.parent_id == parent_id,
                Folder.user_id == user_id
            )
        )
        children = [row[0] for row in result.all()]
        for child_id in children:
            descendants.append(child_id)
            await collect_children(child_id)
    
    await collect_children(folder_id)
    return descendants


@router.post("/", response_model=FolderResponse)
async def create_folder(
    payload: FolderCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Klasör oluştur."""
    if payload.parent_id:
        result = await db.execute(
            select(Folder).where(
                Folder.id == payload.parent_id,
                Folder.user_id == user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Üst klasör bulunamadı veya size ait değil",
            )
    folder = Folder(
        name=payload.name,
        parent_id=payload.parent_id,
        user_id=user.id,
    )
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return _serialize_folder(folder)


@router.get("/{folder_id}", response_model=FolderResponse)
async def get_folder(
    folder_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Klasör detayı (sadece kendi klasörünüz)."""
    folder = await _get_user_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klasör bulunamadı",
        )
    return _serialize_folder(folder)


@router.get("/", response_model=list[FolderResponse])
async def list_folders(
    parent_id: UUID | None = None,
    all: bool = Query(default=True, description="Tüm klasörleri getir (hiyerarşik)"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Klasör listesi; all=True ise tüm klasörler, değilse sadece root veya belirtilen parent."""
    q = select(Folder).where(Folder.user_id == user.id)
    
    if not all:
        if parent_id is not None:
            q = q.where(Folder.parent_id == parent_id)
        else:
            q = q.where(Folder.parent_id.is_(None))
    
    result = await db.execute(q.order_by(Folder.name))
    folders = result.scalars().all()
    return [_serialize_folder(f) for f in folders]


@router.put("/{folder_id}", response_model=FolderResponse)
async def update_folder(
    folder_id: UUID,
    payload: FolderUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Klasör güncelle (isim değiştir, taşı)."""
    folder = await _get_user_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klasör bulunamadı",
        )
    
    # İsim güncelleme
    if payload.name is not None:
        folder.name = payload.name
    
    # Parent değiştirme (taşıma)
    if payload.parent_id is not None:
        # Kendine veya alt klasörüne taşınamaz
        if payload.parent_id == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Klasör kendisine taşınamaz",
            )
        
        descendant_ids = await _get_descendant_folder_ids(db, folder_id, user.id)
        if payload.parent_id in descendant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Klasör alt klasörüne taşınamaz",
            )
        
        # Hedef klasörün kullanıcıya ait olduğunu kontrol et
        target_folder = await _get_user_folder(db, payload.parent_id, user.id)
        if not target_folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Hedef klasör bulunamadı",
            )
        
        folder.parent_id = payload.parent_id
    elif payload.parent_id is None and "parent_id" in (payload.model_dump(exclude_unset=True) or {}):
        # Açıkça None olarak set edilmişse root'a taşı
        folder.parent_id = None
    
    await db.flush()
    await db.refresh(folder)
    return _serialize_folder(folder)


@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_folder(
    folder_id: UUID,
    cascade: bool = Query(default=False, description="Alt klasörleri ve videoları da sil"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Klasör sil. cascade=True ise alt klasörler ve videolar da silinir."""
    folder = await _get_user_folder(db, folder_id, user.id)
    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Klasör bulunamadı",
        )
    
    # Alt klasörleri kontrol et
    descendant_ids = await _get_descendant_folder_ids(db, folder_id, user.id)
    all_folder_ids = [folder_id] + descendant_ids
    
    if cascade:
        # Önce bu klasör ve alt klasörlerdeki videoları sil
        await db.execute(
            sql_delete(Video).where(Video.folder_id.in_(all_folder_ids))
        )
        # Sonra alt klasörleri sil (en derinden başlayarak)
        for fid in reversed(descendant_ids):
            await db.execute(sql_delete(Folder).where(Folder.id == fid))
        # Son olarak ana klasörü sil
        await db.delete(folder)
    else:
        # Alt klasör veya video var mı kontrol et
        if descendant_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Klasörde alt klasörler var. Önce onları silin veya cascade=true kullanın",
            )
        
        video_result = await db.execute(
            select(Video.id).where(Video.folder_id == folder_id).limit(1)
        )
        if video_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Klasörde videolar var. Önce onları silin/taşıyın veya cascade=true kullanın",
            )
        
        await db.delete(folder)
    
    await db.flush()
    return None
