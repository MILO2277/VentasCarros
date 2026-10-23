from typing import Optional, Protocol, Union

from domain.entities.user import User


class IUserRepository(Protocol):
    def create_if_absent(self, user: User) -> User: ...

    def create_first_admin(self, user: User) -> User: ...

    def get_by_id(self, user_id: Union[int, str]) -> Optional[User]: ...

    def get_by_email(self, email: str) -> Optional[User]: ...

    def get_all(self) -> list[User]: ...


UserRepository = IUserRepository