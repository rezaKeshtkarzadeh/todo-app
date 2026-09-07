from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.core.errors import AppError
from app.db.session import get_db_session
from app.schemas.task import TaskCreate, TaskUpdate, TaskRead
from app.models.task import Task
from app.dependencies.auth import get_current_user
from app.dependencies.csrf import validate_csrf
from app.services.task_service import (
    get_user_task,
    create_task,
    update_task,
    delete_task,
)


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """List all tasks for the current user."""
    user = current_user.user

    result = await db.execute(
        select(Task).where(Task.user_id == user.id).order_by(Task.created_at.desc())
    )
    tasks = result.scalars().all()
    return tasks


@router.post("", response_model=TaskRead, status_code=201, dependencies=[Depends(validate_csrf)])
async def create_task_endpoint(
    request: Request,
    payload: TaskCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """Create a new task for the current user. Requires CSRF."""
    user = current_user.user

    task = await create_task(db, request, user.id, payload.title)
    await db.commit()
    return task


@router.patch("/{task_id}", response_model=TaskRead, dependencies=[Depends(validate_csrf)])
async def update_task_endpoint(
    request: Request,
    task_id: UUID,
    payload: TaskUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Update a task. Uses PATCH with partial body.
    Scoped by (task_id, user_id) in the query itself.
    Not found/other-user's task → 404 TASK_NOT_FOUND.
    Requires CSRF.
    """
    user = current_user.user

    task = await get_user_task(db, task_id, user.id)
    if not task:
        raise AppError("TASK_NOT_FOUND", 404, "Task not found.")

    try:
        updated_task = await update_task(
            db,
            request,
            task,
            title=payload.title,
            is_done=payload.is_done,
        )
    except ValueError as e:
        raise AppError("VALIDATION_ERROR", 422, str(e))

    await db.commit()
    return updated_task


@router.delete("/{task_id}", status_code=204, dependencies=[Depends(validate_csrf)])
async def delete_task_endpoint(
    request: Request,
    task_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Delete a task. Hard delete.
    Scoped by (task_id, user_id).
    Not found/other-user's task → 404 TASK_NOT_FOUND.
    Requires CSRF.
    """
    user = current_user.user

    task = await get_user_task(db, task_id, user.id)
    if not task:
        raise AppError("TASK_NOT_FOUND", 404, "Task not found.")

    await delete_task(db, request, task)
    await db.commit()
    return Response(status_code=204)