import hashlib

from domain.entities.car import Car
from domain.entities.purchase import Purchase
from domain.entities.user import User
from firebase_admin import firestore
from infrastructure.firestore.mappers import (
	car_from_document,
	car_to_document,
	purchase_from_document,
	purchase_to_document,
	user_from_document,
	user_to_document,
)


class RepositoryError(RuntimeError):
	"""Persistence failure translated from the Firestore SDK."""


class FirestoreCarRepository:
	def __init__(self, client):
		self._collection = client.collection("cars")

	def get_all(self):
		try:
			return [car_from_document(doc.id, doc.to_dict()) for doc in self._collection.stream()]
		except Exception as error:
			raise RepositoryError("No se pudieron consultar los carros.") from error

	def get_by_id(self, car_id):
		try:
			document = self._collection.document(str(car_id)).get()
			return car_from_document(document.id, document.to_dict()) if document.exists else None
		except Exception as error:
			raise RepositoryError("No se pudo consultar el carro.") from error

	def create(self, car: Car):
		try:
			document = self._collection.document()
			document.set(car_to_document(car))
			return car_from_document(document.id, car_to_document(car))
		except Exception as error:
			raise RepositoryError("No se pudo registrar el carro.") from error

	def update(self, car: Car):
		try:
			document = self._collection.document(str(car.id))
			if not document.get().exists:
				return None
			document.set(car_to_document(car))
			return car_from_document(str(car.id), car_to_document(car))
		except Exception as error:
			raise RepositoryError("No se pudo actualizar el carro.") from error

	def delete(self, car_id):
		try:
			document = self._collection.document(str(car_id))
			if not document.get().exists:
				return False
			document.delete()
			return True
		except Exception as error:
			raise RepositoryError("No se pudo eliminar el carro.") from error


class FirestoreUserRepository:
	def __init__(self, client):
		self._client = client
		self._collection = client.collection("users")

	def create_if_absent(self, user: User):
		try:
			normalized_email = user.email.strip().lower()
			if self.get_by_email(normalized_email):
				raise ValueError("El correo ya está registrado.")
			document_id = "email-" + hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
			document = self._collection.document(document_id)
			transaction = self._client.transaction()

			@firestore.transactional
			def create_user(active_transaction):
				if document.get(transaction=active_transaction).exists:
					raise ValueError("El correo ya está registrado.")
				active_transaction.create(document, user_to_document(user))

			create_user(transaction)
			user.id = document_id
			return user
		except ValueError:
			raise
		except Exception as error:
			raise RepositoryError("No se pudo registrar el usuario.") from error

	def create_first_admin(self, user: User):
		try:
			if any(existing.role.value == "ADMIN" for existing in self.get_all()):
				raise ValueError("Ya existe un administrador; no se creó otra cuenta.")
			normalized_email = user.email.strip().lower()
			if self.get_by_email(normalized_email):
				raise ValueError("El correo ya está registrado.")
			document_id = "email-" + hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()
			user_reference = self._collection.document(document_id)
			marker_reference = self._client.collection("system_metadata").document("first_admin")
			transaction = self._client.transaction()

			@firestore.transactional
			def create_admin(active_transaction):
				marker = marker_reference.get(transaction=active_transaction)
				if marker.exists:
					raise ValueError("Ya existe un administrador; no se creó otra cuenta.")
				if user_reference.get(transaction=active_transaction).exists:
					raise ValueError("El correo ya está registrado.")
				active_transaction.create(user_reference, user_to_document(user))
				active_transaction.create(marker_reference, {"user_id": document_id})

			create_admin(transaction)
			user.id = document_id
			return user
		except ValueError:
			raise
		except Exception as error:
			raise RepositoryError("No se pudo crear el administrador inicial.") from error

	def get_by_id(self, user_id):
		try:
			document = self._collection.document(str(user_id)).get()
			return user_from_document(document.id, document.to_dict()) if document.exists else None
		except Exception as error:
			raise RepositoryError("No se pudo consultar el usuario.") from error

	def get_by_email(self, email):
		try:
			documents = self._collection.where("email", "==", email.strip().lower()).limit(1).stream()
			document = next(iter(documents), None)
			return user_from_document(document.id, document.to_dict()) if document else None
		except Exception as error:
			raise RepositoryError("No se pudo consultar el usuario por correo.") from error

	def get_all(self):
		try:
			return [user_from_document(doc.id, doc.to_dict()) for doc in self._collection.stream()]
		except Exception as error:
			raise RepositoryError("No se pudieron consultar los usuarios.") from error


class FirestorePurchaseRepository:
	def __init__(self, client):
		self._client = client
		self._cars = client.collection("cars")
		self._collection = client.collection("purchases")

	def create_for_available_car(self, purchase: Purchase):
		try:
			car_reference = self._cars.document(str(purchase.car_id))
			purchase_reference = self._collection.document()
			transaction = self._client.transaction()

			@firestore.transactional
			def commit_purchase(active_transaction):
				car_snapshot = car_reference.get(transaction=active_transaction)
				if not car_snapshot.exists:
					raise ValueError("El carro no existe.")
				car_data = car_snapshot.to_dict()
				if not car_data.get("available", True):
					raise ValueError("Este carro no está disponible.")
				purchase.price = float(car_data["price"])
				active_transaction.update(car_reference, {"available": False})
				active_transaction.set(purchase_reference, purchase_to_document(purchase))

			commit_purchase(transaction)
			return purchase_from_document(
				purchase_reference.id,
				purchase_to_document(purchase),
			)
		except ValueError:
			raise
		except Exception as error:
			raise RepositoryError("No se pudo registrar la compra.") from error

	def get_by_user_id(self, user_id):
		try:
			documents = self._collection.where("user_id", "==", str(user_id)).stream()
			return [purchase_from_document(doc.id, doc.to_dict()) for doc in documents]
		except Exception as error:
			raise RepositoryError("No se pudieron consultar las compras.") from error