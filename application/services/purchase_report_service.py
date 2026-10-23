from domain.repositories.purchase_repository import PurchaseRepository


class PurchaseReportService:
	def __init__(self, purchase_repository: PurchaseRepository):
		self.purchase_repository = purchase_repository

	def get_user_purchase_summary(self, user_id):
		purchases = self.purchase_repository.get_by_user_id(user_id)
		return {
			"purchase_count": len(purchases),
			"total_spent": sum(purchase.price for purchase in purchases),
		}
