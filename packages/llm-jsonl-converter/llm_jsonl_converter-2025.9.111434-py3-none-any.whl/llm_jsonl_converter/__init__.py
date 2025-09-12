import re
import json
from typing import List, Dict, Any

from langchain_llm7 import ChatLLM7
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from llm_formats import get_llm_jsonl_formats
from llmatch_messages import llmatch
from tqdm.auto import tqdm

def generate_jsonl_from_text(
    text: str,
    *,
    target_format_name: str,
    llm: BaseChatModel | None = None,
    chunk_word_size: int = 1000,
    verbose: bool = False,
) -> str:
    """
    Convert unstructured `text` into JSONL using an LLM, one line per chunk.

    Splits text into word-based chunks, prompts an LLM to produce a JSON object
    for each chunk in a specified JSONL format, validates the output, and
    accumulates valid lines into a JSONL string. Includes a progress bar and
    handles per-chunk errors gracefully.

    Args:
        text: The large unstructured text to convert.
        target_format_name: The name of the target JSONL format to use.
        llm: An optional LLM instance. If None, a default ChatLLM7 instance is used.
        chunk_word_size: The number of words per chunk. Defaults to 1000.
        verbose: If True, prints detailed progress and error messages.

    Returns:
        A JSONL string containing only valid, parsed, and validated JSON lines.

    Raises:
        ValueError: If the target_format_name is not found in get_llm_jsonl_formats().
    """
    if llm is None:
        llm = ChatLLM7(model="gemini-2.5-flash-lite", base_url="https://api.llm7.io/v1")

    formats = get_llm_jsonl_formats()
    target_format = next((f for f in formats if f["name"] == target_format_name), None)
    if target_format is None:
        raise ValueError(f"Target format '{target_format_name}' not found.")

    line_regex_str = target_format["line_regex"]
    target_pattern = re.compile(line_regex_str, re.DOTALL)
    example_json = json.dumps(target_format["example"], indent=2)

    words = re.findall(r"\S+", text)
    chunks = [
        " ".join(words[i:i + chunk_word_size])
        for i in range(0, len(words), chunk_word_size)
        if words[i:i + chunk_word_size]
    ]

    system_message_content = (
        "You are a precise data generator. "
        "Output **exactly one** JSON object wrapped **only** in `<jsonl_line>...</jsonl_line>` tags. "
        "The JSON must conform to the target format named `{target_format_name}` whose fields and structure match the provided description. "
        "Do not include explanations, comments, extra keys, or additional text outside the tags. "
        "Use only information from the provided chunk. If insufficient, produce the minimal valid object consistent with the format. "
        "All strings must be valid JSON strings (escape quotes, backslashes, newlines)."
    )

    pattern = r"<jsonl_line>\s*(\{[\s\S]*?\})\s*</jsonl_line>"
    valid_lines: List[str] = []
    total_chunks = len(chunks)
    skipped_count = 0

    with tqdm(total=total_chunks, desc="Generating JSONL", unit="chunk") as pbar:
        for i, chunk_text in enumerate(chunks):
            try:
                human_message_content = [
                    {"type": "text", "text": f"Target format name: {target_format_name}\n"},
                    {"type": "text", "text": f"Conform to this regex (anchors included): {line_regex_str}\n"},
                    {"type": "text", "text": f"Example JSON (for shape only, content will differ):\n{example_json}\n\n"},
                    {"type": "text", "text": f"Chunk: >>>{chunk_text}<<<"}
                ]

                response = llmatch(
                    llm=llm,
                    messages=[SystemMessage(content=system_message_content.format(target_format_name=target_format_name)),
                              HumanMessage(content=human_message_content)],
                    pattern=pattern,
                    verbose=verbose,
                )

                if not response["success"]:
                    if verbose:
                        tqdm.write(f"[skip] chunk {i}: LLM extraction failed.")
                    skipped_count += 1
                    pbar.update(1)
                    continue

                raw_json_str = response["extracted_data"][0]
                try:
                    parsed_json = json.loads(raw_json_str)
                    # Re-serialize to ensure consistent formatting and escape characters
                    normalized_line = json.dumps(parsed_json, ensure_ascii=False)
                except json.JSONDecodeError:
                    if verbose:
                        tqdm.write(f"[skip] chunk {i}: LLM output is not valid JSON.")
                    skipped_count += 1
                    pbar.update(1)
                    continue

                if target_pattern.fullmatch(normalized_line):
                    valid_lines.append(normalized_line)
                else:
                    if verbose:
                        tqdm.write(f"[skip] chunk {i}: JSON line did not match regex.")
                    skipped_count += 1

            except Exception as e:
                if verbose:
                    tqdm.write(f"[skip] chunk {i}: Error processing chunk - {e}")
                skipped_count += 1
            finally:
                pbar.update(1)
                pbar.set_postfix({"ok": len(valid_lines), "skipped": skipped_count})

    return "\n".join(valid_lines) + "\n"