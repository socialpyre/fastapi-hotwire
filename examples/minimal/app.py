"""Minimal fastapi-hotwire demo: a todo list with turbo-stream append/remove.

Run with::

    uv run uvicorn app:app --reload

Then open http://127.0.0.1:8000.
"""

from __future__ import annotations

from itertools import count
from pathlib import Path

from fastapi import FastAPI, Form, Request

from fastapi_hotwire import HotwireTemplates, TurboStreamResponse, streams

app = FastAPI()
templates = HotwireTemplates(directory=str(Path(__file__).parent / "templates"), flashes=False)

# In-memory store for the demo. Real apps would use a database.
_id = count(1)
todos: list[dict] = []


@app.get("/")
def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {"todos": todos})


@app.post("/todos")
def create(request: Request, text: str = Form(...)):
    todo = {"id": next(_id), "text": text}
    todos.append(todo)
    return templates.render_stream(
        request,
        "index.html",
        "todo_row",
        action="append",
        target="todos",
        todo=todo,
    )


@app.post("/todos/{todo_id}/delete")
def delete(request: Request, todo_id: int):
    global todos
    todos = [t for t in todos if t["id"] != todo_id]
    return TurboStreamResponse(streams.remove(target=f"todo-{todo_id}"))
