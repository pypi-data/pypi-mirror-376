from enum import Enum
from typing import Dict, Literal, Optional

import numpy as np
from numpy.typing import NDArray
from pydantic import (
    AliasChoices,
    AliasPath,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    field_validator,
    model_serializer,
    model_validator,
)

from xdof_sdk.data.schema.types import LengthUnit, Transform3D


class CameraId(str, Enum):
    """Enum for different camera IDs."""

    TOP_CAMERA = "top_camera"
    LEFT_CAMERA = "left_camera"
    RIGHT_CAMERA = "right_camera"
    SECONDARY_TOP = "secondary_top_camera"

    # Not used in prod
    TEST_CAMERA = "test_camera"


class CameraExtrinsics(BaseModel):
    world: Literal["left_rgb"] = "left_rgb"

    right_rgb: Transform3D = Field(
        validation_alias=AliasChoices(
            "right_rgb",
            AliasPath("extrinsics", "right_rgb"),
        )
    )
    """ Transform of the right_rgb camera in the left_rgb frame. Units should be in meters."""

    @field_validator("right_rgb", mode="before")
    @classmethod
    def validate_right_rgb(cls, value):
        # Legacy format: raw 4x4 list/array assumed to be in mm
        if isinstance(value, list):
            value = np.array(value, dtype=np.float64)

        if isinstance(value, np.ndarray):
            if value.shape != (4, 4):
                raise ValueError(f"Invalid shape for right_rgb: {value.shape}")
            # Legacy format - assume mm units
            return Transform3D(matrix=value, units=LengthUnit.MM)

        # Modern format: either a Transform3D object or if read from JSON,
        # a dict that can be converted to a Transform3D
        elif isinstance(value, Transform3D):
            return value
        elif isinstance(value, dict):
            return Transform3D(**value)
        else:
            raise ValueError(f"Invalid type for right_rgb: {type(value)}")

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)


class SingleCameraIntrinsicData(BaseModel):
    intrinsics_matrix: NDArray[np.float64]

    distortion_coefficients: list[float] = Field(
        validation_alias=AliasChoices(
            "distortion_coefficients",
            AliasPath("distortion", "distortion_coefficients"),
        )
    )

    distortion_model: str = Field(
        validation_alias=AliasChoices(
            "distortion_model",
            AliasPath("distortion", "distortion_model"),
        )
    )

    @field_validator("intrinsics_matrix", mode="before")
    @classmethod
    def validate_intrinsics_matrix(cls, value):
        if isinstance(value, list):
            value = np.array(value, dtype=np.float64)

        if isinstance(value, np.ndarray):
            if value.shape != (3, 3):
                raise ValueError(f"Invalid shape for intrinsics_matrix: {value.shape}")
            return value

        raise ValueError(f"Invalid type for intrinsics_matrix: {type(value)}")

    @field_serializer("intrinsics_matrix")
    def serialize_intrinsics_matrix(
        self, value: NDArray[np.float64]
    ) -> list[list[float]]:
        if value.shape != (3, 3):
            raise ValueError(f"Invalid shape for intrinsics_matrix: {value.shape}")
        return value.tolist()

    model_config = ConfigDict(extra="ignore", arbitrary_types_allowed=True)


class IntrinsicsList(BaseModel):
    rgb: Optional[SingleCameraIntrinsicData] = None
    """ Intrinsics for a single camera for a non-stereo camera. """

    left_rgb: Optional[SingleCameraIntrinsicData] = None
    """ Intrinsics for the left camera of a stereo camera. """

    right_rgb: Optional[SingleCameraIntrinsicData] = None
    """ Intrinsics for the right camera of a stereo camera. """


class CameraInfo(BaseModel):
    width: int
    height: int

    extrinsics: Optional[CameraExtrinsics] = None
    """ Extrinsics for the camera. Really only used for getting the right camera's extrinsics from left_rgb. """

    intrinsics: Optional[IntrinsicsList] = Field(
        default=None,
        validation_alias=AliasChoices(
            "intrinsics",
            AliasPath("intrinsic_data", "cameras"),
        ),
    )
    """ Intrinsics for the sensors(s) in this camera. """


class CameraInfoList(BaseModel):
    cameras: Dict[CameraId, CameraInfo] = {}

    @model_validator(mode="before")
    @classmethod
    def collect_camera_fields(cls, values):
        if isinstance(values, dict):
            cameras = {}

            for key, value in list(values.items()):
                try:
                    # Try to convert key to CameraId - will raise ValueError if invalid
                    camera_id = CameraId(key)
                    cameras[camera_id] = value
                    del values[key]  # Remove from top level immediately
                except ValueError:
                    # Not a valid CameraId, throw error
                    raise ValueError(
                        f"Invalid camera ID: '{key}'. Must be one of: {[e.value for e in CameraId]}"
                    )

            if cameras:
                values["cameras"] = cameras
        return values

    @property
    def top_camera(self) -> CameraInfo:
        """Backwards compatibility property for top_camera."""
        return self.cameras[CameraId.TOP_CAMERA]

    @property
    def left_camera(self) -> CameraInfo:
        """Backwards compatibility property for left_camera."""
        return self.cameras[CameraId.LEFT_CAMERA]

    @property
    def right_camera(self) -> CameraInfo:
        """Backwards compatibility property for right_camera."""
        return self.cameras[CameraId.RIGHT_CAMERA]

    @model_serializer
    def serialize_model(self):
        """Serialize model back to flat structure for backwards compatibility."""
        result = {}
        for camera_id, camera_info in self.cameras.items():
            result[camera_id.value] = camera_info
        return result
