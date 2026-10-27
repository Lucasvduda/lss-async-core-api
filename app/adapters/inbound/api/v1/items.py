from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, UploadFile

from app.adapters.inbound.api.deps import get_current_user, get_item_repo
from app.adapters.inbound.api.schemas import ImportResult, ItemCreateRequest, ItemResponse, PaginatedItems
from app.adapters.outbound.persistence.repositories import SqlAlchemyItemRepository
from app.application.use_cases.items import CreateItem, DeleteItem, GetItem, ImportItemsCsv, ListItems
from app.domain.entities import User
from app.infrastructure.logging import get_logger

router = APIRouter(prefix="/items", tags=["Items"])
logger = get_logger(__name__)


def _to_response(item) -> ItemResponse:
    return ItemResponse(
        id=item.id,
        title=item.title,
        description=item.description,
        status=item.status,
        owner_id=item.owner_id,
        created_at=item.created_at,
        updated_at=item.updated_at,
    )


@router.get("", response_model=PaginatedItems)
async def list_items(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    q: str | None = Query(None, description="Search in title/description"),
    user: User = Depends(get_current_user),
    items: SqlAlchemyItemRepository = Depends(get_item_repo),
) -> PaginatedItems:
    result = await ListItems(items).execute(user, page=page, page_size=page_size, status=status, q=q)
    return PaginatedItems(
        items=[_to_response(i) for i in result["items"]],
        page=result["page"],
        page_size=result["page_size"],
        total=result["total"],
        pages=result["pages"],
    )


@router.post("", response_model=ItemResponse, status_code=201)
async def create_item(
    body: ItemCreateRequest,
    user: User = Depends(get_current_user),
    items: SqlAlchemyItemRepository = Depends(get_item_repo),
) -> ItemResponse:
    item = await CreateItem(items).execute(user, body.title, body.description, body.status)
    return _to_response(item)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    user: User = Depends(get_current_user),
    items: SqlAlchemyItemRepository = Depends(get_item_repo),
) -> ItemResponse:
    item = await GetItem(items).execute(user, item_id)
    return _to_response(item)


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: int,
    user: User = Depends(get_current_user),
    items: SqlAlchemyItemRepository = Depends(get_item_repo),
) -> None:
    await DeleteItem(items).execute(user, item_id)


def _log_import(user_id: int, imported: int) -> None:
    logger.info("csv_import_finished", extra={"user_id": user_id, "imported": imported})


@router.post("/import/csv", response_model=ImportResult)
async def import_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    items: SqlAlchemyItemRepository = Depends(get_item_repo),
) -> ImportResult:
    content = await file.read()
    result = await ImportItemsCsv(items).execute(user, content)
    background_tasks.add_task(_log_import, user.id, result["imported"])
    return ImportResult(imported=result["imported"])
