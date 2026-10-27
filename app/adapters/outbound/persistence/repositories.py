from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.outbound.persistence.models import ItemModel, UserModel
from app.domain.entities import Item, Role, User


def _user_from_model(m: UserModel) -> User:
    return User(
        id=m.id,
        email=m.email,
        full_name=m.full_name,
        role=Role(m.role),
        hashed_password=m.hashed_password,
        is_active=m.is_active,
        created_at=m.created_at or datetime.now(timezone.utc),
    )


def _item_from_model(m: ItemModel) -> Item:
    return Item(
        id=m.id,
        title=m.title,
        description=m.description,
        status=m.status,
        owner_id=m.owner_id,
        created_at=m.created_at or datetime.now(timezone.utc),
        updated_at=m.updated_at or datetime.now(timezone.utc),
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self._session.get(UserModel, user_id)
        return _user_from_model(result) if result else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserModel).where(UserModel.email == email.lower())
        result = await self._session.scalar(stmt)
        return _user_from_model(result) if result else None

    async def create(self, email: str, full_name: str, hashed_password: str, role: Role) -> User:
        model = UserModel(
            email=email.lower(),
            full_name=full_name,
            hashed_password=hashed_password,
            role=role.value,
        )
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _user_from_model(model)


class SqlAlchemyItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, item_id: int) -> Item | None:
        result = await self._session.get(ItemModel, item_id)
        return _item_from_model(result) if result else None

    async def list_filtered(
        self,
        *,
        skip: int,
        limit: int,
        status: str | None,
        q: str | None,
        owner_id: int | None,
    ) -> tuple[list[Item], int]:
        filters = []
        if status:
            filters.append(ItemModel.status == status)
        if owner_id is not None:
            filters.append(ItemModel.owner_id == owner_id)
        if q:
            like = f"%{q}%"
            filters.append(or_(ItemModel.title.ilike(like), ItemModel.description.ilike(like)))

        count_stmt = select(func.count()).select_from(ItemModel)
        list_stmt = select(ItemModel).order_by(ItemModel.id.desc()).offset(skip).limit(limit)
        for f in filters:
            count_stmt = count_stmt.where(f)
            list_stmt = list_stmt.where(f)

        total = await self._session.scalar(count_stmt) or 0
        rows = (await self._session.scalars(list_stmt)).all()
        return [_item_from_model(r) for r in rows], int(total)

    async def create(self, title: str, description: str | None, status: str, owner_id: int) -> Item:
        model = ItemModel(title=title, description=description, status=status, owner_id=owner_id)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _item_from_model(model)

    async def update(self, item: Item) -> Item:
        model = await self._session.get(ItemModel, item.id)
        if not model:
            return item
        model.title = item.title
        model.description = item.description
        model.status = item.status
        await self._session.commit()
        await self._session.refresh(model)
        return _item_from_model(model)

    async def delete(self, item_id: int) -> None:
        model = await self._session.get(ItemModel, item_id)
        if model:
            await self._session.delete(model)
            await self._session.commit()

    async def bulk_create(self, rows: list[dict[str, Any]], owner_id: int) -> int:
        models = [
            ItemModel(
                title=str(r["title"])[:200],
                description=r.get("description"),
                status=str(r.get("status") or "open")[:32],
                owner_id=owner_id,
            )
            for r in rows
            if r.get("title")
        ]
        self._session.add_all(models)
        await self._session.commit()
        return len(models)
