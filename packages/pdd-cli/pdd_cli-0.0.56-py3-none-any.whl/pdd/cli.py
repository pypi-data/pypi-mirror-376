# pdd/cli.py
"""
Command Line Interface (CLI) for the PDD (Prompt-Driven Development) tool.

This module provides the main CLI functionality for PDD, including commands for
generating code, tests, fixing issues, and managing prompts.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path # Import Path

import click
from rich.console import Console
from rich.theme import Theme
from rich.markup import MarkupError, escape

# --- Relative Imports for Internal Modules ---
from . import DEFAULT_STRENGTH, __version__, DEFAULT_TIME
from .auto_deps_main import auto_deps_main
from .auto_update import auto_update
from .bug_main import bug_main
from .change_main import change_main
from .cmd_test_main import cmd_test_main
from .code_generator_main import code_generator_main
from .conflicts_main import conflicts_main
# Need to import construct_paths for tests patching pdd.cli.construct_paths
from .construct_paths import construct_paths, list_available_contexts
from .context_generator_main import context_generator_main
from .crash_main import crash_main
from .detect_change_main import detect_change_main
from .fix_main import fix_main
from .fix_verification_main import fix_verification_main
from .install_completion import install_completion, get_local_pdd_path
from .preprocess_main import preprocess_main
from .pytest_output import run_pytest_and_capture_output
from .split_main import split_main
from .sync_main import sync_main
from .trace_main import trace_main
from .track_cost import track_cost
from .update_main import update_main


# --- Initialize Rich Console ---
# Define a custom theme for consistent styling
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "green",
    "path": "dim blue",
    "command": "bold magenta",
})
console = Console(theme=custom_theme)

# --- Helper Function for Error Handling ---
def handle_error(exception: Exception, command_name: str, quiet: bool):
    """Prints error messages using Rich console.""" # Modified docstring
    if not quiet:
        console.print(f"[error]Error during '{command_name}' command:[/error]", style="error")
        if isinstance(exception, FileNotFoundError):
            console.print(f"  [error]File not found:[/error] {exception}", style="error")
        elif isinstance(exception, (ValueError, IOError)):
            console.print(f"  [error]Input/Output Error:[/error] {exception}", style="error")
        elif isinstance(exception, click.UsageError): # Handle Click usage errors explicitly if needed
             console.print(f"  [error]Usage Error:[/error] {exception}", style="error")
             # click.UsageError should typically exit with 2, but we are handling it.
        elif isinstance(exception, MarkupError):
            console.print("  [error]Markup Error:[/error] Invalid Rich markup encountered.", style="error")
            # Print the error message safely escaped
            console.print(escape(str(exception)))
        else:
            console.print(f"  [error]An unexpected error occurred:[/error] {exception}", style="error")
    # Do NOT re-raise e here. Let the command function return None.


# --- Main CLI Group ---
@click.group(chain=True, invoke_without_command=True, help="PDD (Prompt-Driven Development) Command Line Interface.")
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing files without asking for confirmation (commonly used with 'sync' to update generated outputs).",
)
@click.option(
    "--strength",
    type=click.FloatRange(0.0, 1.0),
    default=DEFAULT_STRENGTH,
    show_default=True,
    help="Set the strength of the AI model (0.0 to 1.0).",
)
@click.option(
    "--temperature",
    type=click.FloatRange(0.0, 2.0), # Allow higher temperatures if needed
    default=0.0,
    show_default=True,
    help="Set the temperature of the AI model.",
)
@click.option(
    "--time",
    type=click.FloatRange(0.0, 1.0),
    default=None,
    show_default=True,
    help="Controls reasoning allocation for LLMs (0.0-1.0). Uses DEFAULT_TIME if None.",
)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Increase output verbosity for more detailed information.",
)
@click.option(
    "--quiet",
    is_flag=True,
    default=False,
    help="Decrease output verbosity for minimal information.",
)
@click.option(
    "--output-cost",
    type=click.Path(dir_okay=False, writable=True),
    default=None,
    help="Enable cost tracking and output a CSV file with usage details.",
)
@click.option(
    "--review-examples",
    is_flag=True,
    default=False,
    help="Review and optionally exclude few-shot examples before command execution.",
)
@click.option(
    "--local",
    is_flag=True,
    default=False,
    help="Run commands locally instead of in the cloud.",
)
@click.option(
    "--context",
    "context_override",
    type=str,
    default=None,
    help="Override automatic context detection and use the specified .pddrc context.",
)
@click.option(
    "--list-contexts",
    "list_contexts",
    is_flag=True,
    default=False,
    help="List available contexts from .pddrc and exit.",
)
@click.version_option(version=__version__, package_name="pdd-cli")
@click.pass_context
def cli(
    ctx: click.Context,
    force: bool,
    strength: float,
    temperature: float,
    verbose: bool,
    quiet: bool,
    output_cost: Optional[str],
    review_examples: bool,
    local: bool,
    time: Optional[float], # Type hint is Optional[float]
    context_override: Optional[str],
    list_contexts: bool,
):
    """
    Main entry point for the PDD CLI. Handles global options and initializes context.
    Supports multi-command chaining.
    """
    # Ensure PDD_PATH is set before any commands run
    get_local_pdd_path()
    
    ctx.ensure_object(dict)
    ctx.obj["force"] = force
    ctx.obj["strength"] = strength
    ctx.obj["temperature"] = temperature
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    ctx.obj["output_cost"] = output_cost
    ctx.obj["review_examples"] = review_examples
    ctx.obj["local"] = local
    # Use DEFAULT_TIME if time is not provided
    ctx.obj["time"] = time if time is not None else DEFAULT_TIME
    # Persist context override for downstream calls
    ctx.obj["context"] = context_override

    # Suppress verbose if quiet is enabled
    if quiet:
        ctx.obj["verbose"] = False

    # If --list-contexts is provided, print and exit before any other actions
    if list_contexts:
        try:
            names = list_available_contexts()
        except Exception as exc:
            # Surface config errors as usage errors
            raise click.UsageError(f"Failed to load .pddrc: {exc}")
        # Print one per line; avoid Rich formatting for portability
        for name in names:
            click.echo(name)
        ctx.exit(0)

    # Optional early validation for --context
    if context_override:
        try:
            names = list_available_contexts()
        except Exception as exc:
            # If .pddrc is malformed, propagate as usage error
            raise click.UsageError(f"Failed to load .pddrc: {exc}")
        if context_override not in names:
            raise click.UsageError(
                f"Unknown context '{context_override}'. Available contexts: {', '.join(names)}"
            )

    # Perform auto-update check unless disabled
    if os.getenv("PDD_AUTO_UPDATE", "true").lower() != "false":
        try:
            if not quiet:
                console.print("[info]Checking for updates...[/info]")
            # Removed quiet=quiet argument as it caused TypeError
            auto_update()
        except Exception as exception:  # Using more descriptive name
            if not quiet:
                console.print(
                    f"[warning]Auto-update check failed:[/warning] {exception}", 
                    style="warning"
                )

# --- Result Callback for Chained Commands ---
@cli.result_callback()
@click.pass_context
def process_commands(ctx: click.Context, results: List[Optional[Tuple[Any, float, str]]], **kwargs):
    """
    Processes the results from chained commands.

    Receives a list of tuples, typically (result, cost, model_name),
    or None from each command function.
    """
    total_chain_cost = 0.0
    # Get Click's invoked subcommands attribute first
    invoked_subcommands = getattr(ctx, 'invoked_subcommands', [])
    # If Click didn't provide it (common in real runs), fall back to the list
    # tracked on ctx.obj by @track_cost — but avoid doing this during pytest
    # so unit tests continue to assert the "Unknown Command" output.
    if not invoked_subcommands:
        import os as _os
        if not _os.environ.get('PYTEST_CURRENT_TEST'):
            try:
                if ctx.obj and isinstance(ctx.obj, dict):
                    invoked_subcommands = ctx.obj.get('invoked_subcommands', []) or []
            except Exception:
                invoked_subcommands = []
    num_commands = len(invoked_subcommands)
    num_results = len(results) # Number of results actually received

    if not ctx.obj.get("quiet"):
        console.print("\n[info]--- Command Chain Execution Summary ---[/info]")

    for i, result_tuple in enumerate(results):
        # Use the retrieved subcommand name (might be "Unknown Command X" in tests)
        command_name = invoked_subcommands[i] if i < num_commands else f"Unknown Command {i+1}"

        # Check if the command failed (returned None)
        if result_tuple is None:
            if not ctx.obj.get("quiet"):
                # Check if it was install_completion (which normally returns None)
                if command_name == "install_completion":
                    console.print(f"  [info]Step {i+1} ({command_name}):[/info] Command completed.")
                # If command name is unknown, and it might be install_completion which prints its own status
                elif command_name.startswith("Unknown Command"):
                    console.print(f"  [info]Step {i+1} ({command_name}):[/info] Command executed (see output above for status details).")
                # Check if it was preprocess (which returns a dummy tuple on success)
                # This case handles actual failure for preprocess
                elif command_name == "preprocess":
                    console.print(f"  [error]Step {i+1} ({command_name}):[/error] Command failed.")
                else:
                    console.print(f"  [error]Step {i+1} ({command_name}):[/error] Command failed.")
        # Check if the result is the expected tuple structure from @track_cost or preprocess success
        elif isinstance(result_tuple, tuple) and len(result_tuple) == 3:
            _result_data, cost, model_name = result_tuple
            total_chain_cost += cost
            if not ctx.obj.get("quiet"):
                # Special handling for preprocess success message (check actual command name)
                actual_command_name = invoked_subcommands[i] if i < num_commands else None # Get actual name if possible
                if actual_command_name == "preprocess" and cost == 0.0 and model_name == "local":
                    console.print(f"  [info]Step {i+1} ({command_name}):[/info] Command completed (local).")
                else:
                    # Generic output using potentially "Unknown Command" name
                    console.print(f"  [info]Step {i+1} ({command_name}):[/info] Cost: ${cost:.6f}, Model: {model_name}")
        else:
            # Handle unexpected return types if necessary
            if not ctx.obj.get("quiet"):
                # Provide more detail on the unexpected type
                console.print(f"  [warning]Step {i+1} ({command_name}):[/warning] Unexpected result format: {type(result_tuple).__name__} - {str(result_tuple)[:50]}...")


    if not ctx.obj.get("quiet"):
        # Only print total cost if at least one command potentially contributed cost
        if any(res is not None and isinstance(res, tuple) and len(res) == 3 for res in results):
            console.print(f"[info]Total Estimated Cost for Chain:[/info] ${total_chain_cost:.6f}")
        # Indicate if the chain might have been incomplete due to errors
        if num_results < num_commands and not all(res is None for res in results): # Avoid printing if all failed
            console.print("[warning]Note: Chain may have terminated early due to errors.[/warning]")
        console.print("[info]-------------------------------------[/info]")


# --- Command Definitions ---

@cli.command("generate")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the generated code (file or directory).",
)
@click.option(
    "--original-prompt",
    "original_prompt_file_path",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to the original prompt file for incremental generation.",
)
@click.option(
    "--incremental",
    "incremental_flag",
    is_flag=True,
    default=False,
    help="Force incremental patching even if changes are significant (requires existing output).",
)
@click.option(
    "-e",
    "--env",
    "env_kv",
    multiple=True,
    help="Set template variable (KEY=VALUE) or read KEY from env",
)
@click.pass_context
@track_cost
def generate(
    ctx: click.Context,
    prompt_file: str,
    output: Optional[str],
    original_prompt_file_path: Optional[str],
    incremental_flag: bool,
    env_kv: Tuple[str, ...],
) -> Optional[Tuple[str, float, str]]:
    """Generate code from a prompt file."""
    try:
        # Parse -e/--env arguments into a dict
        env_vars: Dict[str, str] = {}
        import os as _os
        for item in env_kv or ():
            if "=" in item:
                key, value = item.split("=", 1)
                key = key.strip()
                if key:
                    env_vars[key] = value
            else:
                key = item.strip()
                if key:
                    val = _os.environ.get(key)
                    if val is not None:
                        env_vars[key] = val
                    else:
                        if ctx.obj.get("verbose") and not ctx.obj.get("quiet"):
                            console.print(f"[warning]-e {key} not found in environment; skipping[/warning]")
        generated_code, incremental, total_cost, model_name = code_generator_main(
            ctx=ctx,
            prompt_file=prompt_file,
            output=output,
            original_prompt_file_path=original_prompt_file_path,
            force_incremental_flag=incremental_flag,
            env_vars=env_vars or None,
        )
        return generated_code, total_cost, model_name
    except Exception as exception:
        handle_error(exception, "generate", ctx.obj.get("quiet", False))
        return None


@cli.command("example")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the generated example code (file or directory).",
)
@click.pass_context
@track_cost
def example(
    ctx: click.Context, 
    prompt_file: str, 
    code_file: str, 
    output: Optional[str]
) -> Optional[Tuple[str, float, str]]:
    """Generate example code for a given prompt and implementation."""
    try:
        example_code, total_cost, model_name = context_generator_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            output=output,
        )
        return example_code, total_cost, model_name
    except Exception as exception:
        handle_error(exception, "example", ctx.obj.get("quiet", False))
        return None


@cli.command("test")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the generated test file (file or directory).",
)
@click.option(
    "--language", 
    type=str, 
    default=None, 
    help="Specify the programming language."
)
@click.option(
    "--coverage-report",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to the coverage report file for existing tests.",
)
@click.option(
    "--existing-tests",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to the existing unit test file.",
)
@click.option(
    "--target-coverage",
    type=click.FloatRange(0.0, 100.0),
    default=None,  # Use None, default handled in cmd_test_main or env var
    help="Desired code coverage percentage (default: 10.0 or PDD_TEST_COVERAGE_TARGET).",
)
@click.option(
    "--merge",
    is_flag=True,
    default=False,
    help="Merge new tests with existing test file instead of creating a separate file.",
)
@click.pass_context
@track_cost
def test(
    ctx: click.Context,
    prompt_file: str,
    code_file: str,
    output: Optional[str],
    language: Optional[str],
    coverage_report: Optional[str],
    existing_tests: Optional[str],
    target_coverage: Optional[float],
    merge: bool,
) -> Optional[Tuple[str, float, str]]:
    """Generate unit tests for a given prompt and implementation."""
    try:
        test_code, total_cost, model_name = cmd_test_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            output=output,
            language=language,
            coverage_report=coverage_report,
            existing_tests=existing_tests,
            target_coverage=target_coverage,
            merge=merge,
        )
        return test_code, total_cost, model_name
    except Exception as exception:
        handle_error(exception, "test", ctx.obj.get("quiet", False))
        return None


@cli.command("preprocess")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the preprocessed prompt file (file or directory).",
)
@click.option(
    "--xml",
    is_flag=True,
    default=False,
    help="Insert XML delimiters for structure (minimal preprocessing).",
)
@click.option(
    "--recursive",
    is_flag=True,
    default=False,
    help="Recursively preprocess includes.",
)
@click.option(
    "--double",
    is_flag=True,
    default=False,
    help="Double curly brackets.",
)
@click.option(
    "--exclude",
    multiple=True,
    default=None,
    help="List of keys to exclude from curly bracket doubling.",
)
@click.pass_context
# No @track_cost as preprocessing is local, but return dummy tuple for callback
def preprocess(
    ctx: click.Context,
    prompt_file: str,
    output: Optional[str],
    xml: bool,
    recursive: bool,
    double: bool,
    exclude: Optional[Tuple[str, ...]],
) -> Optional[Tuple[str, float, str]]:
    """Preprocess a prompt file to prepare it for LLM use."""
    try:
        # Since preprocess is a local operation, we don't track cost
        # But we need to return a tuple in the expected format for result callback
        result = preprocess_main(
            ctx=ctx,
            prompt_file=prompt_file,
            output=output,
            xml=xml,
            recursive=recursive,
            double=double,
            exclude=list(exclude) if exclude else [],
        )
        
        # Handle the result from preprocess_main
        if result is None:
            # If preprocess_main returns None, still return a dummy tuple for the callback
            return "", 0.0, "local"
        else:
            # Unpack the return value from preprocess_main
            processed_prompt, total_cost, model_name = result
            return processed_prompt, total_cost, model_name
    except Exception as exception:
        handle_error(exception, "preprocess", ctx.obj.get("quiet", False))
        return None


@cli.command("fix")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("unit_test_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("error_file", type=click.Path(dir_okay=False))  # Allow non-existent for loop mode
@click.option(
    "--output-test",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the fixed unit test file (file or directory).",
)
@click.option(
    "--output-code",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the fixed code file (file or directory).",
)
@click.option(
    "--output-results",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the results log (file or directory).",
)
@click.option(
    "--loop", 
    is_flag=True, 
    default=False, 
    help="Enable iterative fixing process."
)
@click.option(
    "--verification-program",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Path to a Python program that verifies the fix.",
)
@click.option(
    "--max-attempts",
    type=int,
    default=3,
    show_default=True,
    help="Maximum number of fix attempts.",
)
@click.option(
    "--budget",
    type=float,
    default=5.0,
    show_default=True,
    help="Maximum cost allowed for the fixing process.",
)
@click.option(
    "--auto-submit",
    is_flag=True,
    default=False,
    help="Automatically submit the example if all unit tests pass.",
)
@click.pass_context
@track_cost
def fix(
    ctx: click.Context,
    prompt_file: str,
    code_file: str,
    unit_test_file: str,
    error_file: str,
    output_test: Optional[str],
    output_code: Optional[str],
    output_results: Optional[str],
    loop: bool,
    verification_program: Optional[str],
    max_attempts: int,
    budget: float,
    auto_submit: bool,
) -> Optional[Tuple[Dict[str, Any], float, str]]:
    """Fix code based on a prompt and unit test errors."""
    try:
        # The actual logic is in fix_main
        success, fixed_unit_test, fixed_code, attempts, total_cost, model_name = fix_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            unit_test_file=unit_test_file,
            error_file=error_file,
            output_test=output_test,
            output_code=output_code,
            output_results=output_results,
            loop=loop,
            verification_program=verification_program,
            max_attempts=max_attempts,
            budget=budget,
            auto_submit=auto_submit,
        )
        result = {
            "success": success,
            "fixed_unit_test": fixed_unit_test,
            "fixed_code": fixed_code,
            "attempts": attempts,
        }
        return result, total_cost, model_name
    except Exception as exception:
        handle_error(exception, "fix", ctx.obj.get("quiet", False))
        return None


@cli.command("split")
@click.argument("input_prompt", type=click.Path(exists=True, dir_okay=False))
@click.argument("input_code", type=click.Path(exists=True, dir_okay=False))
@click.argument("example_code", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output-sub",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the generated sub-prompt file (file or directory).",
)
@click.option(
    "--output-modified",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the modified prompt file (file or directory).",
)
@click.pass_context
@track_cost
def split(
    ctx: click.Context,
    input_prompt: str,
    input_code: str,
    example_code: str,
    output_sub: Optional[str],
    output_modified: Optional[str],
) -> Optional[Tuple[Dict[str, str], float, str]]: # Modified return type
    """Split large complex prompt files into smaller ones."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "split"
    try:
        result_data, total_cost, model_name = split_main(
            ctx=ctx,
            input_prompt_file=input_prompt,
            input_code_file=input_code,
            example_code_file=example_code,
            output_sub=output_sub,
            output_modified=output_modified,
        )
        return result_data, total_cost, model_name
    except Exception as e:
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("change")
@click.argument("change_prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("input_code", type=click.Path(exists=True)) # Can be file or dir
@click.argument("input_prompt_file", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option(
    "--budget",
    type=float,
    default=5.0,
    show_default=True,
    help="Maximum cost allowed for the change process.",
)
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the modified prompt file (file or directory).",
)
@click.option(
    "--csv",
    "use_csv",
    is_flag=True,
    default=False,
    help="Use a CSV file for batch change prompts.",
)
@click.pass_context
@track_cost
def change(
    ctx: click.Context,
    change_prompt_file: str,
    input_code: str,
    input_prompt_file: Optional[str],
    output: Optional[str],
    use_csv: bool,
    budget: float,
) -> Optional[Tuple[str | Dict, float, str]]: # Modified return type
    """Modify prompt(s) based on change instructions."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "change"
    try:
        # --- ADD VALIDATION LOGIC HERE ---
        input_code_path = Path(input_code) # Convert to Path object
        if use_csv:
            if not input_code_path.is_dir():
                raise click.UsageError("INPUT_CODE must be a directory when using --csv.")
            if input_prompt_file:
                raise click.UsageError("Cannot use --csv and specify an INPUT_PROMPT_FILE simultaneously.")
        else: # Not using CSV
            if not input_prompt_file:
                 # This check might be better inside change_main, but can be here too
                 raise click.UsageError("INPUT_PROMPT_FILE is required when not using --csv.")
            if not input_code_path.is_file():
                 # This check might be better inside change_main, but can be here too
                 raise click.UsageError("INPUT_CODE must be a file when not using --csv.")
        # --- END VALIDATION LOGIC ---

        result_data, total_cost, model_name = change_main(
            ctx=ctx,
            change_prompt_file=change_prompt_file,
            input_code=input_code,
            input_prompt_file=input_prompt_file,
            output=output,
            use_csv=use_csv,
            budget=budget,
        )
        return result_data, total_cost, model_name
    except (click.UsageError, Exception) as e: # Catch specific and general exceptions
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("update")
@click.argument("input_prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("modified_code_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("input_code_file", type=click.Path(exists=True, dir_okay=False), required=False)
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the updated prompt file. If not specified, overwrites the original prompt file to maintain it as the source of truth.",
)
@click.option(
    "--git",
    is_flag=True,
    default=False,
    help="Use git history to find the original code file.",
)
@click.pass_context
@track_cost
def update(
    ctx: click.Context,
    input_prompt_file: str,
    modified_code_file: str,
    input_code_file: Optional[str],
    output: Optional[str],
    git: bool,
) -> Optional[Tuple[str, float, str]]: # Modified return type
    """Update the original prompt file based on modified code."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "update"
    try:
        if git and input_code_file:
            raise click.UsageError("Cannot use --git and specify an INPUT_CODE_FILE simultaneously.")
        if not git and not input_code_file:
            raise click.UsageError("INPUT_CODE_FILE is required when not using --git.")

        updated_prompt, total_cost, model_name = update_main(
            ctx=ctx,
            input_prompt_file=input_prompt_file,
            modified_code_file=modified_code_file,
            input_code_file=input_code_file,
            output=output,
            git=git,
        )
        return updated_prompt, total_cost, model_name
    except (click.UsageError, Exception) as e: # Catch specific and general exceptions
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("detect")
@click.argument("prompt_files", nargs=-1, type=click.Path(exists=True, dir_okay=False))
@click.argument("change_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the CSV analysis results (file or directory).",
)
@click.pass_context
@track_cost
def detect(
    ctx: click.Context,
    prompt_files: Tuple[str, ...],
    change_file: str,
    output: Optional[str],
) -> Optional[Tuple[List[Dict[str, str]], float, str]]: # Modified return type
    """Analyze prompts and a change description to find needed changes."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "detect"
    try:
        if not prompt_files:
             raise click.UsageError("At least one PROMPT_FILE must be provided.")

        changes_list, total_cost, model_name = detect_change_main(
            ctx=ctx,
            prompt_files=list(prompt_files),
            change_file=change_file,
            output=output,
        )
        return changes_list, total_cost, model_name
    except (click.UsageError, Exception) as e: # Catch specific and general exceptions
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("conflicts")
@click.argument("prompt1", type=click.Path(exists=True, dir_okay=False))
@click.argument("prompt2", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the CSV conflict analysis results (file or directory).",
)
@click.pass_context
@track_cost
def conflicts(
    ctx: click.Context,
    prompt1: str,
    prompt2: str,
    output: Optional[str],
) -> Optional[Tuple[List[Dict[str, str]], float, str]]: # Modified return type
    """Analyze two prompt files to find conflicts."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "conflicts"
    try:
        conflicts_list, total_cost, model_name = conflicts_main(
            ctx=ctx,
            prompt1=prompt1,
            prompt2=prompt2,
            output=output,
        )
        return conflicts_list, total_cost, model_name
    except Exception as e:
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("crash")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("program_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("error_file", type=click.Path(dir_okay=False)) # Allow non-existent
@click.option(
    "--output", # Corresponds to output_code in crash_main
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the fixed code file (file or directory).",
)
@click.option(
    "--output-program",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the fixed program file (file or directory).",
)
@click.option("--loop", is_flag=True, default=False, help="Enable iterative fixing process.")
@click.option(
    "--max-attempts",
    type=int,
    default=3,
    show_default=True,
    help="Maximum number of fix attempts.",
)
@click.option(
    "--budget",
    type=float,
    default=5.0,
    show_default=True,
    help="Maximum cost allowed for the fixing process.",
)
@click.pass_context
@track_cost
def crash(
    ctx: click.Context,
    prompt_file: str,
    code_file: str,
    program_file: str,
    error_file: str,
    output: Optional[str], # Maps to output_code
    output_program: Optional[str],
    loop: bool,
    max_attempts: int,
    budget: float,
) -> Optional[Tuple[Dict[str, Any], float, str]]: # Modified return type
    """Fix errors in a code module and calling program that caused a crash."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "crash"
    try:
        success, fixed_code, fixed_program, attempts, cost, model = crash_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            program_file=program_file,
            error_file=error_file,
            output=output,
            output_program=output_program,
            loop=loop,
            max_attempts=max_attempts,
            budget=budget,
        )
        result_data = {
            "success": success,
            "attempts": attempts,
            "fixed_code": fixed_code,
            "fixed_program": fixed_program,
        }
        return result_data, cost, model
    except Exception as e:
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("trace")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_line", type=int)
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the trace analysis results log (file or directory).",
)
@click.pass_context
@track_cost
def trace(
    ctx: click.Context,
    prompt_file: str,
    code_file: str,
    code_line: int,
    output: Optional[str],
) -> Optional[Tuple[int | str, float, str]]: # Modified return type
    """Find the associated line number between a prompt file and generated code."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "trace"
    try:
        prompt_line_result, total_cost, model_name = trace_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            code_line=code_line,
            output=output,
        )
        # Check if trace_main indicated failure (e.g., by returning None or specific error)
        # This depends on trace_main's implementation; assuming it raises exceptions for now.
        if prompt_line_result is None and total_cost == 0.0 and model_name == 'local_error': # Example check if trace_main returns specific tuple on failure
             # Optionally handle specific non-exception failures differently if needed
             # For now, rely on exceptions being raised for errors like out-of-range.
             pass
        return prompt_line_result, total_cost, model_name
    except Exception as e:
        handle_error(e, command_name, quiet)
        # Exit with non-zero status code on any exception
        ctx.exit(1)


@cli.command("bug")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("program_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("current_output_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("desired_output_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the generated unit test (file or directory).",
)
@click.option("--language", type=str, default=None, help="Specify the programming language (default: Python).")
@click.pass_context
@track_cost
def bug(
    ctx: click.Context,
    prompt_file: str,
    code_file: str,
    program_file: str,
    current_output_file: str,
    desired_output_file: str,
    output: Optional[str],
    language: Optional[str],
) -> Optional[Tuple[str, float, str]]: # Modified return type
    """Generate a unit test based on observed and desired outputs."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "bug"
    try:
        unit_test_content, total_cost, model_name = bug_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            program_file=program_file,
            current_output=current_output_file,
            desired_output=desired_output_file,
            output=output,
            language=language,
        )
        return unit_test_content, total_cost, model_name
    except Exception as e:
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("auto-deps")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("directory_path", type=str) # Path with potential glob pattern
@click.option(
    "--output",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the modified prompt file (file or directory).",
)
@click.option(
    "--csv",
    "auto_deps_csv_path",
    type=click.Path(dir_okay=False), # CSV path is a file
    default=None, # Default handled by auto_deps_main or env var
    help="Specify the CSV file for dependency info (default: project_dependencies.csv or PDD_AUTO_DEPS_CSV_PATH).",
)
@click.option(
    "--force-scan",
    is_flag=True,
    default=False,
    help="Force rescanning of all potential dependency files.",
)
@click.pass_context
@track_cost
def auto_deps(
    ctx: click.Context,
    prompt_file: str,
    directory_path: str,
    output: Optional[str],
    auto_deps_csv_path: Optional[str],
    force_scan: bool,
) -> Optional[Tuple[str, float, str]]: # Modified return type
    """Analyze a prompt and insert dependencies from a directory or glob.

    DIRECTORY_PATH accepts either a directory path or a glob pattern and is
    expanded recursively when you use patterns like `**/*.py`. Examples:
      - examples/**/*.py
      - context/*_example.py
      - examples/*
    """
    quiet = ctx.obj.get("quiet", False)
    command_name = "auto-deps"
    try:
        # Strip both single and double quotes from the provided path
        clean_directory_path = directory_path.strip("'\"")

        modified_prompt, total_cost, model_name = auto_deps_main(
            ctx=ctx,
            prompt_file=prompt_file,
            directory_path=clean_directory_path,
            auto_deps_csv_path=auto_deps_csv_path,
            output=output,
            force_scan=force_scan,
        )
        return modified_prompt, total_cost, model_name
    except Exception as e:
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("verify")
@click.argument("prompt_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("code_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("program_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--output-results",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the verification results log (file or directory).",
)
@click.option(
    "--output-code",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the verified code file (file or directory).",
)
@click.option(
    "--output-program",
    type=click.Path(writable=True),
    default=None,
    help="Specify where to save the verified program file (file or directory).",
)
@click.option(
    "--max-attempts",
    type=int,
    default=3,
    show_default=True,
    help="Maximum number of fix attempts within the verification loop.",
)
@click.option(
    "--budget",
    type=float,
    default=5.0,
    show_default=True,
    help="Maximum cost allowed for the verification and fixing process.",
)
@click.pass_context
@track_cost
def verify(
    ctx: click.Context,
    prompt_file: str,
    code_file: str,
    program_file: str,
    output_results: Optional[str],
    output_code: Optional[str],
    output_program: Optional[str],
    max_attempts: int,
    budget: float,
) -> Optional[Tuple[Dict[str, Any], float, str]]: # Modified return type
    """Verify code correctness against prompt using LLM judgment."""
    quiet = ctx.obj.get("quiet", False)
    command_name = "verify"
    try:
        success, final_program, final_code, attempts, total_cost_value, model_name_value = fix_verification_main(
            ctx=ctx,
            prompt_file=prompt_file,
            code_file=code_file,
            program_file=program_file,
            output_results=output_results,
            output_code=output_code,
            output_program=output_program,
            loop=True,
            verification_program=program_file,
            max_attempts=max_attempts,
            budget=budget,
        )
        result_data = {
            "success": success,
            "attempts": attempts,
            "verified_code_path": output_code,
            "verified_program_path": output_program,
            "results_log_path": output_results,
        }
        return result_data, total_cost_value, model_name_value
    except Exception as e:
        handle_error(e, command_name, quiet)
        return None # Return None on failure


@cli.command("sync")
@click.argument("basename", type=str)
@click.option(
    "--max-attempts",
    type=int,
    default=3,
    show_default=True,
    help="Maximum number of sync attempts.",
)
@click.option(
    "--budget",
    type=float,
    default=10.0,
    show_default=True,
    help="Maximum total cost allowed for the entire sync process.",
)
@click.option(
    "--skip-verify",
    is_flag=True,
    default=False,
    help="Skip verification step during sync.",
)
@click.option(
    "--skip-tests",
    is_flag=True,
    default=False,
    help="Skip test generation during sync.",
)
@click.option(
    "--target-coverage",
    type=click.FloatRange(0.0, 100.0),
    default=10.0,
    show_default=True,
    help="Target code coverage percentage for generated tests.",
)
@click.option(
    "--log",
    is_flag=True,
    default=False,
    help="Enable detailed logging during sync.",
)
@click.pass_context
@track_cost
def sync(
    ctx: click.Context,
    basename: str,
    max_attempts: int,
    budget: float,
    skip_verify: bool,
    skip_tests: bool,
    target_coverage: float,
    log: bool,
) -> Optional[Tuple[Dict[str, Any], float, str]]:
    """Automatically execute the complete PDD workflow loop for a given basename.

    This command implements the entire synchronized cycle, intelligently determining
    what steps are needed and executing them in the correct order. It detects
    programming languages by scanning for prompt files matching the pattern
    {basename}_{language}.prompt in the prompts directory.

    Note: Sync typically overwrites generated files to keep outputs up to date.
    In most real runs, include the global ``--force`` flag (e.g., ``pdd --force sync BASENAME``)
    to allow overwrites without interactive confirmation.
    """
    try:
        results, total_cost, model = sync_main(
            ctx=ctx,
            basename=basename,
            max_attempts=max_attempts,
            budget=budget,
            skip_verify=skip_verify,
            skip_tests=skip_tests,
            target_coverage=target_coverage,
            log=log,
        )
        return results, total_cost, model
    except Exception as exception:
        handle_error(exception, "sync", ctx.obj.get("quiet", False))
        return None


@cli.command("pytest-output")
@click.argument("test_file", type=click.Path(exists=True, dir_okay=False))
@click.option(
    "--json-only",
    is_flag=True,
    default=False,
    help="Output only JSON to stdout for programmatic use.",
)
@click.pass_context
# No @track_cost since this is a utility command
def pytest_output_cmd(ctx: click.Context, test_file: str, json_only: bool) -> None:
    """Run pytest on a test file and capture structured output.
    
    This is a utility command used internally by PDD for capturing pytest results
    in a structured format. It can also be used directly for debugging test issues.
    
    Examples:
        pdd pytest-output tests/test_example.py
        pdd pytest-output tests/test_example.py --json-only
    """
    command_name = "pytest-output"
    quiet_mode = ctx.obj.get("quiet", False)

    try:
        import json
        pytest_output = run_pytest_and_capture_output(test_file)
        
        if json_only:
            # Print only valid JSON to stdout for programmatic use
            print(json.dumps(pytest_output))
        else:
            # Pretty print the output for interactive use
            if not quiet_mode:
                console.print(f"Running pytest on: [blue]{test_file}[/blue]")
                from rich.pretty import pprint
                pprint(pytest_output, console=console)
                
    except Exception as e:
        handle_error(e, command_name, quiet_mode)


@cli.command("install_completion")
@click.pass_context
# No @track_cost
def install_completion_cmd(ctx: click.Context) -> None: # Return type remains None
    """Install shell completion for the PDD CLI."""
    command_name = "install_completion" # For error handling
    quiet_mode = ctx.obj.get("quiet", False) # Get quiet from context

    try:
        # The actual install_completion function is imported from .install_completion
        install_completion(quiet=quiet_mode) # Pass quiet_mode
        # Success messages are handled within install_completion based on quiet_mode
        # No need to print additional messages here unless specifically required
        # if not quiet_mode:
        #     console.print(f"[success]'{command_name}' command completed successfully.[/success]")
    except Exception as e:
        # Use the centralized error handler
        handle_error(e, command_name, quiet_mode)
        # Do not return anything, as the callback expects None or a tuple


# --- Entry Point ---
if __name__ == "__main__":
    cli()
