from __future__ import annotations

import contextlib
import os
import tempfile
from dataclasses import asdict
from multiprocessing import cpu_count
from pathlib import Path
from re import Pattern
from re import compile as compile_regex
from typing import TYPE_CHECKING, ClassVar, cast

import anyio
import pypdfium2
from anyio import Path as AsyncPath
from playa import parse

from kreuzberg._extractors._base import Extractor
from kreuzberg._mime_types import PDF_MIME_TYPE, PLAIN_TEXT_MIME_TYPE
from kreuzberg._ocr import get_ocr_backend
from kreuzberg._playa import extract_pdf_metadata, extract_pdf_metadata_sync
from kreuzberg._types import EasyOCRConfig, ExtractionResult, Metadata, OcrBackendType, PaddleOCRConfig, TesseractConfig
from kreuzberg._utils._errors import create_error_context, should_retry
from kreuzberg._utils._image_preprocessing import calculate_optimal_dpi
from kreuzberg._utils._pdf_lock import pypdfium_file_lock
from kreuzberg._utils._string import normalize_spaces
from kreuzberg._utils._sync import run_sync, run_taskgroup_batched
from kreuzberg._utils._table import generate_table_summary
from kreuzberg._utils._tmp import create_temp_file
from kreuzberg.exceptions import ParsingError

if TYPE_CHECKING:  # pragma: no cover
    from PIL.Image import Image
    from playa.document import Document


