from __future__ import annotations

import logging
import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter, sleep
from typing import Any

import dotenv
import rtoml as toml

# --- Rich UI for users ---
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from examexam.apis.conversation_and_router import Conversation, Router
from examexam.find_the_toml import extract_questions_toml as extract_toml
from examexam.jinja_management import jinja_env

# Load environment variables (e.g., OPENAI_API_KEY)
dotenv.load_dotenv()

# ---- Logging setup (for developers) ----
# Keep logger.info/debug; print user-facing stuff with Rich Console.
logger = logging.getLogger(__name__)
if not logger.handlers:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO"),
        format="%(message)s",
        datefmt="%H:%M:%S",
        handlers=[RichHandler(rich_tracebacks=True, markup=True, show_time=False, show_level=True)],
    )

console = Console()


# ---------- Custom Exceptions ----------
class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""


class FatalLLMError(Exception):
    """Errors that should not be retried (e.g., missing API key)."""


# ---------- Helpers ----------
@dataclass
class GenStats:
    calls: int = 0
    tokens_prompt: int | None = None
    tokens_completion: int | None = None
    tokens_total: int | None = None
    last_call_seconds: float | None = None


def _validate_schema(data: dict[str, Any]) -> None:
    """
    Validates the structure of the parsed TOML data.
    Raises SchemaValidationError on failure.
    """
    if not isinstance(data, dict):
        raise SchemaValidationError("TOML content is not a dictionary.")

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise SchemaValidationError("TOML must contain a non-empty `[[questions]]` array of tables.")

    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            raise SchemaValidationError(f"Question {i + 1} is not a valid table/dictionary.")
        if "question" not in q or not isinstance(q["question"], str) or not q["question"]:
            raise SchemaValidationError(f"Question {i + 1} is missing a non-empty 'question' string.")

        options = q.get("options")
        if not isinstance(options, list) or not options:
            raise SchemaValidationError(
                f"Question {i + 1} '{q.get('question', '')[:30]}...' is missing a non-empty `[[questions.options]]` array."
            )

        saw_true = False
        for j, opt in enumerate(options):
            if not isinstance(opt, dict):
                raise SchemaValidationError(f"Option {j + 1} for question {i + 1} is not a valid table/dictionary.")
            if not isinstance(opt.get("text"), str) or not opt.get("text"):
                raise SchemaValidationError(f"Option {j + 1} for question {i + 1} is missing a 'text' string.")
            if not isinstance(opt.get("explanation"), str) or not opt.get("explanation"):
                raise SchemaValidationError(f"Option {j + 1} for question {i + 1} is missing an 'explanation' string.")
            if not isinstance(opt.get("is_correct"), bool):
                raise SchemaValidationError(
                    f"Option {j + 1} for question {i + 1} is missing an 'is_correct' boolean flag."
                )
            if opt["is_correct"]:
                saw_true = True

        if not saw_true:
            raise SchemaValidationError(
                f"Question {i + 1} '{q.get('question', '')[:30]}...' must have at least one option with is_correct = true."
            )


def create_new_conversation(system_prompt: str) -> Conversation:
    logger.debug("Creating new Conversation with system prompt length=%d", len(system_prompt))
    conversation = Conversation(system=system_prompt)
    return conversation


def _fatal_if_misconfigured(model: str) -> None:
    """Raise FatalLLMError for obviously fatal misconfigurations before calling LLM."""
    # Allow a stub model name used for tests.
    if model.lower() not in {"fakebot", "none", "noop"} and not os.getenv("OPENAI_API_KEY"):
        raise FatalLLMError("OPENAI_API_KEY is not set. Set the environment variable or pass api_key to the client.")


def _is_fatal_message(msg: str) -> bool:
    msg_lower = msg.lower()
    fatal_markers = [
        "unknown modelapi_key client option must be set",
        "no api key",
        "invalid api key",
        "unauthorized",
        "model not found",
        "does not exist or you do not have access",
        "access denied",
    ]
    return any(m in msg_lower for m in fatal_markers)


