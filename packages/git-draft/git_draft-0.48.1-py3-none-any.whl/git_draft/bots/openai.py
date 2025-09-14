"""OpenAI API-backed bots

They can be used with services other than OpenAI as long as them implement a
sufficient subset of the API. For example the `completions_bot` only requires
tools support.

See the following links for more resources:

* https://platform.openai.com/docs/assistants/tools/function-calling
* https://platform.openai.com/docs/assistants/deep-dive#runs-and-run-steps
* https://platform.openai.com/docs/api-reference/assistants-streaming/events
* https://github.com/openai/openai-python/blob/main/src/openai/resources/beta/threads/runs/runs.py
"""

from collections.abc import Mapping, Sequence
import json
import logging
from pathlib import PurePosixPath
from typing import Any, Self, TypedDict, cast, override

import openai

from ..common import JSONObject, UnreachableError, config_string, reindent
from ..instructions import SYSTEM_PROMPT
from .common import ActionSummary, Bot, Goal, UserFeedback, Worktree


_logger = logging.getLogger(__name__)


_DEFAULT_MODEL = "gpt-4o"


def completions_bot(
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = _DEFAULT_MODEL,
) -> Bot:
    """Compatibility-mode bot, uses completions with function calling"""
    return _CompletionsBot(_new_client(api_key, base_url), model)


def threads_bot(
    api_key: str | None = None,
    base_url: str | None = None,
    model: str = _DEFAULT_MODEL,
) -> Bot:
    """Beta bot, uses assistant threads with function calling"""
    return _ThreadsBot(_new_client(api_key, base_url), model)


def _new_client(api_key: str | None, base_url: str | None) -> openai.OpenAI:
    return openai.OpenAI(
        api_key=config_string(api_key) if api_key else None,
        base_url=base_url,
    )


class _ToolsFactory:
    def __init__(self, strict: bool) -> None:
        self._strict = strict

    def _param(
        self,
        name: str,
        description: str,
        inputs: Mapping[str, Any] | None = None,
        _required_inputs: Sequence[str] | None = None,
    ) -> openai.types.beta.FunctionToolParam:
        param: openai.types.beta.FunctionToolParam = {
            "type": "function",
            "function": {
                "name": name,
                "description": reindent(description),
                "parameters": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": inputs or {},
                    "required": list(inputs.keys()) if inputs else [],
                },
            },
        }
        if self._strict:
            param["function"]["strict"] = True
        return param

    def params(self) -> Sequence[openai.types.chat.ChatCompletionToolParam]:
        return [
            self._param(
                name="ask_user",
                description="""
                    Request more information from the user

                    Call this function if and only if you are unable to achieve
                    your task with the information you already have.
                """,
                inputs={
                    "question": {
                        "type": "string",
                        "description": "Question to be answered by the user",
                    },
                },
            ),
            self._param(
                name="list_files",
                description="List all available files",
            ),
            self._param(
                name="read_file",
                description="Get a file's contents",
                inputs={
                    "path": {
                        "type": "string",
                        "description": "Path of the file to be read",
                    },
                },
            ),
            self._param(
                name="write_file",
                description="""
                    Set a file's contents

                    The file will be created if it does not already exist.
                """,
                inputs={
                    "path": {
                        "type": "string",
                        "description": "Path of the file to be updated",
                    },
                    "contents": {
                        "type": "string",
                        "description": "New contents of the file",
                    },
                },
            ),
            self._param(
                name="delete_file",
                description="Delete a file",
                inputs={
                    "path": {
                        "type": "string",
                        "description": "Path of the file to be deleted",
                    },
                },
            ),
            self._param(
                name="rename_file",
                description="Rename a file",
                inputs={
                    "src_path": {
                        "type": "string",
                        "description": "Old file path",
                    },
                    "dst_path": {
                        "type": "string",
                        "description": "New file path",
                    },
                },
            ),
        ]


