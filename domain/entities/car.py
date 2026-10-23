from dataclasses import dataclass
from typing import Union


@dataclass
class Car:
	id: Union[int, str]
	brand: str
	model: str
	year: int
	price: float
	description: str
	image: str
	available: bool
