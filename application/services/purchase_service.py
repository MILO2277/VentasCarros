from datetime import datetime

from domain.entities.purchase import Purchase
from domain.repositories.car_repository import CarRepository
from domain.repositories.purchase_repository import PurchaseRepository


class PurchaseService:
	def __init__(self, purchase_repository: PurchaseRepository, car_repository: CarRepository):
		self.purchase_repository = purchase_repository
		self.car_repository = car_repository

	def buy_car(self, user_id, car_id):
		car = self.car_repository.get_by_id(car_id)
		if car is None:
			raise ValueError("El carro no existe.")
		if not car.available:
			raise ValueError("Este carro no está disponible.")
		purchase = Purchase(
			id=0,
			user_id=user_id,
			car_id=car.id,
			purchase_date=datetime.now().astimezone(),
			price=car.price,
		)
		return self.purchase_repository.create_for_available_car(purchase)

	def get_user_purchases(self, user_id):
		return self.purchase_repository.get_by_user_id(user_id)