class _ToolHandler[V]:
    def __init__(self, tree: Worktree, feedback: UserFeedback) -> None:
        self._tree = tree
        self._feedback = feedback

    def _on_ask_user(self, response: str) -> V:
        raise NotImplementedError()

    def _on_read_file(self, path: PurePosixPath, contents: str | None) -> V:
        raise NotImplementedError()

    def _on_write_file(self, path: PurePosixPath) -> V:
        raise NotImplementedError()

    def _on_delete_file(self, path: PurePosixPath) -> V:
        raise NotImplementedError()

    def _on_rename_file(
        self, src_path: PurePosixPath, dst_path: PurePosixPath
    ) -> V:
        raise NotImplementedError()

    def _on_list_files(self, paths: Sequence[PurePosixPath]) -> V:
        raise NotImplementedError()

    def handle_function(self, function: Any) -> V:
        inputs = json.loads(function.arguments)
        _logger.info("Requested function: %s", function)
        match function.name:
            case "ask_user":
                question = inputs["question"]
                response = self._feedback.ask(question)
                return self._on_ask_user(response)
            case "read_file":
                path = PurePosixPath(inputs["path"])
                return self._on_read_file(path, self._tree.read_file(path))
            case "write_file":
                path = PurePosixPath(inputs["path"])
                contents = inputs["contents"]
                self._tree.write_file(path, contents)
                return self._on_write_file(path)
            case "delete_file":
                path = PurePosixPath(inputs["path"])
                self._tree.delete_file(path)
                return self._on_delete_file(path)
            case "rename_file":
                src_path = PurePosixPath(inputs["src_path"])
                dst_path = PurePosixPath(inputs["dst_path"])
                self._tree.rename_file(src_path, dst_path)
                return self._on_rename_file(src_path, dst_path)
            case "list_files":
                paths = self._tree.list_files()
                return self._on_list_files(paths)
            case _ as name:
                raise UnreachableError(f"Unexpected function: {name}")


class _CompletionsBot(Bot):
    def __init__(self, client: openai.OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    async def act(
        self, goal: Goal, tree: Worktree, feedback: UserFeedback
    ) -> ActionSummary:
        tools = _ToolsFactory(strict=False).params()
        tool_handler = _CompletionsToolHandler(tree, feedback)

        messages: list[openai.types.chat.ChatCompletionMessageParam] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": goal.prompt},
        ]

        request_count = 0
        while True:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="required",
            )
            assert len(response.choices) == 1
            choice = response.choices[0]
            request_count += 1

            done = True
            messages.append(cast(Any, choice.message.to_dict(mode="json")))
            calls = choice.message.tool_calls
            for call in calls or []:
                output = tool_handler.handle_function(call.function)
                if output is not None:
                    done = False
                    messages.append({"role": "user", "content": output})
            if done:
                break

        return ActionSummary(request_count=request_count)


class _CompletionsToolHandler(_ToolHandler[str | None]):
    def _on_ask_user(self, response: str) -> str:
        return response

    def _on_read_file(self, path: PurePosixPath, contents: str | None) -> str:
        if contents is None:
            return f"`{path}` does not exist."
        return f"The contents of `{path}` are:\n\n```\n{contents}\n```\n"

    def _on_write_file(self, _path: PurePosixPath) -> None:
        return None

    def _on_delete_file(self, _path: PurePosixPath) -> None:
        return None

    def _on_rename_file(
        self, _src_path: PurePosixPath, _dst_path: PurePosixPath
    ) -> None:
        return None

    def _on_list_files(self, paths: Sequence[PurePosixPath]) -> str:
        joined = "\n".join(f"* {p}" for p in paths)
        return f"Here are the available files: {joined}"


