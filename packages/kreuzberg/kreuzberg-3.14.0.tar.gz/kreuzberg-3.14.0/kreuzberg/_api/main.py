from __future__ import annotations

import traceback
from functools import lru_cache
from json import dumps, loads
from typing import TYPE_CHECKING, Annotated, Any, Literal

import msgspec
from typing_extensions import TypedDict

from kreuzberg import (
    EasyOCRConfig,
    ExtractionConfig,
    ExtractionResult,
    KreuzbergError,
    MissingDependencyError,
    PaddleOCRConfig,
    ParsingError,
    TesseractConfig,
    ValidationError,
    batch_extract_bytes,
)
from kreuzberg._config import discover_config

if TYPE_CHECKING:
    from litestar.datastructures import UploadFile


class HealthResponse(TypedDict):
    """Response model for health check endpoint."""

    status: str


class ConfigurationResponse(TypedDict):
    """Response model for configuration endpoint."""

    message: str
    config: dict[str, Any] | None


try:
    from litestar import Litestar, Request, Response, get, post
    from litestar.contrib.opentelemetry import OpenTelemetryConfig, OpenTelemetryPlugin
    from litestar.enums import RequestEncodingType
    from litestar.logging import StructLoggingConfig
    from litestar.openapi.config import OpenAPIConfig
    from litestar.openapi.spec.contact import Contact
    from litestar.openapi.spec.license import License
    from litestar.params import Body
    from litestar.status_codes import (
        HTTP_400_BAD_REQUEST,
        HTTP_422_UNPROCESSABLE_ENTITY,
        HTTP_500_INTERNAL_SERVER_ERROR,
    )
except ImportError as e:  # pragma: no cover
    raise MissingDependencyError.create_for_package(
        dependency_group="litestar",
        functionality="Litestar API and docker container",
        package_name="litestar",
    ) from e


def exception_handler(request: Request[Any, Any, Any], exception: KreuzbergError) -> Response[Any]:
    if isinstance(exception, ValidationError):
        status_code = HTTP_400_BAD_REQUEST
    elif isinstance(exception, ParsingError):
        status_code = HTTP_422_UNPROCESSABLE_ENTITY
    else:
        status_code = HTTP_500_INTERNAL_SERVER_ERROR

    message = str(exception)
    details = dumps(exception.context)

    if request.app.logger:
        request.app.logger.error(
            "API error",
            method=request.method,
            url=str(request.url),
            status_code=status_code,
            message=message,
            context=exception.context,
        )

    return Response(
        content={"message": message, "details": details},
        status_code=status_code,
    )


