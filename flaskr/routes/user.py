from flask import Blueprint, current_app, flash, redirect, render_template, url_for

from flaskr.routes import login_required, user_required

bp = Blueprint("user", __name__)


@bp.route("/")
def home_public():
	cars = current_app.extensions["car_service"].get_cars()
	return render_template("user/home.html", cars=cars)


@bp.route("/user")
@user_required
def home():
	cars = current_app.extensions["car_service"].get_cars()
	return render_template("user/home.html", cars=cars)


@bp.route("/cars")
def cars():
	cars = current_app.extensions["car_service"].get_cars()
	return render_template("user/cars.html", cars=cars)


@bp.route("/vehicles/<car_id>")
def car_detail(car_id):
	car = current_app.extensions["car_service"].get_car(car_id)
	if car is None:
		flash("El carro no existe.", "danger")
		return redirect(url_for("user.cars"))
	return render_template("user/car_detail.html", car=car)


@bp.route("/vehicles/<car_id>/buy", methods=("POST",))
@user_required
def buy_car(car_id):
	try:
		current_app.extensions["purchase_service"].buy_car(
			session_user_id(), car_id
		)
	except ValueError as error:
		flash(str(error), "danger")
	else:
		flash("Compra simulada realizada correctamente.", "success")
	return redirect(url_for("user.car_detail", car_id=car_id))


@bp.route("/user/purchases")
@user_required
def purchases():
	purchases = current_app.extensions["purchase_service"].get_user_purchases(
		session_user_id()
	)
	cars = {car.id: car for car in current_app.extensions["car_service"].get_cars()}
	return render_template("user/purchases.html", purchases=purchases, cars=cars)


def session_user_id():
	from flask import session

	return session["user_id"]
