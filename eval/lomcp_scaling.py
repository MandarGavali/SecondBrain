"""P2 scaling experiment: LO-MCP tool selection against a simulated 40-tool registry.

The real server exposes only 4-6 tools, so the token saving there is small. This script
builds 40 distinct dummy tools (the 4 real ones + 36 plausible extras), predicts tools for
each probe query and reports schema tokens (full vs selected) and precision/recall against
the expected tool.

Usage:  python -m eval.lomcp_scaling [out.csv]
Needs GOOGLE_API_KEY (embeddings only, no generation calls).
"""
import csv
import sys

from dotenv import load_dotenv
load_dotenv()

from langchain_core.tools import StructuredTool

from secondbrain.agent.tools import get_tools
from secondbrain.lomcp.predictor import ToolIndex

EXTRA_TOOLS = {
    "create_calendar_event": "Create a calendar event with a title, date, time and attendees.",
    "list_calendar_events": "List upcoming calendar events in a date range.",
    "send_email": "Send an email to one or more recipients with a subject and body.",
    "search_email": "Search the user's mailbox for messages matching a query.",
    "create_task": "Add a task to the user's to-do list with an optional due date.",
    "complete_task": "Mark a to-do task as completed.",
    "list_tasks": "List open tasks from the to-do list.",
    "get_weather": "Get the current weather and forecast for a city.",
    "convert_currency": "Convert an amount between two currencies using live rates.",
    "translate_text": "Translate text into another language.",
    "web_search": "Search the public web for recent information.",
    "fetch_url": "Download the text content of a web page by URL.",
    "run_python": "Execute a short Python snippet and return the output.",
    "plot_chart": "Draw a bar or line chart from a list of numbers.",
    "create_note": "Create a new note in the user's notebook.",
    "append_note": "Append text to an existing note.",
    "delete_note": "Delete a note from the notebook.",
    "tag_document": "Attach tags or labels to an uploaded document.",
    "delete_document": "Remove an uploaded document from the knowledge base.",
    "rename_document": "Rename an uploaded document.",
    "extract_tables": "Extract tables from a PDF document as rows and columns.",
    "ocr_image": "Read text from an image using OCR.",
    "set_reminder": "Set a reminder that fires at a given time.",
    "get_stock_price": "Get the latest stock price for a ticker symbol.",
    "create_flashcards": "Turn notes into spaced-repetition flashcards.",
    "schedule_study_session": "Plan a study session for a topic on the calendar.",
    "export_pdf": "Export a note or answer as a PDF file.",
    "share_link": "Create a shareable link for a document.",
    "word_count": "Count words and characters in a text.",
    "define_word": "Look up the dictionary definition of a word.",
    "math_solver": "Solve an arithmetic or algebra problem step by step.",
    "unit_convert": "Convert between units such as km and miles.",
    "timezone_convert": "Convert a time between time zones.",
    "github_issues": "List open issues in a GitHub repository.",
    "slack_post": "Post a message to a Slack channel.",
    "spotify_play": "Play a song or playlist on Spotify.",
}

# (query, expected tool) -- expected tool must be among the 40
PROBES = [
    ("what does my document say about the leave policy", "search_documents"),
    ("which files have I uploaded so far", "list_documents"),
    ("give me a short summary of the report", "summarize_documents"),
    ("make interview questions from my notes", "generate_questions"),
    ("book a meeting with Rahul tomorrow at 3pm", "create_calendar_event"),
    ("email the summary to my professor", "send_email"),
    ("what's the weather in Pune", "get_weather"),
    ("remind me to submit the assignment at 6", "set_reminder"),
    ("pull the tables out of this pdf", "extract_tables"),
    ("delete the old syllabus document", "delete_document"),
    ("convert 100 dollars to rupees", "convert_currency"),
    ("turn chapter 3 into flashcards", "create_flashcards"),
]


def _tool(name, desc):
    return StructuredTool.from_function(func=lambda query="": "", name=name, description=desc)


def main(out_path=None):
    tools = list(get_tools()) + [_tool(n, d) for n, d in EXTRA_TOOLS.items()]
    assert len({t.name for t in tools}) == len(tools) == 40, len(tools)
    index = ToolIndex(tools)

    rows, hits, sel_total, full_total, precisions = [], 0, 0, 0, []
    for query, expected in PROBES:
        info = index.predict(query)
        names = info["names"]
        hit = expected in names
        hits += hit
        precisions.append((1 / len(names)) if hit else 0.0)
        sel_total += info["tokens_selected"]
        full_total += info["tokens_full"]
        rows.append([query, expected, "|".join(names), hit, info["tokens_full"], info["tokens_selected"]])
        print(f"{'OK ' if hit else 'MISS'} {expected:24s} -> {names}")

    n = len(PROBES)
    print(f"\nrecall@selected = {hits / n:.2f}   mean precision = {sum(precisions) / n:.2f}")
    print(f"schema tokens: full={full_total // n}/query  selected={sel_total // n}/query  "
          f"saving={1 - sel_total / full_total:.0%}")

    if out_path:
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["query", "expected", "selected", "hit", "tokens_full", "tokens_selected"])
            w.writerows(rows)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
