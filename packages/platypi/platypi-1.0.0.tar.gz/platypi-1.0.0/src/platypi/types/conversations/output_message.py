# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from ..._utils import PropertyInfo
from ..._models import BaseModel

__all__ = [
    "OutputMessage",
    "Content",
    "ContentOutputText",
    "ContentOutputTextAnnotation",
    "ContentOutputTextAnnotationFileCitation",
    "ContentOutputTextAnnotationURLCitation",
    "ContentOutputTextAnnotationContainerFileCitation",
    "ContentOutputTextAnnotationFilePath",
    "ContentOutputTextLogprob",
    "ContentOutputTextLogprobTopLogprob",
    "ContentRefusal",
]


class ContentOutputTextAnnotationFileCitation(BaseModel):
    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_citation"]
    """The type of the file citation. Always `file_citation`."""


class ContentOutputTextAnnotationURLCitation(BaseModel):
    end_index: int
    """The index of the last character of the URL citation in the message."""

    start_index: int
    """The index of the first character of the URL citation in the message."""

    title: str
    """The title of the web resource."""

    type: Literal["url_citation"]
    """The type of the URL citation. Always `url_citation`."""

    url: str
    """The URL of the web resource."""


class ContentOutputTextAnnotationContainerFileCitation(BaseModel):
    container_id: str
    """The ID of the container file."""

    end_index: int
    """The index of the last character of the container file citation in the message."""

    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the container file cited."""

    start_index: int
    """The index of the first character of the container file citation in the message."""

    type: Literal["container_file_citation"]
    """The type of the container file citation. Always `container_file_citation`."""


class ContentOutputTextAnnotationFilePath(BaseModel):
    file_id: str
    """The ID of the file."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_path"]
    """The type of the file path. Always `file_path`."""


ContentOutputTextAnnotation: TypeAlias = Annotated[
    Union[
        ContentOutputTextAnnotationFileCitation,
        ContentOutputTextAnnotationURLCitation,
        ContentOutputTextAnnotationContainerFileCitation,
        ContentOutputTextAnnotationFilePath,
    ],
    PropertyInfo(discriminator="type"),
]


class ContentOutputTextLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float


class ContentOutputTextLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[ContentOutputTextLogprobTopLogprob]


class ContentOutputText(BaseModel):
    annotations: List[ContentOutputTextAnnotation]
    """The annotations of the text output."""

    text: str
    """The text output from the model."""

    type: Literal["output_text"]
    """The type of the output text. Always `output_text`."""

    logprobs: Optional[List[ContentOutputTextLogprob]] = None


class ContentRefusal(BaseModel):
    refusal: str
    """The refusal explanation from the model."""

    type: Literal["refusal"]
    """The type of the refusal. Always `refusal`."""


Content: TypeAlias = Annotated[Union[ContentOutputText, ContentRefusal], PropertyInfo(discriminator="type")]


class OutputMessage(BaseModel):
    id: str
    """The unique ID of the output message."""

    content: List[Content]
    """The content of the output message."""

    role: Literal["assistant"]
    """The role of the output message. Always `assistant`."""

    status: Literal["in_progress", "completed", "incomplete"]
    """The status of the message input.

    One of `in_progress`, `completed`, or `incomplete`. Populated when input items
    are returned via API.
    """

    type: Literal["message"]
    """The type of the output message. Always `message`."""
