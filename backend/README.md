# Local Ollama Chat API

The FastAPI application is organized by responsibility:

- `app/api/` contains HTTP routes.
- `app/services/` contains chat orchestration and model integration.
- `app/repositories/` contains SQLModel-based persistence.
- `app/models/` contains SQLModel entities.
- `app/schemas/` contains API request models.
- `alembic/` contains versioned schema migrations.
- `data/chat.db` is the default SQLite database.

## Run

1. Install and start [Ollama](https://ollama.com/), then download the default
   model:

   ```powershell
   ollama pull mridiot918/qwen3.6-27b-uncensored
   ```

2. From this directory, create a virtual environment, install dependencies,
   and start the API:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   uvicorn app.main:app --reload --access-log --log-level info
   ```

   For a direct run without reload, use:

   ```powershell
   python .\app\main.py
   ```

If the frontend is running in WSL while this backend runs on Windows, bind the
API to an interface reachable from WSL:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --access-log --log-level info
```

Configure Windows Firewall to allow port 8000 only from trusted local/WSL
networks. Keep the default loopback binding when the frontend and backend run
directly on the same host.

The API uses `http://localhost:11434` and the
`mridiot918/qwen3.6-27b-uncensored` model by default. Set `OLLAMA_BASE_URL` or
`OLLAMA_MODEL` to override either value. Requests time out after 60 seconds by
default; set `OLLAMA_REQUEST_TIMEOUT` to change this.

Conversations and messages are stored in `data/chat.db`. Alembic applies schema
migrations at startup; the initial revision adopts an existing chat schema
without recreating its tables. Set `CHAT_DATABASE_PATH` to use another database
location. User messages are persisted before generation; assistant replies move
through `pending`, `streaming`, and `completed`, `interrupted`, or `failed`. A
restart marks unfinished replies as interrupted.

Characters and personas are stored as reusable profiles. A character describes
the role played by the agent; a persona describes the role the user acts as.
Each conversation stores both profile IDs. Editing a profile keeps existing
conversation associations and does not alter stored messages; subsequent model
requests use the edited profile definition. A profile used by a conversation
cannot be deleted.

Generation settings are saved in the database and used for each model request:
selected Ollama model, response token limit (`num_predict`), temperature, and
top-p. User messages are read-only. Only the latest assistant response can be
regenerated, and regeneration replaces that response. Conversation titles can
be changed and conversations deleted. The prompt inspection endpoint returns
the system prompt and active generation settings. Before creating a
conversation, users can preview and edit the generated system prompt; the
result is saved as a snapshot for that conversation.

Create a new schema revision after changing the SQLModel entities with:

```powershell
alembic revision --autogenerate -m "describe the schema change"
```

Review the generated revision before applying it. The application applies
revisions on startup; `alembic upgrade head` can also be run manually.

## API

Create, list, edit, and delete characters at `/characters` and personas at
`/personas` using `POST`, `GET`, `PUT /{profile_id}`, and `DELETE /{profile_id}`.
Conversation creation requires both profile IDs:

```json
{
  "id": "a1289e4f-8f4d-4e94-94d7-c59e47fc4c44",
  "character_id": "b21fe086-8fba-4e30-a1bc-cfd80dd87009",
  "persona_id": "f26cfac6-6c58-40b6-bb91-67e1c1faaf0e"
}
```

List conversations with `GET /conversations` and retrieve stored messages and
their profile associations with `GET /conversations/{conversation_id}`.
Rename a conversation with `PATCH /conversations/{conversation_id}` using
`{"title":"A new title"}`; delete it with `DELETE` on the same path.

`POST /chat` accepts a non-blank `message` (up to 20,000 characters) and a
`conversation_id` belonging to an existing conversation:

```json
{
  "message": "Explain what FastAPI is.",
  "conversation_id": "a1289e4f-8f4d-4e94-94d7-c59e47fc4c44"
}
```

The response uses `text/event-stream`. Generated fragments arrive as `token`
events followed by `done`. If Ollama is unavailable, the model cannot be found,
or a request times out, the stream contains an `error` event.

Use `POST /messages/{message_id}/regenerate` to replace the latest assistant
response. Requests to regenerate an earlier response return `409 Conflict`.

Read or update generation settings with `GET` or `PUT /settings`. The payload
contains `model_name`, `num_predict` (1-32768), `temperature` (0-2), and `top_p`
(greater than 0 through 1). `GET /settings/models` lists models installed in
Ollama. Inspect the assembled prompt and active options with
`GET /conversations/{conversation_id}/prompt`. Preview the generated prompt for
selected profiles with `POST /conversations/prompt-preview`.

Example chat request (after creating a character, a persona, and the conversation):

```powershell
curl.exe -N -H "Content-Type: application/json" -d '{"message":"Hello!","conversation_id":"a1289e4f-8f4d-4e94-94d7-c59e47fc4c44"}' http://localhost:8000/chat
```
