#!/usr/bin/env python3
import argparse
from pathlib import Path
from rich.console import Console
from rich.markdown import Markdown

GREEN = "\033[92m"
RESET = "\033[0m"
console = Console()


def strip_markdown(md: str) -> str:
    """Strip rich Markdown into plain text (for voice)."""
    from io import StringIO
    from rich.console import Console as StrippedConsole
    from rich.text import Text

    sio = StringIO()
    stripped_console = StrippedConsole(file=sio, force_terminal=False, color_system=None)
    stripped_console.print(Markdown(md))
    return Text.from_markup(sio.getvalue()).plain


def _main(Elf):
    parser = argparse.ArgumentParser(description=f"{Elf.__name__} CLI Interface")
    parser.add_argument("message", type=str, help="Your message to the AI")
    parser.add_argument("--empty", action="store_true", help="Start a new conversation")
    parser.add_argument("--purge", action="store_true", help="Purge long-term memory")
    parser.add_argument("--secret", action="store_true", help="Do not save this message in history")
    parser.add_argument("--model", type=str, help="Model to use (default: gpt-5-mini)")

    parser.add_argument("--md", action="store_true", help="Render output with markdown (non-streaming)")
    parser.add_argument("--raw", action="store_true", help="Stream output (default)")

    # tools
    parser.add_argument("--search", action="store_true", help="Perform web search to enrich context")
    parser.add_argument("--deep", action="store_true", help="Deep dive into the top search result")
    parser.add_argument("--shell", action="store_true", help="Write and run a shell command")
    parser.add_argument("--python", action="store_true", help="Write and run Python code")
    parser.add_argument("--install-project", action="store_true", help="Install a Python project into the elf's venv")


    # memory recall
    parser.add_argument(
        "--recall",
        nargs="+",
        help="Recall last N coding adventures, optionally filter by mode (python/shell)."
    )
    parser.add_argument("--long-term", type=int, help="Recall N best matches from long-term memory")

    # other options
    parser.add_argument("--summarize", action="store_true", help="Summarize the output of a shell command")
    parser.add_argument("--voice", action="store_true", help="Speak the response aloud")

    # archive (RAG)
    # rag (archive replacement)
    parser.add_argument("--rag", nargs="+",
                        help="RAG ops: crawl/find/delete/list/overwrite/status/enhance")
    parser.add_argument("--dir", type=Path, help="Directory filter for RAG")
    parser.add_argument("--recursive", action="store_true", help="Recurse into subdirectories when crawling")
    parser.add_argument("--include", action="append", help="Glob(s) to include (repeatable)")
    parser.add_argument("--exclude", action="append", help="Glob(s) to exclude (repeatable)")

    args = parser.parse_args()

    # inside _main, after parsing args:
    invoked_tools = []

    if args.search:
        invoked_tools.append("WebSearch (deep)" if args.deep else "WebSearch")
    if args.rag:
        invoked_tools.append(f"RAG:{args.rag[0]}")
    if args.shell:
        invoked_tools.append("Shell")
    if args.python:
        invoked_tools.append("Python")

    print(f"{GREEN}\U0001f464 You: {args.message}{RESET}")
    elf = Elf(model=args.model or "gpt-5-mini")
    style = getattr(elf, "text_color", "cyan")

    # --- rag ---
    if args.rag:
        subcmd = args.rag[0]
        query = " ".join(args.rag[1:]) if len(args.rag) > 1 else args.message
        hits, msg = elf.handle_rag(
            subcmd, query, args.dir, recursive=args.recursive,
            includes=args.include, excludes=args.exclude
        )
        if msg:
            console.print(msg, style=style)
            if not args.secret:
                elf.memory.add_short("system", msg)

        if hits:
            console.print(f"📚 Injected {len(hits)} rag hits", style=style)
            if not args.secret:
                for h in hits:
                    elf.memory.add_short("system", f"RAG hit: {h}")

        # Only skip chat if NOT enhance
        if subcmd != "enhance":
            return

    # --- conversation control ---
    if args.empty:
        elf.reset_history()
    if args.purge:
        elf.purge_memory()
        console.print(f"\U0001f9f9 {Elf.__name__} forgets everything in the long-term...", style=style)

    # --- enrichments ---
    elf.enrich_with_memory(args.message)
    if args.search:
        elf.enrich_with_search(args.message, deep=args.deep)
        console.print(f"\U0001f50e {Elf.__name__} searches the websies…", style=style)

    if args.recall:
        n = int(args.recall[0])
        mode = args.recall[1] if len(args.recall) > 1 else None
        rows = elf.recall_adventures(n=n, mode=mode)
        memory_reflection = elf.format_recall(rows) if rows else None
    else:
        memory_reflection = None

    if memory_reflection:
        console.print(f"\U0001f4d3 {Elf.__name__} recalls:\n{memory_reflection}", style=style)

    # --- run tools ---
    if args.shell:
        command, result, success, summary = elf.run_shell_task(
            args.message,
            memory_reflection,
            summarize=args.summarize,
        )
        console.print(f"\U0001f9e0 {Elf.__name__} thinks:\n{command}", style=style)
        console.print(f"\U0001f4a5 {Elf.__name__} runs:\n{result}", style=style)
        if summary:
            console.print(f"\U0001f4dc Summary:\n{summary}", style=style)
            if args.voice:
                elf.tools.run("speak_text", summary)
        if not args.secret:
            elf.save_coding_adventure(args.message, command, result, "shell", success)
        return

    if args.python:
        code, result, success, summary = elf.run_python_task(args.message, memory_reflection, summarize=args.summarize)
        console.print(f"\U0001f9e0 {Elf.__name__} writes:\n{code}", style=style)
        console.print(f"\U0001f4a5 {Elf.__name__} executes:\n{result}", style=style)
        if summary:
            console.print(f"\U0001f4dc Summary:\n{summary}", style=style)
            if args.voice:
                elf.tools.run("speak_text", summary)
        if not args.secret:
            elf.save_coding_adventure(args.message, code, result, "python", success)
        return


    # --- chat (default path) ---
    try:
        if args.md:
            reply = elf.chat(args.message, stream=not args.md, invoked_tools=invoked_tools)
            console.print(Markdown(f"\U0001f9dd **{Elf.__name__}:** {reply}"), style=style)
            if args.voice:
                elf.tools.run("speak_text", strip_markdown(reply))
        else:
            stream = elf.chat(args.message, stream=True, invoked_tools=invoked_tools)
            console.print(f"\U0001f9dd {Elf.__name__}: ", style=style, end="")
            reply = ""
            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    reply += delta.content
                    console.print(delta.content, style=style, end="")
            print()
            if args.voice:
                elf.tools.run("speak_text", reply)

        if not args.secret:
            elf.history.append({"role": "assistant", "content": reply})
            elf.save_history()
            elf.remember(args.message, reply)

    except Exception as e:
        console.print(f"\n❌ Error: {e}", style="red")


def main_lobi():
    from lobi import Lobi
    _main(Lobi)


def main_judais():
    from judais import JudAIs
    _main(JudAIs)
