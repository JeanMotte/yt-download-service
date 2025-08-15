from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from yt_download_service.app.interfaces.user_service import IUserService
from yt_download_service.domain.models.user import UserCreate, UserRead
from yt_download_service.infrastructure.database.models import DBUser


class UserService(IUserService):
    """Service for user-related database operations."""

    async def create(self, db: AsyncSession, user_to_create: UserCreate) -> UserRead:
        """Create a new user in the database."""
        # 1. Create the SQLAlchemy model instance
        db_user = DBUser(**user_to_create.model_dump())

        # 2. Use the injected async session correctly
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)

        # 3. Return the Pydantic model
        return UserRead.model_validate(db_user)

    async def get_by_id(self, db: AsyncSession, user_id: UUID) -> UserRead | None:
        """Get a user by their ID using an async session."""
        result = await db.execute(select(DBUser).where(DBUser.id == user_id))
        db_user = result.scalars().first()

        if db_user:
            return UserRead.model_validate(db_user)
        return None

    async def get_by_email(self, db: AsyncSession, email: str) -> UserRead | None:
        """Fetch a user by email using an async session."""
        result = await db.execute(select(DBUser).where(DBUser.email == email))
        db_user = result.scalars().first()
        if db_user:
            return UserRead.model_validate(db_user)
        return None
