from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from domain.entities.role import Role

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=("GET", "POST"))
def login():
	if request.method == "POST":
		email = request.form.get("email", "")
		password = request.form.get("password", "")
		if not email or not password:
			flash("Ingresa tu correo y contraseña.", "danger")
		else:
			auth_service = current_app.extensions["auth_service"]
			user = auth_service.authenticate(email, password)
			if user is None:
				flash("Correo o contraseña incorrectos.", "danger")
			else:
				session.clear()
				session["user_id"] = user.id
				session["role"] = user.role.value
				flash("Sesión iniciada correctamente.", "success")
				if user.role == Role.ADMIN:
					return redirect(url_for("admin.dashboard"))
				return redirect(url_for("user.home"))
	return render_template("auth/login.html")


@bp.route("/register", methods=("GET", "POST"))
def register():
	if request.method == "POST":
		name = request.form.get("name", "")
		email = request.form.get("email", "")
		password = request.form.get("password", "")
		confirm_password = request.form.get("confirm_password", "")
		if password != confirm_password:
			flash("Las contraseñas no coinciden.", "danger")
		else:
			try:
				current_app.extensions["auth_service"].register(name, email, password)
			except ValueError as error:
				flash(str(error), "danger")
			else:
				flash("Registro exitoso. Ahora puedes iniciar sesión.", "success")
				return redirect(url_for("auth.login"))
	return render_template("auth/register.html")


@bp.route("/logout", methods=("POST",))
def logout():
	session.clear()
	flash("Sesión cerrada.", "success")
	return redirect(url_for("user.home"))
