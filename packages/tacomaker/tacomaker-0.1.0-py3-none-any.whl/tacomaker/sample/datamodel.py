import polars as pl
import pathlib
import re
from abc import ABC, abstractmethod
from typing import Any, Literal

import pydantic
from osgeo import gdal

# Dependencies
from tacomaker.tortilla.datamodel import Tortilla

# Asset typesgt
AssetType = Literal["TACOTIFF", "TACOGEOPARQUET", "TORTILLA", "OTHER"]

# Key validation pattern
VALID_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9_]+(?:[:][\w]+)?$")

# Core fields that cannot be overwritten by extensions
PROTECTED_CORE_FIELDS = {"id", "type", "path"}


class SampleExtension(ABC, pydantic.BaseModel):
    """Abstract base class for Sample extensions that compute metadata."""
    
    return_none: bool = pydantic.Field(False, description="If True, return None values while preserving schema")
    
    @abstractmethod
    def get_schema(self) -> dict[str, pl.DataType]:
        """Return the expected schema for this extension."""
        pass
    
    @abstractmethod
    def _compute(self, sample: 'Sample') -> pl.DataFrame:
        """Actual computation logic - only called when return_none=False."""
        pass
    
    def __call__(self, sample: 'Sample') -> pl.DataFrame:
        """
        Process Sample and return computed metadata.
        
        Args:
            sample: Input Sample object
                
        Returns:
            pl.DataFrame: Single-row DataFrame with computed metadata
        """
        # Check return_none FIRST for performance
        if self.return_none:
            schema = self.get_schema()
            none_data = {col_name: [None] for col_name in schema.keys()}
            return pl.DataFrame(none_data, schema=schema)
        
        # Only do actual computation if needed
        return self._compute(sample)


class TacotiffValidator:
    """
    Validator for TACOTIFF sample using GDAL to enforce strict format requirements.

    TACOTIFF format requirements:
    - Driver: GDAL generated COG (Cloud Optimized GeoTIFF)
    - Compression: ZSTD (for optimal compression ratio and speed)
    - Interleave: TILE (for efficient access patterns)
    - Predictor: HORIZONTAL (2) or NONE (1)
    - Overviews: None (to avoid redundant data storage)
    - BIGTIFF: YES (to standardize between large and small files)
    - GEOTIFF version: 1.1 (for standard compliance)
    """

    def validate(self, path: pathlib.Path) -> None:
        """
        Validate a TACOTIFF file against format requirements.

        Example:
            >>> validator = TacotiffValidator()
            >>> validator.validate(Path("my_file.tif"))  # Raises ValueError if invalid
        """

        # Open the dataset using GDAL
        ds = gdal.Open(str(path))

        # Check if GDAL can open the file
        if not ds:
            raise ValueError(f"Cannot open {path} with GDAL")

        try:
            # Get image structure metadata from GDAL
            # This contains compression, interleave, and other format info
            ds_args = ds.GetMetadata("IMAGE_STRUCTURE")

            # Validate ZSTD compression (5000)
            compression = ds_args.get("COMPRESSION", "").upper()
            if compression != "ZSTD":
                raise ValueError(f"TACOTIFF assets must use ZSTD compression, found: {compression or 'NONE'}")

            # Validate TILE interleave
            interleave = ds_args.get("INTERLEAVE", "").upper()
            if interleave != "TILE":
                raise ValueError(f"TACOTIFF assets must use TILE interleave, found: {interleave or 'PIXEL'}")

            # Validate predictor setting
            predictor = ds_args.get("PREDICTOR", "")
            if predictor not in ["1", "2"]:
                raise ValueError(
                    f"TACOTIFF assets must use HORIZONTAL (2) or NONE (1) predictor, found: {predictor or 'unknown'}"
                )

            # Validate no overviews present
            band = ds.GetRasterBand(1)
            overview_count = band.GetOverviewCount()
            if overview_count != 0:
                raise ValueError(f"TACOTIFF assets must not have overviews, found: {overview_count} overview levels")

        finally:
            # Always clean up GDAL dataset to free memory
            ds = None


