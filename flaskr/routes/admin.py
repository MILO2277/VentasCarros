from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from flaskr.routes import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/")
@admin_required
def dashboard():
	cars = current_app.extensions["car_service"].get_cars()
	return render_template("admin/dashboard.html", cars_count=len(cars))


@bp.route("/cars")
@admin_required
def cars():
	cars = current_app.extensions["car_service"].get_cars()
	return render_template("admin/cars.html", cars=cars)


@bp.route("/cars/new", methods=("GET", "POST"))
@admin_required
def create_car():
	if request.method == "POST":
		try:
			current_app.extensions["car_service"].create_car(
				**car_form_data(), **uploaded_image_data()
			)
		except ValueError as error:
			flash(str(error), "danger")
			return render_template("admin/car_form.html", car=None, title="Agregar carro"), 400
		except Exception:
			current_app.logger.exception("No se pudo guardar el carro")
			flash("No se pudo guardar el carro. Inténtalo de nuevo.", "danger")
			return render_template("admin/car_form.html", car=None, title="Agregar carro"), 500
		flash("Carro creado correctamente.", "success")
		return redirect(url_for("admin.cars"))
	return render_template("admin/car_form.html", car=None, title="Agregar carro")


@bp.route("/cars/<car_id>/edit", methods=("GET", "POST"))
@admin_required
def edit_car(car_id):
	car_service = current_app.extensions["car_service"]
	car = car_service.get_car(car_id)
	if car is None:
		flash("El carro no existe.", "danger")
		return redirect(url_for("admin.cars"))
	if request.method == "POST":
		try:
			car_service.update_car(car_id, **car_form_data(), **uploaded_image_data())
		except ValueError as error:
			flash(str(error), "danger")
			return render_template("admin/car_form.html", car=car, title="Editar carro"), 400
		except Exception:
			current_app.logger.exception("No se pudo actualizar el carro")
			flash("No se pudo actualizar el carro. Inténtalo de nuevo.", "danger")
			return render_template("admin/car_form.html", car=car, title="Editar carro"), 500
		flash("Carro actualizado correctamente.", "success")
		return redirect(url_for("admin.cars"))
	return render_template("admin/car_form.html", car=car, title="Editar carro")


@bp.route("/cars/<car_id>/delete", methods=("POST",))
@admin_required
def delete_car(car_id):
	current_app.extensions["car_service"].delete_car(car_id)
	flash("Carro eliminado correctamente.", "success")
	return redirect(url_for("admin.cars"))


def car_form_data():
	try:
		year = int(request.form.get("year", ""))
		price = float(request.form.get("price", ""))
	except ValueError as error:
		raise ValueError("Año y precio deben ser valores numéricos válidos.") from error
	return {
		"brand": request.form.get("brand", "").strip(),
		"model": request.form.get("model", "").strip(),
		"year": year,
		"price": price,
		"description": request.form.get("description", "").strip(),
		"available": request.form.get("available") == "on",
	}


def uploaded_image_data():
	image = request.files.get("image_file")
	if image is None or not image.filename:
		return {}
	return {"image_file": image.stream, "image_filename": image.filename}
