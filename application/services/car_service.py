
from math import isfinite
from typing import Optional
from urllib.parse import urlparse

from domain.entities.car import Car
from domain.repositories.car_repository import CarRepository
from domain.repositories.image_storage import ImageStorage


class CarService:
	def __init__(self, car_repository: CarRepository, image_storage: Optional[ImageStorage] = None):
		self.car_repository = car_repository
		self.image_storage = image_storage

	def get_cars(self):
		return self.car_repository.get_all()

	def get_car(self, car_id):
		return self.car_repository.get_by_id(car_id)

	def create_car(
		self, brand, model, year, price, description, image="", available=True,
		image_file=None, image_filename="",
	):
		stored_image = image
		uploaded_path = None
		try:
			if image_file is not None:
				if self.image_storage is None:
					raise RuntimeError("El almacenamiento de imágenes no está configurado.")
				uploaded_path = self.image_storage.save(image_file, image_filename)
				stored_image = uploaded_path
			self._validate_car(brand, model, year, price, description, stored_image)
			car = Car(0, brand, model, year, price, description, stored_image, available)
			created_car = self.car_repository.create(car)
			if created_car is None:
				raise RuntimeError("El repositorio no confirmó el registro del carro.")
			return created_car
		except Exception:
			self._remove_new_upload(uploaded_path)
			raise

	def update_car(
		self, car_id, brand, model, year, price, description, image=None, available=True,
		image_file=None, image_filename="",
	):
		existing_car = self.car_repository.get_by_id(car_id)
		if existing_car is None:
			return None
		stored_image = existing_car.image if image is None else image
		uploaded_path = None
		try:
			if image_file is not None:
				if self.image_storage is None:
					raise RuntimeError("El almacenamiento de imágenes no está configurado.")
				uploaded_path = self.image_storage.save(image_file, image_filename)
				stored_image = uploaded_path
			self._validate_car(brand, model, year, price, description, stored_image)
			car = Car(car_id, brand, model, year, price, description, stored_image, available)
			updated_car = self.car_repository.update(car)
			if updated_car is None:
				raise RuntimeError("El repositorio no confirmó la actualización del carro.")
			return updated_car
		except Exception:
			self._remove_new_upload(uploaded_path)
			raise

	def delete_car(self, car_id):
		return self.car_repository.delete(car_id)

	def _remove_new_upload(self, uploaded_path):
		if uploaded_path and self.image_storage is not None:
			self.image_storage.delete(uploaded_path)

	@staticmethod
	def _validate_car(brand, model, year, price, description, image):
		if not brand.strip() or not model.strip() or not description.strip():
			raise ValueError("Marca, modelo y descripción son obligatorios.")
		try:
			year = int(year)
			price = float(price)
		except (TypeError, ValueError) as error:
			raise ValueError("El año y el precio deben ser valores numéricos válidos.") from error
		if year < 1886 or year > 2100:
			raise ValueError("El año del vehículo no es válido.")
		if not isfinite(price) or price < 0:
			raise ValueError("El precio debe ser un valor positivo válido.")
		if image.startswith("uploads/cars/") and ".." not in image.split("/"):
			return
		parsed_image = urlparse(image)
		if parsed_image.scheme not in {"http", "https"} or not parsed_image.netloc:
			raise ValueError("La imagen debe usar una URL HTTP o HTTPS válida.")