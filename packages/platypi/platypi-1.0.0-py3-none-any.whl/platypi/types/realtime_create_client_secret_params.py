# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Union, Iterable, Optional
from typing_extensions import Literal, Required, TypeAlias, TypedDict

from .prompt_param import PromptParam
from .mcp_tool_param import McpToolParam
from .tool_choice_options import ToolChoiceOptions
from .noise_reduction_type import NoiseReductionType
from .tool_choice_mcp_param import ToolChoiceMcpParam
from .voice_ids_shared_param import VoiceIDsSharedParam
from .audio_transcription_param import AudioTranscriptionParam
from .realtime_truncation_param import RealtimeTruncationParam
from .tool_choice_function_param import ToolChoiceFunctionParam
from .realtime_audio_formats_param import RealtimeAudioFormatsParam
from .realtime_function_tool_param import RealtimeFunctionToolParam
from .realtime_turn_detection_param import RealtimeTurnDetectionParam

__all__ = [
    "RealtimeCreateClientSecretParams",
    "ExpiresAfter",
    "Session",
    "SessionRealtime",
    "SessionRealtimeAudio",
    "SessionRealtimeAudioInput",
    "SessionRealtimeAudioInputNoiseReduction",
    "SessionRealtimeAudioOutput",
    "SessionRealtimeToolChoice",
    "SessionRealtimeTool",
    "SessionRealtimeTracing",
    "SessionRealtimeTracingTracingConfiguration",
    "SessionTranscription",
    "SessionTranscriptionAudio",
    "SessionTranscriptionAudioInput",
    "SessionTranscriptionAudioInputNoiseReduction",
]


class RealtimeCreateClientSecretParams(TypedDict, total=False):
    expires_after: ExpiresAfter
    """Configuration for the client secret expiration.

    Expiration refers to the time after which a client secret will no longer be
    valid for creating sessions. The session itself may continue after that time
    once started. A secret can be used to create multiple sessions until it expires.
    """

    session: Session
    """Session configuration to use for the client secret.

    Choose either a realtime session or a transcription session.
    """


class ExpiresAfter(TypedDict, total=False):
    anchor: Literal["created_at"]
    """
    The anchor point for the client secret expiration, meaning that `seconds` will
    be added to the `created_at` time of the client secret to produce an expiration
    timestamp. Only `created_at` is currently supported.
    """

    seconds: int
    """The number of seconds from the anchor point to the expiration.

    Select a value between `10` and `7200` (2 hours). This default to 600 seconds
    (10 minutes) if not specified.
    """


class SessionRealtimeAudioInputNoiseReduction(TypedDict, total=False):
    type: NoiseReductionType
    """Type of noise reduction.

    `near_field` is for close-talking microphones such as headphones, `far_field` is
    for far-field microphones such as laptop or conference room microphones.
    """


class SessionRealtimeAudioInput(TypedDict, total=False):
    format: RealtimeAudioFormatsParam
    """The format of the input audio."""

    noise_reduction: SessionRealtimeAudioInputNoiseReduction
    """Configuration for input audio noise reduction.

    This can be set to `null` to turn off. Noise reduction filters audio added to
    the input audio buffer before it is sent to VAD and the model. Filtering the
    audio can improve VAD and turn detection accuracy (reducing false positives) and
    model performance by improving perception of the input audio.
    """

    transcription: AudioTranscriptionParam
    """
    Configuration for input audio transcription, defaults to off and can be set to
    `null` to turn off once on. Input audio transcription is not native to the
    model, since the model consumes audio directly. Transcription runs
    asynchronously through
    [the /audio/transcriptions endpoint](https://platform.openai.com/docs/api-reference/audio/createTranscription)
    and should be treated as guidance of input audio content rather than precisely
    what the model heard. The client can optionally set the language and prompt for
    transcription, these offer additional guidance to the transcription service.
    """

    turn_detection: Optional[RealtimeTurnDetectionParam]
    """Configuration for turn detection, ether Server VAD or Semantic VAD.

    This can be set to `null` to turn off, in which case the client must manually
    trigger model response.

    Server VAD means that the model will detect the start and end of speech based on
    audio volume and respond at the end of user speech.

    Semantic VAD is more advanced and uses a turn detection model (in conjunction
    with VAD) to semantically estimate whether the user has finished speaking, then
    dynamically sets a timeout based on this probability. For example, if user audio
    trails off with "uhhm", the model will score a low probability of turn end and
    wait longer for the user to continue speaking. This can be useful for more
    natural conversations, but may have a higher latency.
    """


