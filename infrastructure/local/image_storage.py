from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from PIL import Image, UnidentifiedImageError


class LocalImageStorage:
	MAX_IMAGE_BYTES = 5 * 1024 * 1024
	FORMAT_EXTENSIONS = {
		"JPEG": ".jpg",
		"PNG": ".png",
		"WEBP": ".webp",
	}

	def __init__(self, upload_directory: Path):
		self._upload_directory = Path(upload_directory).resolve()

	def save(self, file_stream: BinaryIO, original_filename: str) -> str:
		if not original_filename or not Path(original_filename).suffix:
			raise ValueError("Selecciona una imagen JPG, JPEG, PNG o WEBP.")

		content = file_stream.read(self.MAX_IMAGE_BYTES + 1)
		if len(content) > self.MAX_IMAGE_BYTES:
			raise ValueError("La imagen supera el tamaño máximo de 5 MB.")
		if not content:
			raise ValueError("El archivo seleccionado está vacío.")

		try:
			with Image.open(BytesIO(content)) as image:
				image_format = image.format
				image.verify()
		except (UnidentifiedImageError, OSError, ValueError) as error:
			raise ValueError("El archivo no contiene una imagen válida.") from error

		extension = self.FORMAT_EXTENSIONS.get(image_format)
		if extension is None:
			raise ValueError("Formato no permitido. Usa JPG, JPEG, PNG o WEBP.")
		if Path(original_filename).suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
			raise ValueError("Formato no permitido. Usa JPG, JPEG, PNG o WEBP.")

		self._upload_directory.mkdir(parents=True, exist_ok=True)
		filename = f"{uuid4().hex}{extension}"
		destination = (self._upload_directory / filename).resolve()
		if destination.parent != self._upload_directory:
			raise ValueError("Nombre de archivo no válido.")
		destination.write_bytes(content)
		return f"uploads/cars/{filename}"

	def delete(self, stored_path: str) -> None:
		prefix = "uploads/cars/"
		if not stored_path.startswith(prefix):
			return
		candidate = (self._upload_directory / stored_path[len(prefix):]).resolve()
		if candidate.parent == self._upload_directory and candidate.is_file():
			candidate.unlink()