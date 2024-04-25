import json
from metagpt.provider.bedrock.base_provider import BaseBedrockProvider
from metagpt.provider.bedrock.utils import messages_to_prompt_llama


class MistralProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-mistral.html

    def messages_to_prompt(self, messages: list[dict]):
        return messages_to_prompt_llama(messages)

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["outputs"][0]["text"]


class AnthropicProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-anthropic-claude-messages.html

    def get_request_body(self, messages: list[dict], **generate_kwargs):
        body = json.dumps(
            {"messages": messages, "anthropic_version": "bedrock-2023-05-31", **generate_kwargs})
        return body

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["content"][0]["text"]


class CohereProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-cohere-command.html

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generations"][0]["text"]


class MetaProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-meta.html
    max_tokens_field_name = "max_gen_len"

    def messages_to_prompt(self, messages: list[dict]):
        return messages_to_prompt_llama(messages)

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict["generation"]


class Ai21Provider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-jurassic2.html
    max_tokens_field_name = "maxTokens"

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict['completions'][0]["data"]["text"]


class AmazonProvider(BaseBedrockProvider):
    # See https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-titan-text.html
    max_tokens_field_name = "maxTokenCount"

    def get_request_body(self, messages: list[dict], **generate_kwargs):
        body = json.dumps({
            "inputText": self.messages_to_prompt(messages),
            "textGenerationConfig": generate_kwargs
        })
        return body

    def _get_completion_from_dict(self, rsp_dict: dict) -> str:
        return rsp_dict['results'][0]['outputText'].strip()

    def get_choice_text_from_stream(self, event) -> str:
        rsp_dict = json.loads(event["chunk"]["bytes"])
        completions = rsp_dict["outputText"]
        return completions


PROVIDERS = {
    "mistral": MistralProvider(),
    "meta": MetaProvider(),
    "ai21": Ai21Provider(),
    "cohere": CohereProvider(),
    "anthropic": AnthropicProvider(),
    "amazon": AmazonProvider()
}


def get_provider(model_id: str):
    model_name = model_id.split(".")[0]  # meta、mistral……
    if model_name not in PROVIDERS:
        raise KeyError(f"{model_name} is not supported!")
    return PROVIDERS[model_name]
