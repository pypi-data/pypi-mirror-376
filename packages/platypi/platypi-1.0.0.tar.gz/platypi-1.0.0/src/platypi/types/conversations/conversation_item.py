# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import Literal, Annotated, TypeAlias

from ..._utils import PropertyInfo
from ..._models import BaseModel
from .mcp_tool_call import McpToolCall
from .mcp_list_tools import McpListTools
from .reasoning_item import ReasoningItem
from .custom_tool_call import CustomToolCall
from .computer_tool_call import ComputerToolCall
from .image_gen_tool_call import ImageGenToolCall
from .mcp_approval_request import McpApprovalRequest
from .web_search_tool_call import WebSearchToolCall
from .file_search_tool_call import FileSearchToolCall
from .local_shell_tool_call import LocalShellToolCall
from .custom_tool_call_output import CustomToolCallOutput
from .code_interpreter_tool_call import CodeInterpreterToolCall
from .function_tool_call_resource import FunctionToolCallResource
from .local_shell_tool_call_output import LocalShellToolCallOutput
from .mcp_approval_response_resource import McpApprovalResponseResource
from .computer_tool_call_output_resource import ComputerToolCallOutputResource
from .function_tool_call_output_resource import FunctionToolCallOutputResource

__all__ = [
    "ConversationItem",
    "Message",
    "MessageContent",
    "MessageContentInputText",
    "MessageContentOutputText",
    "MessageContentOutputTextAnnotation",
    "MessageContentOutputTextAnnotationFileCitation",
    "MessageContentOutputTextAnnotationURLCitation",
    "MessageContentOutputTextAnnotationContainerFileCitation",
    "MessageContentOutputTextLogprob",
    "MessageContentOutputTextLogprobTopLogprob",
    "MessageContentText",
    "MessageContentSummaryText",
    "MessageContentRefusal",
    "MessageContentInputImage",
    "MessageContentComputerScreenshot",
    "MessageContentInputFile",
]


class MessageContentInputText(BaseModel):
    text: str
    """The text input to the model."""

    type: Literal["input_text"]
    """The type of the input item. Always `input_text`."""


class MessageContentOutputTextAnnotationFileCitation(BaseModel):
    file_id: str
    """The ID of the file."""

    filename: str
    """The filename of the file cited."""

    index: int
    """The index of the file in the list of files."""

    type: Literal["file_citation"]
    """The type of the file citation. Always `file_citation`."""


class MessageContentOutputTextAnnotationURLCitation(BaseModel):
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


class MessageContentOutputTextAnnotationContainerFileCitation(BaseModel):
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


MessageContentOutputTextAnnotation: TypeAlias = Annotated[
    Union[
        MessageContentOutputTextAnnotationFileCitation,
        MessageContentOutputTextAnnotationURLCitation,
        MessageContentOutputTextAnnotationContainerFileCitation,
    ],
    PropertyInfo(discriminator="type"),
]


class MessageContentOutputTextLogprobTopLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float


class MessageContentOutputTextLogprob(BaseModel):
    token: str

    bytes: List[int]

    logprob: float

    top_logprobs: List[MessageContentOutputTextLogprobTopLogprob]


class MessageContentOutputText(BaseModel):
    annotations: List[MessageContentOutputTextAnnotation]
    """The annotations of the text output."""

    text: str
    """The text output from the model."""

    type: Literal["output_text"]
    """The type of the output text. Always `output_text`."""

    logprobs: Optional[List[MessageContentOutputTextLogprob]] = None


class MessageContentText(BaseModel):
    text: str

    type: Literal["text"]


class MessageContentSummaryText(BaseModel):
    text: str

    type: Literal["summary_text"]


class MessageContentRefusal(BaseModel):
    refusal: str
    """The refusal explanation from the model."""

    type: Literal["refusal"]
    """The type of the refusal. Always `refusal`."""


class MessageContentInputImage(BaseModel):
    detail: Literal["low", "high", "auto"]
    """The detail level of the image to be sent to the model.

    One of `high`, `low`, or `auto`. Defaults to `auto`.
    """

    file_id: Optional[str] = None
    """The ID of the file to be sent to the model."""

    image_url: Optional[str] = None
    """The URL of the image to be sent to the model.

    A fully qualified URL or base64 encoded image in a data URL.
    """

    type: Literal["input_image"]
    """The type of the input item. Always `input_image`."""


class MessageContentComputerScreenshot(BaseModel):
    file_id: Optional[str] = None
    """The identifier of an uploaded file that contains the screenshot."""

    image_url: Optional[str] = None
    """The URL of the screenshot image."""

    type: Literal["computer_screenshot"]
    """Specifies the event type.

    For a computer screenshot, this property is always set to `computer_screenshot`.
    """


class MessageContentInputFile(BaseModel):
    file_id: Optional[str] = None
    """The ID of the file to be sent to the model."""

    type: Literal["input_file"]
    """The type of the input item. Always `input_file`."""

    file_url: Optional[str] = None
    """The URL of the file to be sent to the model."""

    filename: Optional[str] = None
    """The name of the file to be sent to the model."""


MessageContent: TypeAlias = Annotated[
    Union[
        MessageContentInputText,
        MessageContentOutputText,
        MessageContentText,
        MessageContentSummaryText,
        MessageContentRefusal,
        MessageContentInputImage,
        MessageContentComputerScreenshot,
        MessageContentInputFile,
    ],
    PropertyInfo(discriminator="type"),
]


class Message(BaseModel):
    id: str
    """The unique ID of the message."""

    content: List[MessageContent]
    """The content of the message"""

    role: Literal["unknown", "user", "assistant", "system", "critic", "discriminator", "developer", "tool"]
    """The role of the message.

    One of `unknown`, `user`, `assistant`, `system`, `critic`, `discriminator`,
    `developer`, or `tool`.
    """

    status: Literal["in_progress", "completed", "incomplete"]
    """The status of item.

    One of `in_progress`, `completed`, or `incomplete`. Populated when items are
    returned via API.
    """

    type: Literal["message"]
    """The type of the message. Always set to `message`."""


ConversationItem: TypeAlias = Annotated[
    Union[
        Message,
        FunctionToolCallResource,
        FunctionToolCallOutputResource,
        FileSearchToolCall,
        WebSearchToolCall,
        ImageGenToolCall,
        ComputerToolCall,
        ComputerToolCallOutputResource,
        ReasoningItem,
        CodeInterpreterToolCall,
        LocalShellToolCall,
        LocalShellToolCallOutput,
        McpListTools,
        McpApprovalRequest,
        McpApprovalResponseResource,
        McpToolCall,
        CustomToolCall,
        CustomToolCallOutput,
    ],
    PropertyInfo(discriminator="type"),
]
