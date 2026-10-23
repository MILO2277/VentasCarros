from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from concurrent.futures import ThreadPoolExecutor

from PIL import Image
from application.seed_catalog import seed_initial_cars
from application.services.car_service import CarService
from application.services.purchase_service import PurchaseService
from domain.entities.car import Car
from domain.entities.role import Role
from flaskr import create_app
from infrastructure.memory.repositories import (
	InMemoryCarRepository,
	InMemoryPurchaseRepository,
	InMemoryUserRepository,
)
from infrastructure.local.image_storage import LocalImageStorage


class WebApplicationTests(unittest.TestCase):
	def setUp(self):
		self.upload_directory = TemporaryDirectory()
		self.static_directory = Path(self.upload_directory.name) / "static"
		self.image_storage = LocalImageStorage(self.static_directory / "uploads" / "cars")
		self.repositories = (
			InMemoryUserRepository(),
			InMemoryCarRepository(),
			None,
		)
		self.repositories = (
			self.repositories[0],
			self.repositories[1],
			InMemoryPurchaseRepository(self.repositories[1]),
		)
		self.app = create_app({
			"TESTING": True,
			"WTF_CSRF_ENABLED": False,
			"REPOSITORY_BACKEND": "memory",
			"REPOSITORIES": self.repositories,
			"IMAGE_STORAGE": self.image_storage,
			"STATIC_FOLDER": str(self.static_directory),
		})
		self.client = self.app.test_client()

	def tearDown(self):
		self.upload_directory.cleanup()

	@staticmethod
	def valid_image(filename="car.png", image_format="PNG", size=(4, 4)):
		buffer = BytesIO()
		Image.new("RGB", size, color="red").save(buffer, format=image_format)
		buffer.seek(0)
		return (buffer, filename)

	def register(self, email="person@example.com"):
		return self.client.post("/register", data={
			"name": "Test Person",
			"email": email,
			"password": "secure-pass-123",
			"confirm_password": "secure-pass-123",
		})

	def login(self, email="person@example.com"):
		return self.client.post("/login", data={
			"email": email,
			"password": "secure-pass-123",
		})

	def test_registration_login_and_duplicate_email(self):
		self.assertEqual(self.register().status_code, 302)
		user = self.repositories[0].get_by_email("person@example.com")
		self.assertNotEqual(user.password, "secure-pass-123")
		self.assertEqual(self.register().status_code, 200)
		self.assertEqual(self.login().status_code, 302)
		self.assertEqual(self.client.get("/user/purchases").status_code, 200)

	def test_administrator_routes_require_database_role(self):
		self.assertEqual(self.client.get("/admin/cars").status_code, 302)
		self.register()
		self.login()
		self.assertEqual(self.client.get("/admin/cars").status_code, 302)

		service = self.app.extensions["auth_service"]
		service.register_first_admin("Admin", "admin@example.com", "secure-admin-123")
		self.client.post("/logout")
		self.client.post("/login", data={
			"email": "admin@example.com",
			"password": "secure-admin-123",
		})
		self.assertEqual(self.client.get("/admin/cars").status_code, 200)

	def test_admin_car_create_update_and_delete(self):
		self.app.extensions["auth_service"].register_first_admin(
			"Admin", "admin@example.com", "secure-admin-123"
		)
		self.client.post("/login", data={
			"email": "admin@example.com",
			"password": "secure-admin-123",
		})
		data = {
			"brand": "Test", "model": "Car", "year": "2025", "price": "25000",
			"description": "Valid test vehicle",
			"available": "on",
		}
		self.assertEqual(self.client.post(
			"/admin/cars/new",
			data={**data, "image_file": self.valid_image()},
			content_type="multipart/form-data",
		).status_code, 302)
		car = next(car for car in self.repositories[1].get_all() if car.brand == "Test")
		original_path = car.image
		self.assertTrue(original_path.startswith("uploads/cars/"))
		catalog_response = self.client.get("/cars")
		self.assertIn(f"/static/{original_path}".encode(), catalog_response.data)
		detail_response = self.client.get(f"/vehicles/{car.id}")
		self.assertIn(f"/static/{original_path}".encode(), detail_response.data)
		edit_response = self.client.get(f"/admin/cars/{car.id}/edit")
		self.assertIn(f"/static/{original_path}".encode(), edit_response.data)
		image_response = self.client.get(f"/static/{original_path}")
		self.assertEqual(image_response.status_code, 200)
		self.assertEqual(image_response.mimetype, "image/png")
		self.assertTrue(image_response.get_data())
		image_response.close()
		self.assertEqual(self.client.post(
			f"/admin/cars/{car.id}/edit",
			data={**data, "model": "Updated"},
			content_type="multipart/form-data",
		).status_code, 302)
		self.assertEqual(self.repositories[1].get_by_id(car.id).model, "Updated")
		self.assertEqual(self.repositories[1].get_by_id(car.id).image, original_path)
		self.assertEqual(self.client.post(
			f"/admin/cars/{car.id}/edit",
			data={**data, "model": "Updated", "image_file": self.valid_image("replacement.webp", "WEBP")},
			content_type="multipart/form-data",
		).status_code, 302)
		updated_car = self.repositories[1].get_by_id(car.id)
		self.assertNotEqual(updated_car.image, original_path)
		self.assertTrue((self.static_directory / original_path).is_file())
		replacement_response = self.client.get(f"/static/{updated_car.image}")
		self.assertEqual(replacement_response.status_code, 200)
		replacement_response.get_data()
		replacement_response.close()
		self.assertEqual(self.client.post(f"/admin/cars/{car.id}/delete").status_code, 302)
		self.assertIsNone(self.repositories[1].get_by_id(car.id))

	def test_external_image_url_remains_compatible(self):
		legacy_car = self.repositories[1].create(Car(
			0, "Legacy", "Vehicle", 2020, 12000, "External image",
			"https://images.example.test/legacy.jpg", True,
		))
		response = self.client.get(f"/vehicles/{legacy_car.id}")
		self.assertEqual(response.status_code, 200)
		self.assertIn(b"https://images.example.test/legacy.jpg", response.data)

	def test_upload_rejects_invalid_and_oversized_images(self):
		invalid = BytesIO(b"not an image")
		with self.assertRaisesRegex(ValueError, "imagen válida"):
			self.image_storage.save(invalid, "invalid.png")
		oversized = BytesIO(b"x" * (5 * 1024 * 1024 + 1))
		with self.assertRaisesRegex(ValueError, "5 MB"):
			self.image_storage.save(oversized, "large.png")

	def test_failed_repository_write_removes_new_upload(self):
		class FailingCarRepository:
			def create(self, _car):
				raise RuntimeError("simulated persistence failure")

		service = CarService(FailingCarRepository(), self.image_storage)
		with self.assertRaisesRegex(RuntimeError, "persistence failure"):
			service.create_car(
				"Test", "Car", 2025, 100, "Vehicle", image_file=self.valid_image()[0],
				image_filename="car.png",
			)
		self.assertEqual(list((self.static_directory / "uploads" / "cars").iterdir()), [])

	def test_purchase_is_single_winner_and_persists_both_changes(self):
		self.register()
		self.login()
		car = self.repositories[1].get_all()[0]
		self.assertEqual(self.client.post(f"/vehicles/{car.id}/buy").status_code, 302)
		self.assertFalse(self.repositories[1].get_by_id(car.id).available)
		self.assertEqual(len(self.repositories[2].get_by_user_id(1)), 1)
		with self.assertRaises(ValueError):
			PurchaseService(self.repositories[2], self.repositories[1]).buy_car(2, car.id)
		self.assertEqual(len(self.repositories[2].get_by_user_id(2)), 0)

	def test_concurrent_purchase_has_exactly_one_winner(self):
		car = self.repositories[1].get_all()[0]
		service = PurchaseService(self.repositories[2], self.repositories[1])

		def buy(user_id):
			try:
				return service.buy_car(user_id, car.id)
			except ValueError:
				return None

		with ThreadPoolExecutor(max_workers=2) as executor:
			results = list(executor.map(buy, (101, 102)))
		self.assertEqual(sum(result is not None for result in results), 1)
		self.assertEqual(len(self.repositories[2].get_by_user_id(101)) + len(self.repositories[2].get_by_user_id(102)), 1)
		self.assertFalse(self.repositories[1].get_by_id(car.id).available)

	def test_seed_command_is_repeatable_and_keeps_existing_documents(self):
		users = InMemoryUserRepository()
		cars = InMemoryCarRepository()
		repositories = (users, cars, InMemoryPurchaseRepository(cars))
		app = create_app({
			"TESTING": True,
			"WTF_CSRF_ENABLED": False,
			"REPOSITORY_BACKEND": "firestore",
			"REPOSITORIES": repositories,
		})
		runner = app.test_cli_runner()
		first = runner.invoke(args=["seed-cars"])
		second = runner.invoke(args=["seed-cars"])
		self.assertEqual(first.exit_code, 0, first.output)
		self.assertIn("10 creados", first.output)
		self.assertEqual(second.exit_code, 0, second.output)
		self.assertIn("10 existentes omitidos", second.output)
		self.assertEqual(len(cars.get_all()), 10)

	def test_seed_backfills_missing_copy_without_changing_sale_state_or_price(self):
		cars = InMemoryCarRepository()
		incomplete_car = cars.create(Car(
			id="test-toyota", brand="Toyota", model="Corolla", year=2023,
			price=76543210, description="", image="", available=False,
		))
		service = CarService(cars)
		result = seed_initial_cars(service)
		toyota = cars.get_by_id(incomplete_car.id)
		self.assertEqual(result, {"created": 9, "updated": 1, "skipped": 0, "failed": 0})
		self.assertEqual(toyota.price, 76543210)
		self.assertFalse(toyota.available)
		self.assertTrue(toyota.description)
		self.assertTrue(toyota.image.startswith("https://"))

	def test_create_admin_command_hides_password_and_refuses_second_admin(self):
		app = create_app({
			"TESTING": True,
			"WTF_CSRF_ENABLED": False,
			"REPOSITORY_BACKEND": "firestore",
			"REPOSITORIES": self.repositories,
		})
		runner = app.test_cli_runner()
		result = runner.invoke(
			args=["create-admin"],
			input="First Admin\nadmin@example.com\nsecure-admin-123\nsecure-admin-123\n",
		)
		self.assertEqual(result.exit_code, 0, result.output)
		self.assertNotIn("secure-admin-123", result.output)
		admin = self.repositories[0].get_by_email("admin@example.com")
		self.assertEqual(admin.role, Role.ADMIN)
		self.assertNotEqual(admin.password, "secure-admin-123")
		second = runner.invoke(
			args=["create-admin"],
			input="Another Admin\nanother@example.com\nsecure-admin-456\nsecure-admin-456\n",
		)
		self.assertNotEqual(second.exit_code, 0)
		self.assertIn("Ya existe un administrador", second.output)

	def test_csrf_rejects_post_without_token(self):
		csrf_app = create_app({
			"TESTING": True,
			"WTF_CSRF_ENABLED": True,
			"REPOSITORY_BACKEND": "memory",
		})
		response = csrf_app.test_client().post("/login", data={
			"email": "person@example.com",
			"password": "secure-pass-123",
		})
		self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
	unittest.main()