class Sample(pydantic.BaseModel):
    """
    The fundamental data unit in the TACO framework, combining raw data with
    structured metadata for training, validation, and testing.

    Supported data asset types:
    - TACOTIFF: Cloud Optimized GeoTIFF with strict format requirements
    - TACOGEOPARQUET: GeoParquet format  with strict format requirements
    - TORTILLA: A set of samples with similar characteristics
    - OTHER: Other file-based formats (e.g., TIFF, NetCDF, HDF5, PDF, CSV)

    Example:
        >>> sample = Sample(
        ...     id="soyuntaco",
        ...     path=Path("/home/lxlx/sentinel2.tif"),
        ...     type="TACOTIFF"
        ... )
        >>> sample.extend_with(stac_obj)
        >>> sample.extend_with({"s2:mgrs_tile": "T30UYA"})
        >>> sample.extend_with(scaling_extension)
    """

    # Core attributes
    id: str  # Unique identifier following TACO naming conventions
    path: pathlib.Path | Tortilla  # Location of data (file or container)
    type: AssetType  # Type of geospatial data asset

    # Private attribute to store extension schemas
    _extension_schemas: dict[str, pl.DataType] = pydantic.PrivateAttr(default_factory=dict)

    model_config = pydantic.ConfigDict(
        arbitrary_types_allowed=True,  # Support Tortilla dataclass
        extra="allow"  # Allow dynamic fields from extensions
    )

    def model_post_init(self, __context: Any) -> None:
        """Initialize core field schemas after model creation."""
        self._extension_schemas.update({
            "id": pl.Utf8,
            "path": pl.Utf8,
            "type": pl.Utf8
        })

    @pydantic.field_validator("id")
    def validate_id(cls, v: str) -> str:
        """Check the ID following TACO conventions - now allows numbers at start."""
        if not v:
            raise ValueError("ID cannot be an empty string.")

        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_]*$", v):
            raise ValueError(
                "ID must start with letter or number and contain only alphanumeric characters or underscores."
            )
        return v

    @pydantic.field_validator("path")
    def validate_path(cls, v: pathlib.Path | Tortilla) -> pathlib.Path | Tortilla:
        """Validate and normalize the data path."""
        if isinstance(v, Tortilla):
            return v

        if isinstance(v, pathlib.Path):
            if not v.exists():
                raise ValueError(f"Path {v} does not exist.")
            return v.absolute()

        raise ValueError("Path must be pathlib.Path or Tortilla instance")

    @pydantic.model_validator(mode="after")
    def global_validation(self):
        """Cross-field validation ensuring path type matches asset type."""
        # TORTILLA type must have Tortilla path
        if self.type == "TORTILLA":
            if not isinstance(self.path, Tortilla):
                raise ValueError("TORTILLA type must have a Tortilla instance as path")

        # TACOTIFF specific validations
        if self.type == "TACOTIFF":
            TacotiffValidator().validate(self.path)

        return self

    def extend_with(self, extension: Any | dict[str, Any], name: str | None = None) -> None:
        """
        Add extension to sample by adding fields directly to the model.

        Args:
            extension: SampleExtension, Pydantic model, or dictionary to add
            name: Optional custom namespace (defaults to class name for objects)

        Returns:
            Sample: Self for method chaining
        """
        # Check if this is a computational SampleExtension
        if hasattr(extension, '__call__') and hasattr(extension, 'model_dump'):
            computed_metadata = extension(self)
            if isinstance(computed_metadata, pl.DataFrame):
                # Convert single-row DataFrame to dict
                if len(computed_metadata) != 1:
                    raise ValueError("SampleExtension must return single-row DataFrame")
                
                # Capture schemas before converting to dict
                for col_name, dtype in computed_metadata.schema.items():
                    self._extension_schemas[col_name] = dtype
                
                metadata_dict = computed_metadata.to_dicts()[0]
                for key, value in metadata_dict.items():
                    self._validate_key(key)
                    if key in PROTECTED_CORE_FIELDS:
                        raise ValueError(f"Cannot override core field: {key}")
                    setattr(self, key, value)

        elif isinstance(extension, pl.DataFrame):
            # Direct DataFrame extension
            if len(extension) != 1:
                raise ValueError("DataFrame extension must have exactly one row")
            
            # Capture schemas before converting to dict
            for col_name, dtype in extension.schema.items():
                self._extension_schemas[col_name] = dtype
            
            metadata_dict = extension.to_dicts()[0]
            for key, value in metadata_dict.items():
                self._validate_key(key)
                if key in PROTECTED_CORE_FIELDS:
                    raise ValueError(f"Cannot override core field: {key}")
                setattr(self, key, value)
                                
        elif isinstance(extension, dict):
            # Dictionary extension - assume default polars inference for types
            for key, value in extension.items():
                self._validate_key(key)
                if key in PROTECTED_CORE_FIELDS:
                    raise ValueError(f"Cannot override core field: {key}")
                setattr(self, key, value)
                
        else:
            # Pydantic model extension - assume default polars inference for types
            namespace = name if name else extension.__class__.__name__.lower()
            if hasattr(extension, "model_dump"):
                extension_data = extension.model_dump()
                for key, value in extension_data.items():
                    namespaced_key = f"{namespace}:{key}"
                    self._validate_key(namespaced_key)
                    if namespaced_key in PROTECTED_CORE_FIELDS:
                        raise ValueError(f"Cannot override core field: {namespaced_key}")
                    setattr(self, namespaced_key, value)
            else:
                raise ValueError(f"Extension must be pydantic model or dict, got: {type(extension)}")
        
        return None

    def _validate_key(self, key: str) -> None:
        """Validate key format."""
        if not VALID_KEY_PATTERN.match(key):
            raise ValueError(
                f"Invalid key format '{key}'. Use alphanumeric + underscore, "
                f"optionally with colon (e.g., 'key', 'my_key', 'stac:title')"
            )

    def export_metadata(self) -> pl.DataFrame:
        """
        Export complete Sample metadata as a single-row DataFrame with proper schemas.

        Returns all fields in the model, including core attributes and
        extension metadata with proper data types preserved.

        Returns:
            pl.DataFrame: Single-row DataFrame with complete sample metadata
        """
        data = self.model_dump()
        
        # Handle path serialization
        if isinstance(self.path, pathlib.Path):
            data["path"] = self.path.as_posix()
        elif isinstance(self.path, Tortilla):
            data["path"] = None
        
        # Create initial DataFrame
        df = pl.DataFrame([data])
        
        # Apply saved schemas
        cast_exprs = []
        for col_name, dtype in self._extension_schemas.items():
            if col_name in df.columns:
                cast_exprs.append(pl.col(col_name).cast(dtype))
        
        if cast_exprs:
            df = df.with_columns(cast_exprs)
        
        return df