class PDFExtractor(Extractor):
    SUPPORTED_MIME_TYPES: ClassVar[set[str]] = {PDF_MIME_TYPE}
    CORRUPTED_PATTERN: ClassVar[Pattern[str]] = compile_regex(r"[\x00-\x08\x0B-\x0C\x0E-\x1F]|\uFFFD")
    SHORT_TEXT_THRESHOLD: ClassVar[int] = 50
    MINIMUM_CORRUPTED_RESULTS: ClassVar[int] = 2

    async def extract_bytes_async(self, content: bytes) -> ExtractionResult:
        file_path, unlink = await create_temp_file(".pdf")
        await AsyncPath(file_path).write_bytes(content)
        try:
            metadata = await self._extract_metadata_with_password_attempts(content)
            result = await self.extract_path_async(file_path)

            result.metadata = metadata
            return result
        finally:
            await unlink()

    async def extract_path_async(self, path: Path) -> ExtractionResult:
        content_bytes = await AsyncPath(path).read_bytes()

        result: ExtractionResult | None = None

        if not self.config.force_ocr:
            try:
                content = await self._extract_pdf_searchable_text(path)
                if self._validate_extracted_text(content):
                    result = ExtractionResult(content=content, mime_type=PLAIN_TEXT_MIME_TYPE, metadata={}, chunks=[])
            except ParsingError:
                pass

        if not result and self.config.ocr_backend is not None:
            result = await self._extract_pdf_text_with_ocr(path, self.config.ocr_backend)

        if not result:
            result = ExtractionResult(content="", mime_type=PLAIN_TEXT_MIME_TYPE, metadata={}, chunks=[])

        result.metadata = await self._extract_metadata_with_password_attempts(content_bytes)

        if self.config.extract_tables:
            # GMFT is optional dependency ~keep
            try:
                from kreuzberg._gmft import extract_tables  # noqa: PLC0415

                result.tables = await extract_tables(path, self.config.gmft_config)
            except ImportError:  # pragma: no cover
                result.tables = []

            if result.tables:
                table_summary = generate_table_summary(result.tables)
                result.metadata = result.metadata | {
                    "table_count": table_summary["table_count"],
                    "tables_summary": f"Document contains {table_summary['table_count']} tables "
                    f"across {table_summary['pages_with_tables']} pages with "
                    f"{table_summary['total_rows']} total rows",
                }

        return self._apply_quality_processing(result)

    def extract_bytes_sync(self, content: bytes) -> ExtractionResult:
        fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(content)

            result = self.extract_path_sync(Path(temp_path))

            metadata = self._extract_metadata_with_password_attempts_sync(content)
            result.metadata = metadata

            return result
        finally:
            with contextlib.suppress(OSError):
                Path(temp_path).unlink()

    def extract_path_sync(self, path: Path) -> ExtractionResult:
        try:
            text = self._extract_pdf_searchable_text_sync(path)
        except ParsingError:
            text = ""

        if (self.config.force_ocr or not self._validate_extracted_text(text)) and self.config.ocr_backend is not None:
            text = self._extract_pdf_with_ocr_sync(path)

        tables = []
        if self.config.extract_tables:
            # GMFT is optional dependency ~keep
            try:
                from kreuzberg._gmft import extract_tables_sync  # noqa: PLC0415

                tables = extract_tables_sync(path)
            except ImportError:
                tables = []

        if not self.config.force_ocr and self._validate_extracted_text(text):
            text = self._extract_with_playa_sync(path, fallback_text=text)

        text = normalize_spaces(text)

        result = ExtractionResult(
            content=text,
            mime_type=PLAIN_TEXT_MIME_TYPE,
            metadata={},
            tables=tables,
            chunks=[],
        )

        if tables:
            table_summary = generate_table_summary(tables)
            result.metadata = result.metadata | {
                "table_count": table_summary["table_count"],
                "tables_summary": f"Document contains {table_summary['table_count']} tables "
                f"across {table_summary['pages_with_tables']} pages with "
                f"{table_summary['total_rows']} total rows",
            }

        return self._apply_quality_processing(result)

    def _validate_extracted_text(self, text: str, corruption_threshold: float = 0.05) -> bool:
        if not text or not text.strip():
            return False

        corruption_matches = self.CORRUPTED_PATTERN.findall(text)

        if len(text) < self.SHORT_TEXT_THRESHOLD:
            return len(corruption_matches) <= self.MINIMUM_CORRUPTED_RESULTS

        return (len(corruption_matches) / len(text)) < corruption_threshold

    async def _convert_pdf_to_images(self, input_file: Path) -> list[Image]:
        document: pypdfium2.PdfDocument | None = None
        last_error = None

        for attempt in range(3):  # Try up to 3 times  # ~keep
            try:
                with pypdfium_file_lock(input_file):
                    document = await run_sync(pypdfium2.PdfDocument, str(input_file))
                    images = []
                    for page in cast("pypdfium2.PdfDocument", document):
                        width, height = page.get_size()

                        if self.config.auto_adjust_dpi:
                            optimal_dpi = calculate_optimal_dpi(
                                page_width=width,
                                page_height=height,
                                target_dpi=self.config.target_dpi,
                                max_dimension=self.config.max_image_dimension,
                                min_dpi=self.config.min_dpi,
                                max_dpi=self.config.max_dpi,
                            )
                        else:
                            optimal_dpi = self.config.target_dpi

                        scale = optimal_dpi / 72.0

                        images.append(page.render(scale=scale).to_pil())
                    return images
            except pypdfium2.PdfiumError as e:  # noqa: PERF203
                last_error = e
                if not should_retry(e, attempt + 1):
                    raise ParsingError(
                        "Could not convert PDF to images",
                        context=create_error_context(
                            operation="convert_pdf_to_images",
                            file_path=input_file,
                            error=e,
                            attempt=attempt + 1,
                        ),
                    ) from e
                # Wait before retry with exponential backoff  # ~keep
                await anyio.sleep(0.5 * (attempt + 1))
            finally:
                if document:
                    with pypdfium_file_lock(input_file), contextlib.suppress(Exception):
                        await run_sync(document.close)

        # All retries failed  # ~keep
        raise ParsingError(
            "Could not convert PDF to images after retries",
            context=create_error_context(
                operation="convert_pdf_to_images",
                file_path=input_file,
                error=last_error,
                attempts=3,
            ),
        ) from last_error

    async def _extract_pdf_text_with_ocr(self, input_file: Path, ocr_backend: OcrBackendType) -> ExtractionResult:
        images = await self._convert_pdf_to_images(input_file)
        backend = get_ocr_backend(ocr_backend)
        ocr_results = await run_taskgroup_batched(
            *[backend.process_image(image, **self.config.get_config_dict()) for image in images],
            batch_size=cpu_count(),
        )
        content = "\n".join(result.content for result in ocr_results)

        return ExtractionResult(content=content, mime_type=PLAIN_TEXT_MIME_TYPE, metadata={}, chunks=[])

    @staticmethod
    async def _extract_pdf_searchable_text(input_file: Path) -> str:
        document: pypdfium2.PdfDocument | None = None
        try:
            with pypdfium_file_lock(input_file):
                document = await run_sync(pypdfium2.PdfDocument, str(input_file))
                pages_content = []
                page_errors = []

                for i, page in enumerate(cast("pypdfium2.PdfDocument", document)):
                    try:
                        text_page = page.get_textpage()
                        page_content = text_page.get_text_bounded()
                        pages_content.append(page_content)
                    except Exception as e:  # noqa: PERF203, BLE001
                        page_errors.append({"page": i + 1, "error": str(e)})
                        pages_content.append(f"[Error extracting page {i + 1}]")

                text = "\n".join(pages_content)
                has_content = bool(text.strip())

                if page_errors and has_content:
                    return normalize_spaces(text)
                if not has_content:
                    raise ParsingError(
                        "Could not extract any text from PDF",
                        context=create_error_context(
                            operation="extract_pdf_searchable_text",
                            file_path=input_file,
                            page_errors=page_errors,
                        ),
                    )

                return normalize_spaces(text)
        except pypdfium2.PdfiumError as e:
            raise ParsingError(
                "Could not extract text from PDF file",
                context=create_error_context(
                    operation="extract_pdf_searchable_text",
                    file_path=input_file,
                    error=e,
                ),
            ) from e
        finally:
            if document:
                with pypdfium_file_lock(input_file), contextlib.suppress(Exception):
                    await run_sync(document.close)

    def _extract_pdf_searchable_text_sync(self, path: Path) -> str:
        pdf = None
        try:
            with pypdfium_file_lock(path):
                pdf = pypdfium2.PdfDocument(str(path))
                pages_text = []
                for page in pdf:
                    text_page = page.get_textpage()
                    text = text_page.get_text_bounded()
                    pages_text.append(text)
                    text_page.close()
                    page.close()
                return "\n".join(pages_text)
        except Exception as e:
            raise ParsingError(f"Failed to extract PDF text: {e}") from e
        finally:
            if pdf:
                with pypdfium_file_lock(path), contextlib.suppress(Exception):
                    pdf.close()

    def _extract_pdf_with_ocr_sync(self, path: Path) -> str:
        pdf = None
        try:
            images = []
            with pypdfium_file_lock(path):
                pdf = pypdfium2.PdfDocument(str(path))
                for page in pdf:
                    bitmap = page.render(scale=200 / 72)
                    pil_image = bitmap.to_pil()
                    images.append(pil_image)
                    bitmap.close()
                    page.close()

            return self._process_pdf_images_with_ocr_direct(images)

        except Exception as e:
            raise ParsingError(f"Failed to OCR PDF: {e}") from e
        finally:
            if pdf:
                with pypdfium_file_lock(path), contextlib.suppress(Exception):
                    pdf.close()

    def _process_pdf_images_with_ocr(self, image_paths: list[str]) -> str:
        backend = get_ocr_backend(self.config.ocr_backend)
        paths = [Path(p) for p in image_paths]

        match self.config.ocr_backend:
            case "tesseract":
                config = (
                    self.config.ocr_config if isinstance(self.config.ocr_config, TesseractConfig) else TesseractConfig()
                )
                results = backend.process_batch_sync(paths, **asdict(config))
            case "paddleocr":
                paddle_config = (
                    self.config.ocr_config if isinstance(self.config.ocr_config, PaddleOCRConfig) else PaddleOCRConfig()
                )
                results = backend.process_batch_sync(paths, **asdict(paddle_config))
            case "easyocr":
                easy_config = (
                    self.config.ocr_config if isinstance(self.config.ocr_config, EasyOCRConfig) else EasyOCRConfig()
                )
                results = backend.process_batch_sync(paths, **asdict(easy_config))
            case _:
                raise NotImplementedError(f"Sync OCR not implemented for {self.config.ocr_backend}")

        return "\n\n".join(result.content for result in results)

    def _process_pdf_images_with_ocr_direct(self, images: list[Image]) -> str:
        backend = get_ocr_backend(self.config.ocr_backend)

        match self.config.ocr_backend:
            case "tesseract":
                config = (
                    self.config.ocr_config if isinstance(self.config.ocr_config, TesseractConfig) else TesseractConfig()
                )
                results = []
                for image in images:
                    result = backend.process_image_sync(image, **asdict(config))
                    results.append(result)
            case "paddleocr":
                paddle_config = (
                    self.config.ocr_config if isinstance(self.config.ocr_config, PaddleOCRConfig) else PaddleOCRConfig()
                )
                results = []
                for image in images:
                    result = backend.process_image_sync(image, **asdict(paddle_config))
                    results.append(result)
            case "easyocr":
                easy_config = (
                    self.config.ocr_config if isinstance(self.config.ocr_config, EasyOCRConfig) else EasyOCRConfig()
                )
                results = []
                for image in images:
                    result = backend.process_image_sync(image, **asdict(easy_config))
                    results.append(result)
            case _:
                raise NotImplementedError(f"Direct image OCR not implemented for {self.config.ocr_backend}")

        return "\n\n".join(result.content for result in results)

    def _parse_with_password_attempts(self, content: bytes) -> Document:
        if isinstance(self.config.pdf_password, str):
            passwords = [self.config.pdf_password] if self.config.pdf_password else [""]
        else:
            passwords = list(self.config.pdf_password)

        last_exception = None
        for password in passwords:
            try:
                return parse(content, max_workers=1, password=password)
            except Exception as e:  # noqa: PERF203, BLE001
                last_exception = e
                continue

        if last_exception:
            raise last_exception from None

        return parse(content, max_workers=1, password="")

    def _get_passwords_to_try(self) -> list[str]:
        if isinstance(self.config.pdf_password, str):
            return [self.config.pdf_password] if self.config.pdf_password else [""]
        return list(self.config.pdf_password) if self.config.pdf_password else [""]

    async def _extract_metadata_with_password_attempts(self, content: bytes) -> Metadata:
        passwords = self._get_passwords_to_try()

        last_exception = None
        for password in passwords:
            try:
                return await extract_pdf_metadata(content, password=password)
            except Exception as e:  # noqa: PERF203, BLE001
                last_exception = e
                continue

        try:
            return await extract_pdf_metadata(content, password="")
        except Exception:
            if last_exception:
                raise last_exception from None
            raise

    def _extract_metadata_with_password_attempts_sync(self, content: bytes) -> Metadata:
        passwords = self._get_passwords_to_try()

        last_exception = None
        for password in passwords:
            try:
                return extract_pdf_metadata_sync(content, password=password)
            except Exception as e:  # noqa: PERF203, BLE001
                last_exception = e
                continue

        try:
            return extract_pdf_metadata_sync(content, password="")
        except Exception:
            if last_exception:
                raise last_exception from None
            raise

    def _extract_with_playa_sync(self, path: Path, fallback_text: str) -> str:
        with contextlib.suppress(Exception):
            content = path.read_bytes()
            document = self._parse_with_password_attempts(content)

            pages_text = []
            for page in document.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages_text.append(page_text)

            if pages_text:
                return "\n\n".join(pages_text)

        return fallback_text
