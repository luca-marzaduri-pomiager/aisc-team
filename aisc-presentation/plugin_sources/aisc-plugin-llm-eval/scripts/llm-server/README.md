This app allow running a server on a remote machine to get the outputs of the LLM(s).

# Installation

```bash
uv sync
```

# Run server:

```bash
uv run uvicorn src.llm_server.__main__:app --port 9008 --host 0.0.0.0
```
