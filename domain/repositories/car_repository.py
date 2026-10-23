from typing import Optional, Protocol, Union

from domain.entities.car import Car


class ICarRepository(Protocol):
    def get_all(self) -> list[Car]: ...

    def get_by_id(self, car_id: Union[int, str]) -> Optional[Car]: ...

    def create(self, car: Car) -> Car: ...

    def update(self, car: Car) -> Optional[Car]: ...

    def delete(self, car_id: Union[int, str]) -> bool: ...


CarRepository = ICarRepository