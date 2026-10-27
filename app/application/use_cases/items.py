import csv
import io

from app.application.ports.repositories import ItemRepository
from app.domain.entities import Item, Role, User
from app.domain.errors import ForbiddenError, NotFoundError, ValidationDomainError


class ListItems:
    def __init__(self, items: ItemRepository) -> None:
        self._items = items

    async def execute(
        self,
        user: User,
        *,
        page: int,
        page_size: int,
        status: str | None,
        q: str | None,
    ) -> dict:
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)
        skip = (page - 1) * page_size
        owner_id = None if user.role == Role.ADMIN else user.id
        rows, total = await self._items.list_filtered(
            skip=skip, limit=page_size, status=status, q=q, owner_id=owner_id
        )
        return {
            "items": rows,
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": (total + page_size - 1) // page_size if page_size else 0,
        }


class CreateItem:
    def __init__(self, items: ItemRepository) -> None:
        self._items = items

    async def execute(self, user: User, title: str, description: str | None, status: str) -> Item:
        if user.role == Role.VIEWER:
            raise ForbiddenError("Viewers cannot create items")
        if not title.strip():
            raise ValidationDomainError("Title is required")
        return await self._items.create(title.strip(), description, status or "open", user.id)


class GetItem:
    def __init__(self, items: ItemRepository) -> None:
        self._items = items

    async def execute(self, user: User, item_id: int) -> Item:
        item = await self._items.get_by_id(item_id)
        if not item:
            raise NotFoundError("Item not found")
        if user.role != Role.ADMIN and item.owner_id != user.id:
            raise ForbiddenError("Not allowed to view this item")
        return item


class DeleteItem:
    def __init__(self, items: ItemRepository) -> None:
        self._items = items

    async def execute(self, user: User, item_id: int) -> None:
        item = await self._items.get_by_id(item_id)
        if not item:
            raise NotFoundError("Item not found")
        if user.role != Role.ADMIN and item.owner_id != user.id:
            raise ForbiddenError("Not allowed to delete this item")
        if user.role == Role.VIEWER:
            raise ForbiddenError("Viewers cannot delete items")
        await self._items.delete(item_id)


class ImportItemsCsv:
    def __init__(self, items: ItemRepository) -> None:
        self._items = items

    async def execute(self, user: User, content: bytes) -> dict:
        if user.role == Role.VIEWER:
            raise ForbiddenError("Viewers cannot import CSV")
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValidationDomainError("CSV must be UTF-8") from exc

        reader = csv.DictReader(io.StringIO(text))
        if not reader.fieldnames or "title" not in [f.strip().lower() for f in reader.fieldnames]:
            raise ValidationDomainError("CSV must include a title column")

        normalized_fields = {f: f.strip().lower() for f in reader.fieldnames}
        rows: list[dict] = []
        for raw in reader:
            mapped = {normalized_fields[k]: (v.strip() if isinstance(v, str) else v) for k, v in raw.items()}
            if mapped.get("title"):
                rows.append(
                    {
                        "title": mapped["title"],
                        "description": mapped.get("description"),
                        "status": mapped.get("status") or "open",
                    }
                )
        if not rows:
            raise ValidationDomainError("CSV has no valid rows")
        created = await self._items.bulk_create(rows, user.id)
        return {"imported": created}
