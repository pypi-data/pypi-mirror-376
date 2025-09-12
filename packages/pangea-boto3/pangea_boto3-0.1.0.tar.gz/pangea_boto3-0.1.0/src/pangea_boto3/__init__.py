from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeGuard

from mypy_boto3_bedrock_runtime.type_defs import (
    ContentBlockOutputTypeDef,
    ContentBlockTypeDef,
    MessageTypeDef,
)
from pangea import PangeaConfig
from pangea.services import AIGuard
from pangea.services.ai_guard import Message as PangeaMessage
from typing_extensions import Unpack

from .errors import PangeaAIGuardBlockedError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from mypy_boto3_bedrock_runtime import BedrockRuntimeClient
    from mypy_boto3_bedrock_runtime.type_defs import ConverseRequestTypeDef, ConverseResponseTypeDef

__all__ = ("PangeaAIGuardBlockedError", "converse")


def _content_text(content: Sequence[ContentBlockTypeDef | ContentBlockOutputTypeDef]) -> str:
    return "".join(content_block.get("text", "") for content_block in content)


def _is_user_or_assistant(role: str) -> TypeGuard[Literal["assistant", "user"]]:
    return role in {"assistant", "user"}


def converse(
    client: BedrockRuntimeClient,
    *,
    pangea_api_key: str,
    pangea_input_recipe: str | None = None,
    pangea_output_recipe: str | None = None,
    pangea_base_url_template: str = "https://{SERVICE_NAME}.aws.us.pangea.cloud",
    **kwargs: Unpack[ConverseRequestTypeDef],
) -> ConverseResponseTypeDef:
    messages = kwargs.get("messages", [])
    system = kwargs.get("system", [])

    pangea_messages = [
        PangeaMessage(role=message["role"], content=_content_text(message["content"])) for message in messages
    ]
    pangea_system = [PangeaMessage(role="system", content=message["text"]) for message in system]

    ai_guard_client = AIGuard(token=pangea_api_key, config=PangeaConfig(base_url_template=pangea_base_url_template))
    guard_input_response = ai_guard_client.guard_text(
        messages=pangea_system + pangea_messages, recipe=pangea_input_recipe
    )

    assert guard_input_response.result is not None

    if guard_input_response.result.blocked:
        raise PangeaAIGuardBlockedError()

    if guard_input_response.result.transformed and guard_input_response.result.prompt_messages is not None:
        messages = [
            MessageTypeDef(role=message.role, content=[{"text": message.content}])
            for message in guard_input_response.result.prompt_messages
            if _is_user_or_assistant(message.role)
        ]

    bedrock_response = client.converse(**(kwargs | {"messages": messages}))
    output_message = bedrock_response["output"]["message"]

    guard_output_response = ai_guard_client.guard_text(
        messages=pangea_messages
        + [PangeaMessage(role=output_message["role"], content=_content_text(output_message["content"]))],
        recipe=pangea_output_recipe,
    )

    assert guard_output_response.result is not None

    if guard_output_response.result.blocked:
        raise PangeaAIGuardBlockedError()

    if guard_output_response.result.transformed and guard_output_response.result.prompt_messages is not None:
        output_message["content"] = [{"text": guard_output_response.result.prompt_messages[-1].content}]

    return bedrock_response
