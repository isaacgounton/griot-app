from pydantic_settings import BaseSettings


class AgentSettings(BaseSettings):
    """Agent settings that can be set using environment variables.
    Reference: https://pydantic-docs.helpmanual.io/usage/settings/
    """

    gpt_5_mini: str = "deepseek/deepseek-chat-v3.1:free"
    gpt_4: str = "openai/gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    default_max_completion_tokens: int = 16000
    default_temperature: float = 0


# Create an TeamSettings object
agent_settings = AgentSettings()
