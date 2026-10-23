from dataclasses import dataclass
from datetime import datetime
from typing import Union


@dataclass
class Purchase:
	id: Union[int, str]
	user_id: Union[int, str]
	car_id: Union[int, str]
	purchase_date: datetime
	price: float
