import re

from werkzeug.security import check_password_hash, generate_password_hash

from domain.entities.role import Role
from domain.entities.user import User
from domain.repositories.user_repository import UserRepository


class AuthService:
	def __init__(self, user_repository: UserRepository):
		self.user_repository = user_repository

	def register(self, name, email, password, role=Role.USER):
		user = self._build_user(name, email, password, role)
		return self.user_repository.create_if_absent(user)

	def register_first_admin(self, name, email, password):
		user = self._build_user(name, email, password, Role.ADMIN)
		return self.user_repository.create_first_admin(user)

	@staticmethod
	def _build_user(name, email, password, role):
		normalized_email = email.strip().lower()
		if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized_email):
			raise ValueError("Ingresa un correo válido.")
		if not name.strip() or len(name.strip()) > 100:
			raise ValueError("Todos los campos son obligatorios.")
		if len(normalized_email) > 254:
			raise ValueError("El correo es demasiado largo.")
		if len(password) < 10:
			raise ValueError("La contraseña debe tener al menos 10 caracteres.")
		user = User(
			id=0,
			name=name.strip(),
			email=normalized_email,
			password=generate_password_hash(password),
			role=role,
		)
		return user

	def authenticate(self, email, password):
		user = self.user_repository.get_by_email(email)
		if user and check_password_hash(user.password, password):
			return user
		return None

	def find_by_id(self, user_id):
		return self.user_repository.get_by_id(user_id)