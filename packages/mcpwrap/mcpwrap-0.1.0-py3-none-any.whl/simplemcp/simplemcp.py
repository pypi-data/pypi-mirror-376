"""
SimpleMCP — Minimal MCP-like tool wrapper library
Exposes Python functions as HTTP endpoints automatically.
"""

import inspect
import typing
from typing import Any, Callable, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Registry for tools
tool_registry: Dict[str, Dict[str, Any]] = {}

# ---------------------
# Schema generation
# ---------------------
def type_to_schema(t: Any) -> Dict[str, Any]:
    if t is str:
        return {"type": "string"}
    if t is int:
        return {"type": "integer"}
    if t is float:
        return {"type": "number"}
    if t is bool:
        return {"type": "boolean"}
    if t is list or t == typing.List[str]:
        return {"type": "array"}
    if t is dict or t == typing.Dict[str, Any]:
        return {"type": "object"}
    if hasattr(t, "__fields__") and issubclass(t, BaseModel):
        return {"type": "object", "properties": {f: type_to_schema(fld.outer_type_) for f, fld in t.__fields__.items()}}
    return {"type": "string"}

# ---------------------
# Decorator
# ---------------------
def tool(name: str, desc: str = "", params: Dict[str, str] = None):
    def decorator(func: Callable):
        sig = inspect.signature(func)
        schema = {
            "name": name,
            "description": desc or func.__doc__ or "",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        for pname, param in sig.parameters.items():
            ann = param.annotation if param.annotation != inspect._empty else str
            schema["parameters"]["properties"][pname] = type_to_schema(ann)
            if param.default == inspect._empty:
                schema["parameters"]["required"].append(pname)

        tool_registry[name] = {"func": func, "schema": schema}
        return func
    return decorator

# ---------------------
# Server
# ---------------------
def run_server(host: str = "127.0.0.1", port: int = 8000):
    app = FastAPI()

    @app.get("/")
    def root():
        return {"status": "ok", "tools": list(tool_registry.keys())}

    @app.get("/tools")
    def list_tools():
        return {name: meta["schema"] for name, meta in tool_registry.items()}

    # Register each tool as its own POST endpoint
    for name, meta in tool_registry.items():
        func = meta["func"]
        schema = meta["schema"]

        async def tool_endpoint(payload: Dict[str, Any], _func=func, _schema=schema):
            try:
                return {"output": _func(**payload)}
            except Exception as e:
                raise HTTPException(status_code=400, detail=str(e))

        app.post(f"/{name}")(tool_endpoint)

    uvicorn.run(app, host=host, port=port)

# ---------------------
# Local testing
# ---------------------
def test_tool(name: str, args: Dict[str, Any]):
    if name not in tool_registry:
        raise ValueError(f"Tool {name} not found")
    return tool_registry[name]["func"](**args)