# def extract_toml(markdown_content: str) -> str | None:
#     """Extract TOML fenced block from markdown content."""
#     if not markdown_content:
#         logger.debug("No content returned from router.call; skipping TOML extract")
#         return None
#     match = re.search(r"```toml\n(.*?)\n```", markdown_content, re.DOTALL)
#     if match:
#         logger.info("TOML content found in response.")
#         return match.group(1)
#     logger.debug("TOML fenced block not found in content (len=%d)", len(markdown_content))
#     return None


def generate_questions(
    prompt: str,
    n: int,
    conversation: Conversation,
    service: str,
    model: str,
    *,
    max_retries: int = 2,
    retry_delay_seconds: float = 1.5,
    stats: GenStats | None = None,
) -> dict[str, list[dict[str, Any]]] | None:
    """
    Request questions from an LLM, validates the response, and retries with
    corrective feedback if parsing or schema validation fails.
    """
    logger.info("Generating %d questions for topic: %s", n, prompt)
    _fatal_if_misconfigured(model)

    # Render the prompt from the Jinja2 template
    try:
        template = jinja_env.get_template("generate.md.j2")
        original_user_prompt = template.render(n=n, prompt=prompt)
    except Exception as e:
        logger.error("Failed to load or render Jinja2 template 'generate.md.j2': %s", e)
        raise

    router = Router(conversation)
    current_user_prompt = original_user_prompt
    first_started = perf_counter()

    for attempt in range(max_retries + 1):
        logger.info(f"Generation attempt {attempt + 1}/{max_retries + 1}...")

        # --- 1. Call LLM ---
        try:
            started = perf_counter()
            content = router.call(current_user_prompt, model)
            duration = perf_counter() - started
            if stats:
                stats.calls += 1
                stats.last_call_seconds = duration
            logger.debug("router.call returned content length=%d in %.2fs", len(content or ""), duration)
        except Exception as e:
            msg = str(e)
            logger.error("API Error on attempt %d: %s", attempt + 1, msg)
            if _is_fatal_message(msg):
                logger.error("Fatal API error detected; aborting generation for this topic.")
                return None
            sleep(retry_delay_seconds * (attempt + 1))  # exponential backoff
            continue

        # --- 2. Extract TOML ---
        if not content:
            logger.warning("Attempt %d: Model returned empty content.", attempt + 1)
            current_user_prompt = (
                "Your previous response was empty. Please follow the instructions and generate the TOML content as requested.\n\n"
                + original_user_prompt
            )
            sleep(retry_delay_seconds)
            continue

        toml_content = extract_toml(content)
        if toml_content is None:
            logger.warning("Attempt %d: Failed to find TOML in model response.", attempt + 1)
            current_user_prompt = (
                "Your previous response did not contain a valid TOML code block. Please respond with ONLY the TOML content inside a ```toml ... ``` block, without any introductory text.\n\n"
                + original_user_prompt
            )
            sleep(retry_delay_seconds)
            continue

        # --- 3. Parse TOML ---
        try:
            parsed_data = toml.loads(toml_content)
        except toml.TOMLDecodeError as e:
            logger.warning("Attempt %d: Failed to parse TOML. Error: %s", attempt + 1, e)
            current_user_prompt = (
                f"Your previous TOML response had a syntax error: {e}. Please correct the syntax and provide the full, valid TOML again.\n\n"
                + original_user_prompt
            )
            sleep(retry_delay_seconds)
            continue

        # --- 4. Validate Schema ---
        try:
            _validate_schema(parsed_data)
            logger.info(
                "Successfully generated and validated %d questions in %.2fs",
                len(parsed_data.get("questions", [])),
                perf_counter() - first_started,
            )
            return parsed_data
        except SchemaValidationError as e:
            logger.warning("Attempt %d: Schema validation failed. Error: %s", attempt + 1, e)
            current_user_prompt = (
                f"Your previous TOML response was syntactically correct but failed schema validation: {e}. Please fix the structure and provide the full, valid TOML again.\n\n"
                + original_user_prompt
            )
            sleep(retry_delay_seconds)
            continue

    logger.error("Exceeded max retries (%d) for topic '%s'. Giving up.", max_retries, prompt)
    return None


