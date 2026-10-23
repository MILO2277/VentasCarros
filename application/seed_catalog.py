import logging


INITIAL_CARS = (
	{
		"brand": "Toyota", "model": "Corolla", "year": 2023, "price": 80000000,
		"description": "El Corolla 2023 combina un diseño sobrio con un interior cómodo y un motor eficiente. Es un sedan práctico para el uso diario, con buena reputación por su confiabilidad y bajo costo de mantenimiento.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/67/2023_Toyota_Corolla_Touring_Sports_Hybrid_%28E210%29_IMG_7679.jpg/960px-2023_Toyota_Corolla_Touring_Sports_Hybrid_%28E210%29_IMG_7679.jpg",
	},
	{
		"brand": "Mazda", "model": "3", "year": 2022, "price": 92000000,
		"description": "El Mazda3 2022 destaca por su diseño Kodo, una cabina de buena calidad y una conducción precisa. Su carroceria sedan ofrece una experiencia refinada para quienes buscan un compacto con sensaciones deportivas.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9b/Mazda_3_Axela_sedan_facelift_Shishi_02_2022-05-20.jpg/960px-Mazda_3_Axela_sedan_facelift_Shishi_02_2022-05-20.jpg",
	},
	{
		"brand": "Chevrolet", "model": "Onix", "year": 2024, "price": 76000000,
		"description": "El Chevrolet Onix 2024 es un compacto orientado a la ciudad. Ofrece un tamaño facil de maniobrar, conectividad moderna y un consumo equilibrado para los recorridos diarios.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/4b/Chevrolet_Onix_Turbo_RS_2024.jpg/960px-Chevrolet_Onix_Turbo_RS_2024.jpg",
	},
	{
		"brand": "Ford", "model": "Mustang", "year": 2021, "price": 210000000,
		"description": "El Ford Mustang 2021 conserva la identidad del pony car estadounidense con un capó largo, tracción trasera y una conducción enfocada en el desempeño. Es un deportivo de presencia inconfundible.",
		"image": "https://commons.wikimedia.org/wiki/Special:FilePath/2021%20Ford%20Mustang%20GT.jpg",
	},
	{
		"brand": "Honda", "model": "Civic", "year": 2023, "price": 108000000,
		"description": "El Honda Civic 2023 ofrece un interior amplio para su categoria, manejo estable y una configuracion pensada para el uso diario. Su diseño actual conserva la practicidad que caracteriza al modelo.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/6/63/Honda_Civic_Hybrid_%282022%2C_Europe%29_IAA_2023_1X7A0545_%282%29.jpg/960px-Honda_Civic_Hybrid_%282022%2C_Europe%29_IAA_2023_1X7A0545_%282%29.jpg",
	},
	{
		"brand": "Hyundai", "model": "Tucson", "year": 2023, "price": 138000000,
		"description": "La Hyundai Tucson 2023 es una SUV compacta con postura elevada, espacio para pasajeros y un enfoque familiar. Su diseño exterior angular la diferencia dentro del segmento.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/21/Hyundai_Tucson_%28NX4%29_PHEV_IMG_4375.jpg/960px-Hyundai_Tucson_%28NX4%29_PHEV_IMG_4375.jpg",
	},
	{
		"brand": "Kia", "model": "Sportage", "year": 2023, "price": 145000000,
		"description": "La Kia Sportage 2023 combina una cabina versatil con una posicion de manejo elevada. Es una SUV pensada para ciudad y viajes, con buen espacio interior y una estetica moderna.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/97/2023_Kia_Sportage_%28NQ5%29_in_White%2C_front_left.jpg/960px-2023_Kia_Sportage_%28NQ5%29_in_White%2C_front_left.jpg",
	},
	{
		"brand": "Volkswagen", "model": "Jetta", "year": 2022, "price": 99000000,
		"description": "El Volkswagen Jetta 2022 es un sedan de tamaño compacto con conducción estable, baul amplio y una cabina orientada a la comodidad. Es una alternativa equilibrada para uso familiar.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/00/2022_Volkswagen_Jetta_VII_1X7A0154.jpg/960px-2022_Volkswagen_Jetta_VII_1X7A0154.jpg",
	},
	{
		"brand": "Nissan", "model": "Sentra", "year": 2024, "price": 97000000,
		"description": "El Nissan Sentra 2024 ofrece un habitaculo espacioso, una marcha confortable y el formato practico de un sedan compacto. Su propuesta prioriza comodidad y eficiencia para la ciudad.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/92/2024_Nissan_Sentra_%28B18%29_IMG_4029.jpg/960px-2024_Nissan_Sentra_%28B18%29_IMG_4029.jpg",
	},
	{
		"brand": "Tesla", "model": "Model 3", "year": 2023, "price": 185000000,
		"description": "El Tesla Model 3 2023 es un sedan electrico de cinco puertas con una cabina minimalista y respuesta inmediata del motor electrico. Su autonomia y tecnologia son sus principales argumentos.",
		"image": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/86/Tesla_Model_3_%282023%29_IMG_9488_%28cropped%29.jpg/960px-Tesla_Model_3_%282023%29_IMG_9488_%28cropped%29.jpg",
	},
)


def seed_initial_cars(car_service, logger=None):
	logger = logger or logging.getLogger(__name__)
	existing = {
		(car.brand.casefold(), car.model.casefold(), int(car.year))
		: car
		for car in car_service.get_cars()
	}
	created = 0
	skipped = 0
	updated = 0
	failed = 0
	for data in INITIAL_CARS:
		key = (data["brand"].casefold(), data["model"].casefold(), data["year"])
		existing_car = existing.get(key)
		if existing_car is not None:
			missing_description = not existing_car.description.strip()
			missing_image = not existing_car.image.strip()
			if missing_description or missing_image:
				try:
					car_service.update_car(
						existing_car.id,
						brand=existing_car.brand,
						model=existing_car.model,
						year=existing_car.year,
						price=existing_car.price,
						description=existing_car.description or data["description"],
						image=existing_car.image or data["image"],
						available=existing_car.available,
					)
				except Exception:
					logger.exception("Error al completar carro %s %s %s", *key)
					failed += 1
					continue
				updated += 1
				logger.info("Campos descriptivos completados: %s %s %s", *key)
				continue
			logger.info("Carro existente, se omite: %s %s %s", *key)
			skipped += 1
			continue
		try:
			created_car = car_service.create_car(**data)
		except Exception:
			logger.exception("Error al cargar carro %s %s %s", *key)
			failed += 1
		else:
			existing[key] = created_car
			created += 1
			logger.info("Carro cargado: %s %s %s", *key)
	return {"created": created, "updated": updated, "skipped": skipped, "failed": failed}