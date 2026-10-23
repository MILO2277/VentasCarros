from functools import wraps

from flask import current_app, flash, redirect, session, url_for

from domain.entities.role import Role


def login_required(view):
	@wraps(view)
	def wrapped_view(*args, **kwargs):
		if "user_id" not in session:
			flash("Inicia sesión para continuar.", "warning")
			return redirect(url_for("auth.login"))
		return view(*args, **kwargs)

	return wrapped_view


def user_required(view):
	@wraps(view)
	def wrapped_view(*args, **kwargs):
		user = current_app.extensions["auth_service"].find_by_id(session.get("user_id"))
		if user is None or user.role != Role.USER:
			flash("Esta sección es para usuarios registrados.", "warning")
			return redirect(url_for("admin.dashboard"))
		return view(*args, **kwargs)

	return login_required(wrapped_view)


def admin_required(view):
	@wraps(view)
	def wrapped_view(*args, **kwargs):
		user = current_app.extensions["auth_service"].find_by_id(session.get("user_id"))
		if user is None or user.role != Role.ADMIN:
			flash("No tienes permisos para acceder a esta sección.", "danger")
			return redirect(url_for("user.home"))
		return view(*args, **kwargs)

	return login_required(wrapped_view)