class SessionRealtimeAudioOutput(TypedDict, total=False):
    format: RealtimeAudioFormatsParam
    """The format of the output audio."""

    speed: float
    """
    The speed of the model's spoken response as a multiple of the original speed.
    1.0 is the default speed. 0.25 is the minimum speed. 1.5 is the maximum speed.
    This value can only be changed in between model turns, not while a response is
    in progress.

    This parameter is a post-processing adjustment to the audio after it is
    generated, it's also possible to prompt the model to speak faster or slower.
    """

    voice: VoiceIDsSharedParam
    """The voice the model uses to respond.

    Voice cannot be changed during the session once the model has responded with
    audio at least once. Current voice options are `alloy`, `ash`, `ballad`,
    `coral`, `echo`, `sage`, `shimmer`, `verse`, `marin`, and `cedar`. We recommend
    `marin` and `cedar` for best quality.
    """


class SessionRealtimeAudio(TypedDict, total=False):
    input: SessionRealtimeAudioInput

    output: SessionRealtimeAudioOutput


SessionRealtimeToolChoice: TypeAlias = Union[ToolChoiceOptions, ToolChoiceFunctionParam, ToolChoiceMcpParam]

SessionRealtimeTool: TypeAlias = Union[RealtimeFunctionToolParam, McpToolParam]


class SessionRealtimeTracingTracingConfiguration(TypedDict, total=False):
    group_id: str
    """
    The group id to attach to this trace to enable filtering and grouping in the
    Traces Dashboard.
    """

    metadata: object
    """
    The arbitrary metadata to attach to this trace to enable filtering in the Traces
    Dashboard.
    """

    workflow_name: str
    """The name of the workflow to attach to this trace.

    This is used to name the trace in the Traces Dashboard.
    """


SessionRealtimeTracing: TypeAlias = Union[Literal["auto"], SessionRealtimeTracingTracingConfiguration]


class SessionRealtime(TypedDict, total=False):
    type: Required[Literal["realtime"]]
    """The type of session to create. Always `realtime` for the Realtime API."""

    audio: SessionRealtimeAudio
    """Configuration for input and output audio."""

    include: List[Literal["item.input_audio_transcription.logprobs"]]
    """Additional fields to include in server outputs.

    `item.input_audio_transcription.logprobs`: Include logprobs for input audio
    transcription.
    """

    instructions: str
    """The default system instructions (i.e.

    system message) prepended to model calls. This field allows the client to guide
    the model on desired responses. The model can be instructed on response content
    and format, (e.g. "be extremely succinct", "act friendly", "here are examples of
    good responses") and on audio behavior (e.g. "talk quickly", "inject emotion
    into your voice", "laugh frequently"). The instructions are not guaranteed to be
    followed by the model, but they provide guidance to the model on the desired
    behavior.

    Note that the server sets default instructions which will be used if this field
    is not set and are visible in the `session.created` event at the start of the
    session.
    """

    max_output_tokens: Union[int, Literal["inf"]]
    """
    Maximum number of output tokens for a single assistant response, inclusive of
    tool calls. Provide an integer between 1 and 4096 to limit output tokens, or
    `inf` for the maximum available tokens for a given model. Defaults to `inf`.
    """

    model: Union[
        str,
        Literal[
            "gpt-realtime",
            "gpt-realtime-2025-08-28",
            "gpt-4o-realtime-preview",
            "gpt-4o-realtime-preview-2024-10-01",
            "gpt-4o-realtime-preview-2024-12-17",
            "gpt-4o-realtime-preview-2025-06-03",
            "gpt-4o-mini-realtime-preview",
            "gpt-4o-mini-realtime-preview-2024-12-17",
        ],
    ]
    """The Realtime model used for this session."""

    output_modalities: List[Literal["text", "audio"]]
    """The set of modalities the model can respond with.

    It defaults to `["audio"]`, indicating that the model will respond with audio
    plus a transcript. `["text"]` can be used to make the model respond with text
    only. It is not possible to request both `text` and `audio` at the same time.
    """

    prompt: Optional[PromptParam]
    """Reference to a prompt template and its variables.

    [Learn more](https://platform.openai.com/docs/guides/text?api-mode=responses#reusable-prompts).
    """

    tool_choice: SessionRealtimeToolChoice
    """How the model chooses tools.

    Provide one of the string modes or force a specific function/MCP tool.
    """

    tools: Iterable[SessionRealtimeTool]
    """Tools available to the model."""

    tracing: Optional[SessionRealtimeTracing]
    """
    Realtime API can write session traces to the
    [Traces Dashboard](/logs?api=traces). Set to null to disable tracing. Once
    tracing is enabled for a session, the configuration cannot be modified.

    `auto` will create a trace for the session with default values for the workflow
    name, group id, and metadata.
    """

    truncation: RealtimeTruncationParam
    """
    Controls how the realtime conversation is truncated prior to model inference.
    The default is `auto`.
    """


