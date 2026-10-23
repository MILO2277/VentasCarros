import os
import secrets

import click
from dotenv import load_dotenv
from flask import Flask, render_template, session
from flask_wtf.csrf import CSRFProtect

from domain.entities.role import Role
from application.services.auth_service import AuthService
from application.services.car_service import CarService
from application.services.catalog_service import CatalogService
from application.services.purchase_service import PurchaseService
from application.services.purchase_report_service import PurchaseReportService
from application.seed_catalog import seed_initial_cars
from infrastructure.memory.repositories import (
	InMemoryCarRepository,
	InMemoryPurchaseRepository,
	InMemoryUserRepository,
)
from infrastructure.local.image_storage import LocalImageStorage


def create_app(test_config=None):
	load_dotenv()
	app = Flask(__name__, static_folder=(test_config or {}).get("STATIC_FOLDER", "static"))
	production = os.getenv("FLASK_ENV", "development").lower() == "production"
	secret_key = os.getenv("FLASK_SECRET_KEY")
	if production and not secret_key:
		raise RuntimeError("FLASK_SECRET_KEY es obligatoria en producción.")
	app.config.from_mapping(
		SECRET_KEY=secret_key or secrets.token_hex(32),
		DEBUG=not production and os.getenv("FLASK_DEBUG", "").lower() in {"1", "true", "yes"},
		REPOSITORY_BACKEND=os.getenv("REPOSITORY_BACKEND", "memory").lower(),
		FIRESTORE_PROJECT_ID=os.getenv("FIRESTORE_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT"),
		MAX_CONTENT_LENGTH=5 * 1024 * 1024 + 64 * 1024,
		SESSION_COOKIE_HTTPONLY=True,
		SESSION_COOKIE_SAMESITE="Lax",
		SESSION_COOKIE_SECURE=production,
	)
	if test_config:
		app.config.update(test_config)
	CSRFProtect(app)

	@app.errorhandler(413)
	def request_too_large(_error):
		return render_template("errors/413.html"), 413

	configured_repositories = app.config.get("REPOSITORIES")
	if configured_repositories is None:
		configured_repositories = build_repositories(app.config)
	user_repository, car_repository, purchase_repository = configured_repositories
	image_storage = app.config.get("IMAGE_STORAGE") or LocalImageStorage(
		os.path.join(app.static_folder, "uploads", "cars")
	)

	auth_service = AuthService(user_repository)
	car_service = CarService(car_repository, image_storage)
	catalog_service = CatalogService(car_repository)
	purchase_service = PurchaseService(purchase_repository, car_repository)
	purchase_report_service = PurchaseReportService(purchase_repository)
	app.extensions["repositories"] = {
		"users": user_repository,
		"cars": car_repository,
		"purchases": purchase_repository,
	}
	app.extensions["auth_service"] = auth_service
	app.extensions["car_service"] = car_service
	app.extensions["catalog_service"] = catalog_service
	app.extensions["purchase_service"] = purchase_service
	app.extensions["purchase_report_service"] = purchase_report_service
	app.extensions["image_storage"] = image_storage

	if app.config["REPOSITORY_BACKEND"] == "memory":
		seed_initial_cars(car_service)

	from flaskr.routes.admin import bp as admin_bp
	from flaskr.routes.auth import bp as auth_bp
	from flaskr.routes.user import bp as user_bp

	app.register_blueprint(auth_bp)
	app.register_blueprint(user_bp)
	app.register_blueprint(admin_bp)

	@app.context_processor
	def inject_current_user():
		user = None
		if session.get("user_id"):
			user = auth_service.find_by_id(session["user_id"])
		return {"current_user": user, "image_url": image_url}

	def image_url(image_reference):
		if image_reference and image_reference.startswith("uploads/cars/"):
			from flask import url_for
			return url_for("static", filename=image_reference)
		return image_reference

	@app.cli.command("seed-cars")
	def seed_cars_command():
		if app.config["REPOSITORY_BACKEND"] != "firestore":
			raise click.ClickException("Este comando requiere REPOSITORY_BACKEND=firestore.")
		try:
			result = seed_initial_cars(car_service)
		except Exception as error:
			app.logger.exception("Falló la carga inicial de carros")
			raise click.ClickException("No se pudo consultar Firestore; revisa la configuración y los logs.") from error
		click.echo(
			f"Carga finalizada: {result['created']} creados, "
			f"{result['updated']} completados, {result['skipped']} existentes omitidos, "
			f"{result['failed']} errores."
		)
		if result["failed"]:
			raise click.ClickException("Uno o más carros no pudieron cargarse.")

	@app.cli.command("create-admin")
	def create_admin_command():
		if app.config["REPOSITORY_BACKEND"] != "firestore":
			raise click.ClickException("Este comando requiere REPOSITORY_BACKEND=firestore.")
		name = click.prompt("Nombre del administrador")
		email = click.prompt("Correo del administrador")
		password = click.prompt("Contraseña nueva", hide_input=True, confirmation_prompt=True)
		try:
			auth_service.register_first_admin(name, email, password)
		except ValueError as error:
			raise click.ClickException(str(error)) from error
		click.echo("Administrador creado correctamente.")

	return app


def build_repositories(config):
	backend = config["REPOSITORY_BACKEND"]
	if backend == "memory":
		car_repository = InMemoryCarRepository()
		return (
			InMemoryUserRepository(),
			car_repository,
			InMemoryPurchaseRepository(car_repository),
		)
	if backend == "firestore":
		from infrastructure.firestore.client import create_firestore_client
		from infrastructure.firestore.repositories import (
			FirestoreCarRepository,
			FirestorePurchaseRepository,
			FirestoreUserRepository,
		)

		client = create_firestore_client(config.get("FIRESTORE_PROJECT_ID"))
		return (
			FirestoreUserRepository(client),
			FirestoreCarRepository(client),
			FirestorePurchaseRepository(client),
		)
	raise ValueError("REPOSITORY_BACKEND debe ser 'memory' o 'firestore'.")
