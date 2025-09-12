import re
import json
import inspect
from typing import List, Dict, Any

from langchain_llm7 import ChatLLM7
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage, HumanMessage
from llm_formats import get_llm_jsonl_formats
from llmatch_messages import llmatch
from tqdm.auto import tqdm

# --- Add near the top of your module ---
from typing import Dict

_FORMAT_HINTS: Dict[str, str] = {
    "Simple QA": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"question": <question>, "answer": <answer>}.'
    ),
    "OpenAI Prompt–Completion (SFT)": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"prompt": <question>, "completion": <answer>}'
    ),
    "OpenAI Chat Messages": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"messages":[{"role":"user","content":<question>},{"role":"assistant","content":<answer>}]}'
    ),
    "Alpaca / Self-Instruct": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"instruction": <question>, "input": "", "output": <answer>}.'
    ),
    "Dolly v2": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"instruction": <question>, "context": "", "response": <answer>}.'
    ),
    "DPO (Direct Preference Optimization)": (
        "Derive one concise question about the chunk and create two answers: A=best factual answer from the chunk; "
        "B=a clearly worse but plausible answer (short/vague). Set winner to the better one.\n"
        'Emit: {"prompt": <question>, "chosen": <best_answer>, "rejected": <worse_answer>}.'
    ),
    "Pairwise Ranking (A/B with Winner)": (
        "Derive one concise question about the chunk and create two answers: response_a=best factual answer from the chunk; "
        'response_b=a clearly worse but plausible answer. Set "winner":"A".\n'
        'Emit: {"prompt": <question>, "response_a": <best_answer>, "response_b": <worse_answer>, "winner": "A"}.'
    ),
    "ShareGPT-style Conversations": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"conversations":[{"from":"human","value":<question>},{"from":"gpt","value":<answer>}]}'
    ),
    "T5/FLAN Style": (
        "Derive one concise question about the chunk and answer it strictly from the chunk.\n"
        'Emit: {"inputs": <question>, "targets": <answer>}.'
    ),
}

_DEFAULT_HINT = (
    "Derive one concise question about the chunk and answer it strictly from the chunk. "
    "Map that (question, answer) pair into the fields required by the target format."
)


def clone_llm7(llm: ChatLLM7, **overrides: Any) -> ChatLLM7:
    """
    Clone ChatLLM7 while preserving hidden/sensitive fields (e.g., token),
    then apply overrides like seed=123.
    """
    try:
        # Pydantic v2
        return llm.model_copy(update=overrides)  # type: ignore[attr-defined]
    except AttributeError:
        # Pydantic v1
        return llm.copy(update=overrides)  # type: ignore[attr-defined]


def generate_jsonl_from_text(
    text: str,
    *,
    target_format_name: str,
    llm: BaseChatModel | None = None,
    chunk_word_size: int = 1000,
    rows_per_chunk: int = 1,
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

    format_hint = _FORMAT_HINTS.get(target_format_name, _DEFAULT_HINT)

    system_message_content = (
        "You are a deterministic JSONL line generator.\n"
        "TASK:\n"
        "1) From the provided text CHUNK, extract ONE concise, fact-seeking QUESTION that can be answered using ONLY that chunk.\n"
        "2) Produce ONE ANSWER grounded strictly in the chunk. If the chunk lacks the facts, answer with a minimal, truthful fallback such as \"unknown\".\n"
        "3) Map the (QUESTION, ANSWER) pair into the TARGET FORMAT exactly as instructed in the FORMAT MAPPING below.\n"
        "4) Output EXACTLY ONE JSON object wrapped ONLY by <jsonl_line>...</jsonl_line>. No extra text.\n"
        "\n"
        "OUTPUT RULES:\n"
        "- JSON must be valid and MINIFIED (no pretty-print, no trailing commas).\n"
        "- Use double quotes for all keys and string values; escape all internal quotes, backslashes, and newlines.\n"
        "- Do NOT include markdown, code fences, comments, XML outside the tags, or multiple objects.\n"
        "- Keep QUESTION and ANSWER short (<= 2 sentences each).\n"
    )

    pattern = r"<jsonl_line>\s*(\{[\s\S]*?\})\s*</jsonl_line>"
    # make it as a set to avoid duplicates
    valid_lines: Set[str] = set()
    total_chunks = len(chunks * rows_per_chunk)
    skipped_count = 0

    with tqdm(total=total_chunks, desc="Generating JSONL", unit="chunk") as pbar:
        for i, chunk_text in enumerate(chunks):
            for _ in range(rows_per_chunk):
                try:
                    if rows_per_chunk > 1:
                        llm = clone_llm7(llm, seed=_)

                    human_message_content = [
                        {
                            "type": "text",
                            "text": (
                                f"TARGET FORMAT NAME: {target_format_name}\n\n"
                                "FORMAT MAPPING (how to place QUESTION/ANSWER into fields):\n"
                                f"{format_hint}\n\n"
                                "CONFORMANCE REGEX (the JSON inside the tags must match this when minified):\n"
                                f"{line_regex_str}\n\n"
                                "EXAMPLE SHAPE (for structure only; DO NOT COPY CONTENT):\n"
                                f"{example_json}\n\n"
                                "REQUIRED WRAPPER TAGS (exactly one object inside):\n"
                                "<jsonl_line>{...}</jsonl_line>\n\n"
                                "CHUNK START >>>\n"
                                f"{chunk_text}\n"
                                "<<< CHUNK END"
                            ),
                        }
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
                        valid_lines.add(normalized_line)
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