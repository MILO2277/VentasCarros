from datetime import datetime

from domain.entities.car import Car
from domain.entities.purchase import Purchase
from domain.entities.role import Role
from domain.entities.user import User


def car_from_document(document_id, data):
	return Car(
		id=document_id,
		brand=data["brand"],
		model=data["model"],
		year=int(data["year"]),
		price=float(data["price"]),
		description=data.get("description", ""),
		image=data.get("image", ""),
		available=bool(data.get("available", True)),
	)


def car_to_document(car):
	return {
		"brand": car.brand,
		"model": car.model,
		"year": car.year,
		"price": car.price,
		"description": car.description,
		"image": car.image,
		"available": car.available,
	}


def user_from_document(document_id, data):
	return User(
		id=document_id,
		name=data["name"],
		email=data["email"],
		password=data["password_hash"],
		role=Role(data["role"]),
	)


def user_to_document(user):
	return {
		"name": user.name,
		"email": user.email.strip().lower(),
		"password_hash": user.password,
		"role": user.role.value,
	}


def purchase_from_document(document_id, data):
	purchase_date = data["purchase_date"]
	if not isinstance(purchase_date, datetime):
		purchase_date = purchase_date.to_datetime()
	return Purchase(
		id=document_id,
		user_id=data["user_id"],
		car_id=data["car_id"],
		purchase_date=purchase_date,
		price=float(data["price"]),
	)


def purchase_to_document(purchase):
	return {
		"user_id": str(purchase.user_id),
		"car_id": str(purchase.car_id),
		"purchase_date": purchase.purchase_date,
		"price": purchase.price,
	}