def general_exception_handler(request: Request[Any, Any, Any], exception: Exception) -> Response[Any]:
    error_type = type(exception).__name__
    error_message = str(exception)
    traceback_str = traceback.format_exc()

    if request.app.logger:
        request.app.logger.error(
            "Unhandled exception",
            method=request.method,
            url=str(request.url),
            error_type=error_type,
            message=error_message,
            traceback=traceback_str,
        )

    return Response(
        content={
            "error_type": error_type,
            "message": error_message,
            "traceback": traceback_str,
            "debug": "This is a temporary debug handler",
        },
        status_code=HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _convert_value_type(current_value: Any, new_value: Any) -> Any:
    if isinstance(current_value, bool):
        if isinstance(new_value, str):
            return str(new_value).lower() in ("true", "1", "yes", "on")
        return bool(new_value)
    if isinstance(current_value, int) and not isinstance(new_value, bool):
        return int(new_value) if new_value is not None else current_value
    if isinstance(current_value, float):
        return float(new_value) if new_value is not None else current_value
    return new_value


def _create_ocr_config(
    ocr_backend: Literal["tesseract", "easyocr", "paddleocr"] | None, config_dict: dict[str, Any]
) -> Any:
    if ocr_backend == "tesseract":
        return TesseractConfig(**config_dict)
    if ocr_backend == "easyocr":
        return EasyOCRConfig(**config_dict)
    if ocr_backend == "paddleocr":
        return PaddleOCRConfig(**config_dict)
    return config_dict


@lru_cache(maxsize=128)
def _merge_configs_cached(
    static_config: ExtractionConfig | None,
    query_params: tuple[tuple[str, Any], ...],
    header_config: tuple[tuple[str, Any], ...] | None,
) -> ExtractionConfig:
    base_config = static_config or ExtractionConfig()
    config_dict = base_config.to_dict()

    query_dict = dict(query_params) if query_params else {}
    for key, value in query_dict.items():
        if value is not None and key in config_dict:
            config_dict[key] = _convert_value_type(config_dict[key], value)

    if header_config:
        header_dict = dict(header_config)
        for key, value in header_dict.items():
            if key in config_dict:
                config_dict[key] = value

    if "ocr_config" in config_dict and isinstance(config_dict["ocr_config"], dict):
        ocr_backend = config_dict.get("ocr_backend")
        config_dict["ocr_config"] = _create_ocr_config(ocr_backend, config_dict["ocr_config"])

    return ExtractionConfig(**config_dict)


def _make_hashable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return tuple(sorted((k, _make_hashable(v)) for k, v in obj.items()))
    if isinstance(obj, list):
        return tuple(_make_hashable(item) for item in obj)
    return obj


def merge_configs(
    static_config: ExtractionConfig | None,
    query_params: dict[str, Any],
    header_config: dict[str, Any] | None,
) -> ExtractionConfig:
    query_tuple = tuple(sorted(query_params.items())) if query_params else ()
    header_tuple = _make_hashable(header_config) if header_config else None

    return _merge_configs_cached(static_config, query_tuple, header_tuple)


@post("/extract", operation_id="ExtractFiles")
async def handle_files_upload(  # noqa: PLR0913
    request: Request[Any, Any, Any],
    data: Annotated[list[UploadFile], Body(media_type=RequestEncodingType.MULTI_PART)],
    chunk_content: str | bool | None = None,
    max_chars: int | None = None,
    max_overlap: int | None = None,
    extract_tables: str | bool | None = None,
    extract_entities: str | bool | None = None,
    extract_keywords: str | bool | None = None,
    keyword_count: int | None = None,
    force_ocr: str | bool | None = None,
    ocr_backend: Literal["tesseract", "easyocr", "paddleocr"] | None = None,
    auto_detect_language: str | bool | None = None,
    pdf_password: str | None = None,
) -> list[ExtractionResult]:
    """Extract text, metadata, and structured data from uploaded documents.

    This endpoint processes multiple file uploads and extracts comprehensive information including:
    - Text content with metadata
    - Tables (if enabled)
    - Named entities (if enabled)
    - Keywords (if enabled)
    - Language detection (if enabled)

    Supports various file formats including PDF, Office documents, images, and more.
    Maximum file size: 1GB per file.

    Args:
        request: The HTTP request object
        data: List of files to process (multipart form data)
        chunk_content: Enable text chunking for large documents
        max_chars: Maximum characters per chunk (default: 1000)
        max_overlap: Character overlap between chunks (default: 200)
        extract_tables: Extract tables from documents
        extract_entities: Extract named entities from text
        extract_keywords: Extract keywords from text
        keyword_count: Number of keywords to extract (default: 10)
        force_ocr: Force OCR processing even for text-based documents
        ocr_backend: OCR engine to use (tesseract, easyocr, paddleocr)
        auto_detect_language: Enable automatic language detection
        pdf_password: Password for encrypted PDF files

    Returns:
        List of extraction results, one per uploaded file
    """
    static_config = discover_config()

    query_params = {
        "chunk_content": chunk_content,
        "max_chars": max_chars,
        "max_overlap": max_overlap,
        "extract_tables": extract_tables,
        "extract_entities": extract_entities,
        "extract_keywords": extract_keywords,
        "keyword_count": keyword_count,
        "force_ocr": force_ocr,
        "ocr_backend": ocr_backend,
        "auto_detect_language": auto_detect_language,
        "pdf_password": pdf_password,
    }

    header_config = None
    if config_header := request.headers.get("X-Extraction-Config"):
        try:
            header_config = loads(config_header)
        except Exception as e:
            raise ValidationError(f"Invalid JSON in X-Extraction-Config header: {e}", context={"error": str(e)}) from e

    final_config = merge_configs(static_config, query_params, header_config)

    return await batch_extract_bytes(
        [(await file.read(), file.content_type) for file in data],
        config=final_config,
    )


@get("/health", operation_id="HealthCheck")
async def health_check() -> HealthResponse:
    """Check the health status of the API.

    Returns:
        Simple status response indicating the API is operational
    """
    return {"status": "ok"}


@get("/config", operation_id="GetConfiguration")
async def get_configuration() -> ConfigurationResponse:
    """Get the current extraction configuration.

    Returns the loaded configuration from kreuzberg.toml file if available,
    or indicates that no configuration file was found.

    Returns:
        Configuration data with status message
    """
    config = discover_config()
    if config is None:
        return {"message": "No configuration file found", "config": None}

    return {
        "message": "Configuration loaded successfully",
        "config": msgspec.to_builtins(config, order="deterministic"),
    }


openapi_config = OpenAPIConfig(
    title="Kreuzberg API",
    version="3.14.0",
    description="Document intelligence framework API for extracting text, metadata, and structured data from diverse file formats",
    contact=Contact(
        name="Kreuzberg",
        url="https://github.com/Goldziher/kreuzberg",
    ),
    license=License(
        name="MIT",
        identifier="MIT",
    ),
    use_handler_docstrings=True,
    create_examples=True,
)

app = Litestar(
    route_handlers=[handle_files_upload, health_check, get_configuration],
    plugins=[OpenTelemetryPlugin(OpenTelemetryConfig())],
    logging_config=StructLoggingConfig(),
    openapi_config=openapi_config,
    exception_handlers={
        KreuzbergError: exception_handler,
        Exception: general_exception_handler,
    },
    request_max_body_size=1024 * 1024 * 1024,  # 1GB limit for large file uploads
)
