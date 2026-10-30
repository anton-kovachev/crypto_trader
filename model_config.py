import os

DEFAULT_MODEL_NAME = "openai.gpt-oss-120b"


def _configured_model_name(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if not value or value.casefold() == "none":
        return None
    return value


def resolve_model_name(model_name: str | None = None) -> str:
    return (
        _configured_model_name(model_name)
        or _configured_model_name(os.getenv("MODEL_NAME"))
        or DEFAULT_MODEL_NAME
    )
