from dataclasses import dataclass
from typing import Union

from domain.entities.role import Role


@dataclass
class User:
	id: Union[int, str]
	name: str
	email: str
	password: str
	role: Role
