import re
from ast import literal_eval
from typing import Any
import json

def clean_agent_json(data):
    """Clean and normalize nested JSON responses (dedupe lists, handle dicts)"""
    if isinstance(data, dict):
        return {k: clean_agent_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        seen = set()
        cleaned_list = []
        for item in data:
            key = json.dumps(clean_agent_json(item), sort_keys=True) if isinstance(item, dict) else str(item)
            if key not in seen:
                seen.add(key)
                cleaned_list.append(clean_agent_json(item))
        return cleaned_list
    else:
        return data


def _find_first_balanced_chunk(s: str) -> str | None:
    """
    Find the first balanced JSON-like chunk starting at first '{' or '['.
    Returns the substring (including outer braces) or None if not found.
    """
    start_idx = None
    start_char = None
    for i, ch in enumerate(s):
        if ch in ('{', '['):
            start_idx = i
            start_char = ch
            break
    if start_idx is None:
        return None

    pairs = {'{': '}', '[': ']'}
    open_ch = start_char
    close_ch = pairs[open_ch]
    stack = []
    for i in range(start_idx, len(s)):
        ch = s[i]
        if ch == open_ch:
            stack.append(ch)
        elif ch == close_ch:
            stack.pop()
            if not stack:
                return s[start_idx:i+1]
    return None


def _strip_code_fence(s: str) -> str:
    # Remove triple backtick fences and leading "```json"
    s = re.sub(r"```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _remove_trailing_commas(s: str) -> str:
    # Remove trailing commas in objects/arrays (basic)
    s = re.sub(r",\s*([\]}])", r"\1", s)
    return s


def _json_to_python_literals(s: str) -> str:
    # convert json true/false/null to python True/False/None (for ast.literal_eval fallback)
    s = re.sub(r'\btrue\b', 'True', s, flags=re.IGNORECASE)
    s = re.sub(r'\bfalse\b', 'False', s, flags=re.IGNORECASE)
    s = re.sub(r'\bnull\b', 'None', s, flags=re.IGNORECASE)
    return s

def _replace_single_quotes_with_double(s: str) -> str:
    """
    Attempt to convert simple single-quoted JSON-like syntax to double-quoted valid JSON.
    NOTE: This is conservative and may not fix all pathological cases.
    """
    # Replace single-quoted keys/values with double quotes when safe-ish:
    # This matches single quotes that wrap a sequence without internal unescaped single-quotes.
    s = re.sub(r"(?<=[:\s,\{\[])\s*'([^'\\]*(?:\\.[^'\\]*)*)'\s*(?=[,\}\]\s])", r'"\1"', s)
    # Also convert leading single-quoted keys:  'key':  -> "key":
    s = re.sub(r"'\s*([^'\\]+?)\s*'\s*:", r'"\1":', s)
    return s
def parse_model_response_to_dict(text: str) -> Any:
    """
    Parse a model's text response and return the parsed JSON as Python objects (dict/list).
    Raises ValueError on failure with a helpful message.

    Example:
      obj = parse_model_response_to_dict(model_response_str)
    """
    if not isinstance(text, str):
        raise ValueError("input must be a string")

    original = text.strip()

    # 1) Remove surrounding markdown fences if present
    cleaned = _strip_code_fence(original)

    # 2) Extract first balanced JSON-ish chunk (handles nested objects)
    chunk = _find_first_balanced_chunk(cleaned)
    if chunk is None:
        # maybe the entire cleaned string is JSON-like but without brackets (unlikely)
        # fallback to using whole cleaned text
        chunk = cleaned

    # Try parsing attempts in order, progressively more forgiving:
    attempts = []

    # Attempt 1: direct json.loads
    try:
        return json.loads(chunk)
    except Exception as e:
        attempts.append(("json.loads", str(e)))

    # Attempt 2: remove trailing commas then json.loads
    try:
        chunk2 = _remove_trailing_commas(chunk)
        return json.loads(chunk2)
    except Exception as e:
        attempts.append(("json.loads-after-trailing-commas", str(e)))

    # Attempt 3: try converting single quotes -> double quotes heuristically and json.loads
    try:
        chunk3 = _replace_single_quotes_with_double(chunk)
        chunk3 = _remove_trailing_commas(chunk3)
        return json.loads(chunk3)
    except Exception as e:
        attempts.append(("heuristic-single->double then json.loads", str(e)))

    # Attempt 4: try ast.literal_eval on pythonized literal (true/false/null -> True/False/None)
    try:
        py_like = _json_to_python_literals(chunk)
        obj = literal_eval(py_like)
        return obj
    except Exception as e:
        attempts.append(("ast.literal_eval", str(e)))

    # Attempt 5: apply single->double then ast.literal_eval
    try:
        step = _replace_single_quotes_with_double(chunk)
        step = _json_to_python_literals(step)
        obj = literal_eval(step)
        return obj
    except Exception as e:
        attempts.append(("single->double + ast.literal_eval", str(e)))

    # If we got here, all attempts failed — return helpful error
    msg_lines = ["Failed to parse model response into JSON. Attempts:"]
    for name, err in attempts:
        msg_lines.append(f"- {name}: {err}")
    msg_lines.append("\nOriginal text (truncated to 2000 chars):")
    msg_lines.append(original[:2000])
    raise ValueError("\n".join(msg_lines))