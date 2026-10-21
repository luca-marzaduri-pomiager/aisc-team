import asyncio
from typing import Optional, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from pydantic import BaseModel

from .provider import create_llm


def clear_cuda_cache():
    """Clear CUDA cache to prevent OOM errors."""
    import torch

    if torch.cuda.is_available():
        torch.cuda.empty_cache()


class LLMResponse(BaseModel):
    content: str
    logprobs: Optional[dict[str, Any]] = None


class ModelConfig(BaseModel):
    model_name: str
    device: Optional[str] = None
    load_in_4bit: Optional[bool] = False
    load_in_8bit: Optional[bool] = False
    enable_compile: Optional[bool] = False
    provider: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    model_path: Optional[str] = None
    n_gpu_layers: Optional[int] = None


class PromptConfig(BaseModel):
    prompts: str | list
    max_new_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    topk_logprobs: Optional[int] = None


class GenerationRequest(BaseModel):
    model: ModelConfig
    prompt: PromptConfig


async def get_or_load_model(app: FastAPI, config: ModelConfig):
    """
    1) if model exists -> return
    2) if not -> load under lock to prevent double-loading
    """
    if config.model_name in app.state.models:
        return app.state.models[config.model_name]

    if config.model_name not in app.state.model_locks:
        app.state.model_locks[config.model_name] = asyncio.Lock()

    async with app.state.model_locks[config.model_name]:
        # double-check inside lock
        if config.model_name in app.state.models:
            return app.state.models[config.model_name]

        # load the model
        app.state.models[config.model_name] = create_llm(**config.model_dump())
        return app.state.models[config.model_name]


async def unload_models(app: FastAPI):
    for model_name, model in app.state.models.items():
        model.unload()

    app.state.models.clear()
    app.state.model_locks.clear()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.models: dict[str, Any] = {}
    app.state.model_locks = {}

    yield

    await unload_models(app)


app = FastAPI(lifespan=lifespan)


@app.post("/generate", response_model=list[LLMResponse])
async def generate(request: Request, body: GenerationRequest):
    """
    Generate the outputs for a single batch of inputs
    """
    llm = await get_or_load_model(request.app, body.model)
    responses = await asyncio.to_thread(llm.generate, **body.prompt.model_dump())
    clear_cuda_cache()
    return [LLMResponse(**r.__dict__) for r in responses]


@app.post("/unload_all_models")
async def unload_models_endpoint(request: Request):
    """
    Unload all models from the app state
    """
    await unload_models(request.app)
    return {"status": "models unloaded"}
