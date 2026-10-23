from domain.repositories.car_repository import CarRepository


class CatalogService:
	def __init__(self, car_repository: CarRepository):
		self.car_repository = car_repository

	def search_cars(self, query="", available_only=False):
		search_term = query.strip().casefold()
		cars = self.car_repository.get_all()
		if available_only:
			cars = [car for car in cars if car.available]
		if not search_term:
			return cars
		return [
			car for car in cars
			if search_term in car.brand.casefold()
			or search_term in car.model.casefold()
			or search_term in car.description.casefold()
		]
