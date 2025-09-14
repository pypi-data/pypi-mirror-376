from __future__ import annotations

import contextlib
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from anyio import Path as AsyncPath
from PIL import Image

from kreuzberg._extractors._base import Extractor
from kreuzberg._mime_types import IMAGE_MIME_TYPES
from kreuzberg._ocr import get_ocr_backend
from kreuzberg._utils._image_preprocessing import normalize_image_dpi
from kreuzberg._utils._sync import run_sync
from kreuzberg._utils._tmp import create_temp_file
from kreuzberg.exceptions import ValidationError

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Mapping

    from kreuzberg._types import ExtractionResult


class ImageExtractor(Extractor):
    SUPPORTED_MIME_TYPES: ClassVar[set[str]] = IMAGE_MIME_TYPES

    IMAGE_MIME_TYPE_EXT_MAP: ClassVar[Mapping[str, str]] = {
        "image/bmp": "bmp",
        "image/x-bmp": "bmp",
        "image/x-ms-bmp": "bmp",
        "image/gif": "gif",
        "image/jpeg": "jpg",
        "image/pjpeg": "jpg",
        "image/png": "png",
        "image/tiff": "tiff",
        "image/x-tiff": "tiff",
        "image/jp2": "jp2",
        "image/jpx": "jpx",
        "image/jpm": "jpm",
        "image/mj2": "mj2",
        "image/webp": "webp",
        "image/x-portable-anymap": "pnm",
        "image/x-portable-bitmap": "pbm",
        "image/x-portable-graymap": "pgm",
        "image/x-portable-pixmap": "ppm",
    }

    async def extract_bytes_async(self, content: bytes) -> ExtractionResult:
        extension = self._get_extension_from_mime_type(self.mime_type)
        file_path, unlink = await create_temp_file(f".{extension}")
        await AsyncPath(file_path).write_bytes(content)
        try:
            return await self.extract_path_async(file_path)
        finally:
            await unlink()

    async def extract_path_async(self, path: Path) -> ExtractionResult:
        if self.config.ocr_backend is None:
            raise ValidationError("ocr_backend is None, cannot perform OCR")

        image = await run_sync(Image.open, str(path))
        normalized_image, preprocessing_metadata = normalize_image_dpi(image, self.config)

        backend = get_ocr_backend(self.config.ocr_backend)
        result = await backend.process_image(normalized_image, **self.config.get_config_dict())

        if preprocessing_metadata:
            result.metadata["image_preprocessing"] = preprocessing_metadata

        return self._apply_quality_processing(result)

    def extract_bytes_sync(self, content: bytes) -> ExtractionResult:
        extension = self._get_extension_from_mime_type(self.mime_type)
        fd, temp_path = tempfile.mkstemp(suffix=f".{extension}")

        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content)

            return self.extract_path_sync(Path(temp_path))
        finally:
            with contextlib.suppress(OSError):
                Path(temp_path).unlink()

    def extract_path_sync(self, path: Path) -> ExtractionResult:
        if self.config.ocr_backend is None:
            raise ValidationError("ocr_backend is None, cannot perform OCR")

        image = Image.open(str(path))
        normalized_image, preprocessing_metadata = normalize_image_dpi(image, self.config)

        backend = get_ocr_backend(self.config.ocr_backend)
        result = backend.process_image_sync(normalized_image, **self.config.get_config_dict())

        if preprocessing_metadata:
            result.metadata["image_preprocessing"] = preprocessing_metadata

        return self._apply_quality_processing(result)

    def _get_extension_from_mime_type(self, mime_type: str) -> str:
        if mime_type in self.IMAGE_MIME_TYPE_EXT_MAP:
            return self.IMAGE_MIME_TYPE_EXT_MAP[mime_type]

        for k, v in self.IMAGE_MIME_TYPE_EXT_MAP.items():
            if k.startswith(mime_type):
                return v

        raise ValidationError("unsupported mimetype", context={"mime_type": mime_type})
