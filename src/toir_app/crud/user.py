# from typing import Optional

# from sqlalchemy import select
# from sqlalchemy.orm import selectinload
# from sqlalchemy.ext.asyncio import AsyncSession

from crud.base import DAOBase
from models import User


class UserDAO(DAOBase[User]):
    """DAO для работы с моделью документа с материалами."""

    model = User

    # async def get_by_personal_email(
    #         self, user_email, session: AsyncSession
    # ) -> Optional[User]:
    #     stmt = (
    #         select(self.model)
    #         .where(self.model.email == user_email)
    #         .options(
    #             selectinload(self.model.users_organization)
    #         )
    #         .limit(1)
    #     )
    #     result = await session.scalar(stmt)
    #     return result


user_dao = UserDAO(model=User)
