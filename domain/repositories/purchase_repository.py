from typing import List, Protocol, Union

from domain.entities.purchase import Purchase


class ISaleRepository(Protocol):
    def create_for_available_car(self, purchase: Purchase) -> Purchase: ...

    def get_by_user_id(self, user_id: Union[int, str]) -> List[Purchase]: ...


PurchaseRepository = ISaleRepository