class SessionTranscriptionAudioInputNoiseReduction(TypedDict, total=False):
    type: NoiseReductionType
    """Type of noise reduction.

    `near_field` is for close-talking microphones such as headphones, `far_field` is
    for far-field microphones such as laptop or conference room microphones.
    """


class SessionTranscriptionAudioInput(TypedDict, total=False):
    format: RealtimeAudioFormatsParam
    """The PCM audio format. Only a 24kHz sample rate is supported."""

    noise_reduction: SessionTranscriptionAudioInputNoiseReduction
    """Configuration for input audio noise reduction.

    This can be set to `null` to turn off. Noise reduction filters audio added to
    the input audio buffer before it is sent to VAD and the model. Filtering the
    audio can improve VAD and turn detection accuracy (reducing false positives) and
    model performance by improving perception of the input audio.
    """

    transcription: AudioTranscriptionParam
    """
    Configuration for input audio transcription, defaults to off and can be set to
    `null` to turn off once on. Input audio transcription is not native to the
    model, since the model consumes audio directly. Transcription runs
    asynchronously through
    [the /audio/transcriptions endpoint](https://platform.openai.com/docs/api-reference/audio/createTranscription)
    and should be treated as guidance of input audio content rather than precisely
    what the model heard. The client can optionally set the language and prompt for
    transcription, these offer additional guidance to the transcription service.
    """

    turn_detection: Optional[RealtimeTurnDetectionParam]
    """Configuration for turn detection, ether Server VAD or Semantic VAD.

    This can be set to `null` to turn off, in which case the client must manually
    trigger model response.

    Server VAD means that the model will detect the start and end of speech based on
    audio volume and respond at the end of user speech.

    Semantic VAD is more advanced and uses a turn detection model (in conjunction
    with VAD) to semantically estimate whether the user has finished speaking, then
    dynamically sets a timeout based on this probability. For example, if user audio
    trails off with "uhhm", the model will score a low probability of turn end and
    wait longer for the user to continue speaking. This can be useful for more
    natural conversations, but may have a higher latency.
    """


class SessionTranscriptionAudio(TypedDict, total=False):
    input: SessionTranscriptionAudioInput


class SessionTranscription(TypedDict, total=False):
    type: Required[Literal["transcription"]]
    """The type of session to create.

    Always `transcription` for transcription sessions.
    """

    audio: SessionTranscriptionAudio
    """Configuration for input and output audio."""

    include: List[Literal["item.input_audio_transcription.logprobs"]]
    """Additional fields to include in server outputs.

    `item.input_audio_transcription.logprobs`: Include logprobs for input audio
    transcription.
    """


Session: TypeAlias = Union[SessionRealtime, SessionTranscription]
