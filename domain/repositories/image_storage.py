from typing import BinaryIO, Protocol


class ImageStorage(Protocol):
	def save(self, file_stream: BinaryIO, original_filename: str) -> str: ...

	def delete(self, stored_path: str) -> None: ...