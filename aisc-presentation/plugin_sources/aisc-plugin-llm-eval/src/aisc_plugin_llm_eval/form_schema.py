from pydantic import BaseModel, Field


class ConfigFormSchema(BaseModel):
    endpoint: str = Field(
        default="",
        title="Remote Endpoint",
        description="Endpoint for generating outputs with LLMs (Experimental)",
        examples=[
            "http://host.docker.internal:9008/generate",
            "http://localhost:9008/generate",
        ],
    )

    # prompt template
    prompt_template: str = Field(
        default="",
        title="Prompt Template",
        description=(
            "Enter the prompt template to evaluate the LLM: "
            "'Question:{{question}}:\nAnswer:'"
        ),
    )

    # Evaluated LLM
    model_name: str = Field(
        default="",
        title="Evaluated LLM",
        description="Model name from Hugging Face",
        examples=["ibm-granite/granite-4.0-h-350m"],
    )

    batch_size: int = Field(
        default=1,
        title="Batch size",
        description="Number of items per batch",
        gt=0,
    )

    temperature: float = Field(
        default=0.6,
        title="Temperature",
        description="Sampling temperature",
        multiple_of=0.01,
        gt=0.0,
    )

    max_new_tokens: int = Field(
        default=512,
        title="Maximum new tokens",
        description="Maximum tokens to generate (may be capped to fit context)",
        gt=1,
    )

    enable_top_p: bool = Field(
        default=False,
        title="Enable to set top_p",
    )

    top_p: float = Field(
        default=0.9,
        title="top_p: Nucleus sampling parameter",
        description="Optional float between 0 and 1",
        multiple_of=0.01,
        ge=0.0,
        le=1.0,
    )

    # single prompt mode
    prompt: str = Field(
        default="",
        title="Prompt",
        description="Enter the prompt to evaluate the LLM",
    )

    answer: str = Field(
        default="",
        title="Answer (Optional)",
        description="An expected answer to the provided prompt",
    )

    # Judge LLM
    model_judge_name: str = Field(
        default="",
        title="Judge LLM (Optional)",
        description="Model name from Hugging Face",
        examples=["LiquidAI/LFM2.5-1.2B-Thinking"],
    )

    batch_size_judge: int = Field(
        default=1,
        title="Batch size for the Judge LLM",
        description="Number of items per batch for the Judge LLM",
        gt=0,
    )

    retries_judge: int = Field(
        default=3,
        title="Number of Judge LLM Retries",
        description="Number of times to retry the Judge LLM if JSON parsing fails.",
        gt=0,
    )

    temperature_judge: float = Field(
        default=0.6,
        title="Temperature for the Judge LLM",
        description="Sampling temperature",
        multiple_of=0.01,
        gt=0.0,
    )

    max_new_tokens_judge: int = Field(
        default=512,
        title="Maximum new tokens",
        description="Maximum tokens to generate for the Judge LLM (may be capped to fit context)",
        gt=1,
    )

    enable_top_p_judge: bool = Field(
        default=False,
        title="Enable to set top_p for the Judge LLM",
    )

    top_p_judge: float = Field(
        default=0.9,
        title="top_p: Nucleus sampling parameter for the Judge LLM",
        description="Optional float between 0 and 1",
        multiple_of=0.01,
        ge=0.0,
        le=1.0,
    )

    regex_pattern: str = Field(
        default="",
        title="Regular Expression expected in the model response",
    )
