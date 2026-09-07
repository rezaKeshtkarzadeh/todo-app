from uuid import UUID
from sqlalchemy import select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.services.logging_service import log_audit_event


async def get_user_task(db: AsyncSession, task_id: UUID, user_id: UUID) -> Task | None:
    """Get a task by ID scoped to user."""
    result = await db.execute(
        select(Task).where(
            and_(Task.id == task_id, Task.user_id == user_id)
        )
    )
    return result.scalar_one_or_none()


async def create_task(
    db: AsyncSession,
    request,
    user_id: UUID,
    title: str,
) -> Task:
    """Create a new task for the user."""
    task = Task(user_id=user_id, title=title)
    db.add(task)
    await db.flush()

    # Write audit log
    await log_audit_event(
        db=db,
        action="TASK_CREATED",
        resource_type="task",
        resource_id=task.id,
        user_id=user_id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"title": task.title},
    )

    return task


async def update_task(
    db: AsyncSession,
    request,
    task: Task,
    title: str | None = None,
    is_done: bool | None = None,
) -> Task:
    """Update a task. At least one field must be provided."""
    if title is None and is_done is None:
        raise ValueError("At least one field (title or is_done) must be provided.")

    if title is not None:
        task.title = title
    if is_done is not None:
        task.is_done = is_done

    await db.flush()

    # Write audit log
    await log_audit_event(
        db=db,
        action="TASK_UPDATED",
        resource_type="task",
        resource_id=task.id,
        user_id=task.user_id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"title": task.title, "is_done": task.is_done},
    )

    return task


async def delete_task(
    db: AsyncSession,
    request,
    task: Task,
) -> None:
    """Hard delete a task."""
    task_id = task.id
    user_id = task.user_id

    await db.execute(
        delete(Task).where(Task.id == task_id)
    )
    await db.flush()

    # Write audit log
    await log_audit_event(
        db=db,
        action="TASK_DELETED",
        resource_type="task",
        resource_id=task_id,
        user_id=user_id,
        request_id=getattr(request.state, "request_id", None),
        metadata={},
    )