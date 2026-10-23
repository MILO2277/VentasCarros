from threading import Lock
from typing import List, Optional, Union

from domain.entities.car import Car
from domain.entities.purchase import Purchase
from domain.entities.user import User


class InMemoryCarRepository:
    def __init__(self):
        self._cars = []
        self._next_id = 1

    def create(self, car: Car) -> Car:
        car.id = self._next_id
        self._next_id += 1
        self._cars.append(car)
        return car

    def get_by_id(self, car_id: Union[int, str]) -> Optional[Car]:
        return next((car for car in self._cars if str(car.id) == str(car_id)), None)

    def get_all(self) -> List[Car]:
        return list(self._cars)

    def update(self, car: Car) -> Optional[Car]:
        existing_car = self.get_by_id(car.id)
        if existing_car is None:
            return None
        existing_car.brand = car.brand
        existing_car.model = car.model
        existing_car.year = car.year
        existing_car.price = car.price
        existing_car.description = car.description
        existing_car.image = car.image
        existing_car.available = car.available
        return existing_car

    def delete(self, car_id: Union[int, str]) -> bool:
        car = self.get_by_id(car_id)
        if car is None:
            return False
        self._cars.remove(car)
        return True


class InMemoryUserRepository:
    def __init__(self):
        self._users = []
        self._next_id = 1
        self._user_lock = Lock()

    def create_if_absent(self, user: User) -> User:
        with self._user_lock:
            if self.get_by_email(user.email):
                raise ValueError("El correo ya está registrado.")
            user.id = self._next_id
            self._next_id += 1
            self._users.append(user)
            return user

    def create_first_admin(self, user: User) -> User:
        with self._user_lock:
            if any(existing.role.value == "ADMIN" for existing in self._users):
                raise ValueError("Ya existe un administrador; no se creó otra cuenta.")
            if self.get_by_email(user.email):
                raise ValueError("El correo ya está registrado.")
            user.id = self._next_id
            self._next_id += 1
            self._users.append(user)
            return user

    def get_by_id(self, user_id: Union[int, str]) -> Optional[User]:
        return next((user for user in self._users if str(user.id) == str(user_id)), None)

    def get_by_email(self, email: str) -> Optional[User]:
        normalized_email = email.strip().lower()
        return next((user for user in self._users if user.email.lower() == normalized_email), None)

    def get_all(self) -> List[User]:
        return list(self._users)


class InMemoryPurchaseRepository:
    def __init__(self, car_repository):
        self._purchases = []
        self._next_id = 1
        self._car_repository = car_repository
        self._purchase_lock = Lock()

    def create_for_available_car(self, purchase: Purchase) -> Purchase:
        with self._purchase_lock:
            car = self._car_repository.get_by_id(purchase.car_id)
            if car is None:
                raise ValueError("El carro no existe.")
            if not car.available:
                raise ValueError("Este carro no está disponible.")
            car.available = False
            if self._car_repository.update(car) is None:
                raise ValueError("No se pudo actualizar la disponibilidad del carro.")
            purchase.price = car.price
            purchase.id = self._next_id
            self._next_id += 1
            self._purchases.append(purchase)
            return purchase

    def get_by_user_id(self, user_id: Union[int, str]) -> List[Purchase]:
        return [purchase for purchase in self._purchases if str(purchase.user_id) == str(user_id)]