def save_toml_to_file(toml_content: str, file_name: str) -> None:
    """Save TOML to file, appending to existing [[questions]]."""
    path = Path(file_name)
    logger.debug("Saving TOML to %s (exists=%s)", path, path.exists())
    try:
        if path.exists():
            with path.open(encoding="utf-8") as file:
                existing_content = toml.load(file)
            existing_content.setdefault("questions", [])
            new_questions = toml.loads(toml_content).get("questions", [])
            logger.debug(
                "Extending existing %d questions with %d new questions",
                len(existing_content["questions"]),
                len(new_questions),
            )
            existing_content["questions"].extend(new_questions)
            with path.open("w", encoding="utf-8") as file:
                toml.dump(existing_content, file)
        else:
            with path.open("w", encoding="utf-8") as file:
                file.write(toml_content)
        console.print(f"[bold green]TOML content saved to[/] {file_name}")
    except (toml.TomlParsingError, OSError) as e:
        logger.error(f"Failed to save TOML to {file_name}: {e}")
        console.print(f"[bold red]Error saving TOML to {file_name}. Check file permissions and content.[/bold red]")


def generate_questions_now(
    questions_per_toc_topic: int,
    file_name: str,
    toc_file: str,
    system_prompt: str,
    model: str = "fakebot",
) -> int:
    """Main execution with Rich progress UI."""
    toc_path = Path(toc_file)
    if not toc_path.exists():
        console.print(Panel.fit(f"[red]TOC file not found:[/] {toc_file}", title="Error"))
        return 0

    with toc_path.open(encoding="utf-8") as f:
        services = [line.strip() for line in f if line.strip()]

    total_topics = len(services)
    if total_topics == 0:
        console.print(Panel.fit("[yellow]TOC file is empty.[/]", title="Nothing to do"))
        return 0

    console.rule("[bold]Exam Question Generation")
    console.print(
        f"Generating [bold]{questions_per_toc_topic}[/] per topic across [bold]{total_topics}[/] topics with model [italic]{model}[/]…\n"
    )

    # Overall and per-topic progress bars.
    total_so_far = 0

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TextColumn("•"),
        TimeElapsedColumn(),
        TextColumn("ETA:"),
        TimeRemainingColumn(),
        expand=True,
        console=console,
        transient=False,
    )

    stats = GenStats()

    absolute_failures = 0
    with progress:
        overall_task = progress.add_task("Overall", total=total_topics)

        for idx, service in enumerate(services, start=1):
            topic_task = progress.add_task(f"{idx}/{total_topics} {service}", total=1)
            prompt = f"They must all be '{service}' questions."
            conversation = create_new_conversation(system_prompt)

            t0 = perf_counter()
            questions = generate_questions(
                prompt,
                questions_per_toc_topic,
                conversation,
                service,
                model,
                stats=stats,
            )
            dt = perf_counter() - t0

            if not questions:
                absolute_failures += 1
                progress.update(topic_task, description=f"{idx}/{total_topics} {service} [red](failed)[/]")
                if absolute_failures >= 3:
                    console.print(
                        "\n[bold red]Stopping due to 3 consecutive topic failures. Check API keys, model access, and network.[/bold red]"
                    )
                    break  # Exit the loop
            else:
                absolute_failures = 0  # Reset counter on success
                for question in questions.get("questions", []):
                    question["id"] = str(uuid.uuid4())

                total_so_far += len(questions.get("questions", []))
                logger.info("Total questions so far: %d", total_so_far)

                toml_content = toml.dumps(questions)
                save_toml_to_file(toml_content, file_name)

                progress.update(
                    topic_task,
                    description=f"{idx}/{total_topics} {service} [green](ok in {dt:.2f}s)[/]",
                )

            progress.advance(topic_task)
            progress.advance(overall_task)

    console.rule()
    console.print(
        Panel.fit(
            f"[bold green]Done[/]: generated [bold]{total_so_far}[/] questions across [bold]{total_topics}[/] topics.",
            title="Summary",
        )
    )
    return total_so_far


if __name__ == "__main__":
    # Example direct run; tweak as needed.
    generate_questions_now(
        questions_per_toc_topic=10,
        file_name="personal_multiple_choice_tests.toml",
        toc_file="../example_inputs/personally_important.txt",
        model="openai",
        system_prompt="We are writing multiple choice tests.",
    )
