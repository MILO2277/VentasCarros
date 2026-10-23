import unittest

from application.services.car_service import CarService
from application.services.catalog_service import CatalogService
from application.services.purchase_service import PurchaseService
from application.services.purchase_report_service import PurchaseReportService
from domain.entities.car import Car
from domain.entities.purchase import Purchase
from domain.entities.role import Role
from domain.entities.user import User
from infrastructure.firestore.mappers import (
	car_from_document,
	car_to_document,
	purchase_from_document,
	purchase_to_document,
	user_from_document,
	user_to_document,
)
from infrastructure.memory.repositories import (
	InMemoryCarRepository,
	InMemoryPurchaseRepository,
)


class MinimalCarRepository:
	def __init__(self):
		self.car = None

	def get_all(self):
		return [self.car] if self.car else []

	def get_by_id(self, car_id):
		return self.car if self.car and str(self.car.id) == str(car_id) else None

	def create(self, car):
		car.id = "external-id"
		self.car = car
		return car

	def update(self, car):
		if self.get_by_id(car.id) is None:
			return None
		self.car = car
		return car

	def delete(self, car_id):
		if self.get_by_id(car_id) is None:
			return False
		self.car = None
		return True


class ArchitectureTests(unittest.TestCase):
	def test_catalog_service_searches_and_filters_available_cars(self):
		car_repository = InMemoryCarRepository()
		car_repository.create(Car(0, "Toyota", "Corolla", 2023, 10, "Sedan", "", True))
		car_repository.create(Car(0, "Toyota", "Camry", 2022, 20, "Sedan", "", False))
		car_repository.create(Car(0, "Honda", "Civic", 2023, 15, "Compact", "", True))
		service = CatalogService(car_repository)

		results = service.search_cars("TOYOTA", available_only=True)

		self.assertEqual([car.model for car in results], ["Corolla"])

	def test_purchase_report_summarizes_user_spending(self):
		car_repository = InMemoryCarRepository()
		purchase_repository = InMemoryPurchaseRepository(car_repository)
		car = car_repository.create(Car(0, "Honda", "Civic", 2023, 10, "", "", True))
		purchase_repository.create_for_available_car(
			Purchase(0, 7, car.id, __import__("datetime").datetime(2025, 1, 1), 10)
		)
		service = PurchaseReportService(purchase_repository)

		self.assertEqual(
			service.get_user_purchase_summary(7),
			{"purchase_count": 1, "total_spent": 10},
		)
		self.assertEqual(
			service.get_user_purchase_summary(8),
			{"purchase_count": 0, "total_spent": 0},
		)

	def test_car_service_works_with_different_repository_implementations(self):
		for repository in (InMemoryCarRepository(), MinimalCarRepository()):
			with self.subTest(repository=type(repository).__name__):
				service = CarService(repository)
				car = service.create_car("Toyota", "Corolla", 2023, 80000000, "Sedan", "https://example.com/car.jpg")
				self.assertIs(service.car_repository, repository)
				self.assertEqual(service.get_car(car.id).model, "Corolla")
				self.assertEqual(len(service.get_cars()), 1)

	def test_purchase_persists_availability_and_purchase(self):
		car_repository = InMemoryCarRepository()
		purchase_repository = InMemoryPurchaseRepository(car_repository)
		car = car_repository.create(Car(0, "Honda", "Civic", 2023, 10, "", "", True))
		service = PurchaseService(purchase_repository, car_repository)

		purchase = service.buy_car(7, car.id)

		self.assertFalse(car_repository.get_by_id(car.id).available)
		self.assertEqual(service.get_user_purchases(7), [purchase])
		self.assertEqual(purchase.price, 10)

	def test_mapper_round_trips_entities(self):
		car = Car("car-1", "Mazda", "3", 2022, 12.5, "Description", "image.jpg", False)
		self.assertEqual(car_from_document("car-1", car_to_document(car)), car)

		user = User("user-1", "Ana", "ana@example.com", "hash", Role.ADMIN)
		self.assertEqual(user_from_document("user-1", user_to_document(user)), user)

		purchase = Purchase("sale-1", "user-1", "car-1", __import__("datetime").datetime(2025, 1, 1), 12.5)
		self.assertEqual(
			purchase_from_document("sale-1", purchase_to_document(purchase)),
			purchase,
		)


if __name__ == "__main__":
	unittest.main()