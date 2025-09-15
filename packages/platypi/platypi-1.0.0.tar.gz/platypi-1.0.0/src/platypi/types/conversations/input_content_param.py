# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .input_audio_param import InputAudioParam
from .input_text_content_param import InputTextContentParam

__all__ = ["InputContentParam", "InputImage", "InputFile"]


class InputImage(TypedDict, total=False):
    detail: Required[Literal["low", "high", "auto"]]
    """The detail level of the image to be sent to the model.

    One of `high`, `low`, or `auto`. Defaults to `auto`.
    """

    type: Required[Literal["input_image"]]
    """The type of the input item. Always `input_image`."""

    file_id: Optional[str]
    """The ID of the file to be sent to the model."""

    image_url: Optional[str]
    """The URL of the image to be sent to the model.

    A fully qualified URL or base64 encoded image in a data URL.
    """


class InputFile(TypedDict, total=False):
    type: Required[Literal["input_file"]]
    """The type of the input item. Always `input_file`."""

    file_data: str
    """The content of the file to be sent to the model."""

    file_id: Optional[str]
    """The ID of the file to be sent to the model."""

    file_url: str
    """The URL of the file to be sent to the model."""

    filename: str
    """The name of the file to be sent to the model."""


InputContentParam: TypeAlias = Union[InputTextContentParam, InputImage, InputFile, InputAudioParam]