class _ThreadsBot(Bot):
    def __init__(self, client: openai.OpenAI, model: str) -> None:
        self._client = client
        self._model = model

    def _load_assistant_id(self) -> str:
        kwargs: JSONObject = dict(
            model=self._model,
            instructions=SYSTEM_PROMPT,
            tools=_ToolsFactory(strict=True).params(),
        )
        path = self.state_folder_path(ensure_exists=True) / "ASSISTANT_ID"
        try:
            with open(path) as f:
                assistant_id = f.read()
            self._client.beta.assistants.update(assistant_id, **kwargs)
        except (FileNotFoundError, openai.NotFoundError):
            assistant = self._client.beta.assistants.create(**kwargs)
            assistant_id = assistant.id
            with open(path, "w") as f:
                f.write(assistant_id)
        return assistant_id

    async def act(
        self, goal: Goal, tree: Worktree, feedback: UserFeedback
    ) -> ActionSummary:
        assistant_id = self._load_assistant_id()

        thread = self._client.beta.threads.create()
        self._client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=goal.prompt,
        )

        # We intentionally do not count the two requests above, to focus on
        # "data requests" only.
        action = ActionSummary(request_count=0, token_count=0)
        with self._client.beta.threads.runs.stream(
            thread_id=thread.id,
            assistant_id=assistant_id,
            event_handler=_EventHandler(self._client, tree, feedback, action),
        ) as stream:
            stream.until_done()
        return action


class _EventHandler(openai.AssistantEventHandler):
    def __init__(
        self,
        client: openai.Client,
        tree: Worktree,
        feedback: UserFeedback,
        action: ActionSummary,
    ) -> None:
        super().__init__()
        self._client = client
        self._tree = tree
        self._feedback = feedback
        self._action = action
        self._action.increment_request_count()

    def _clone(self) -> Self:
        return self.__class__(
            self._client, self._tree, self._feedback, self._action
        )

    @override
    def on_event(self, event: openai.types.beta.AssistantStreamEvent) -> None:
        if event.event == "thread.run.requires_action":
            run_id = event.data.id  # Retrieve the run ID from the event data
            self._handle_action(run_id, event.data)
        elif event.event == "thread.run.completed":
            _logger.info("Threads run completed. [usage=%s]", event.data.usage)
        else:
            _logger.debug("Threads event: %s", event)

    @override
    def on_run_step_done(
        self, run_step: openai.types.beta.threads.runs.RunStep
    ) -> None:
        usage = run_step.usage
        if usage:
            _logger.debug("Threads run step usage: %s", usage)
            self._action.increment_token_count(usage.total_tokens)
        else:
            _logger.warning("Missing usage in threads run step")

    def _handle_action(self, _run_id: str, data: Any) -> None:
        tool_outputs = list[Any]()
        for tool in data.required_action.submit_tool_outputs.tool_calls:
            handler = _ThreadToolHandler(self._tree, self._feedback, tool.id)
            tool_outputs.append(handler.handle_function(tool.function))

        run = self.current_run
        assert run, "No ongoing run"
        with self._client.beta.threads.runs.submit_tool_outputs_stream(
            thread_id=run.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs,
            event_handler=self._clone(),
        ) as stream:
            stream.until_done()


class _ToolOutput(TypedDict):
    tool_call_id: str
    output: str


class _ThreadToolHandler(_ToolHandler[_ToolOutput]):
    def __init__(
        self, tree: Worktree, feedback: UserFeedback, call_id: str
    ) -> None:
        super().__init__(tree, feedback)
        self._call_id = call_id

    def _wrap(self, output: str) -> _ToolOutput:
        return _ToolOutput(tool_call_id=self._call_id, output=output)

    def _on_ask_user(self, response: str) -> _ToolOutput:
        return self._wrap(response)

    def _on_read_file(
        self, _path: PurePosixPath, contents: str | None
    ) -> _ToolOutput:
        return self._wrap(contents or "")

    def _on_write_file(self, _path: PurePosixPath) -> _ToolOutput:
        return self._wrap("OK")

    def _on_delete_file(self, _path: PurePosixPath) -> _ToolOutput:
        return self._wrap("OK")

    def _on_rename_file(
        self, _src_path: PurePosixPath, _dst_path: PurePosixPath
    ) -> _ToolOutput:
        return self._wrap("OK")

    def _on_list_files(self, paths: Sequence[PurePosixPath]) -> _ToolOutput:
        return self._wrap("\n".join(str(p) for p in paths))
