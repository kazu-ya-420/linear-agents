# Agent Structure 03
# break → sub-agent 1 → sub-agent 2 → merge

import os
import json
import textwrap
import openai
from dotenv import load_dotenv

load_dotenv()

# ───────────────────────── Config & Helper ─────────────────────────

MODEL = "openai/gpt-4o-2024-11-20"

# Colors for terminal output
BLUE = "\033[94m"
RED = "\033[91m"
RESET = "\033[0m"

api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("Set OPENROUTER_API_KEY environment variable")

client = openai.OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)


def chat(msgs):
    try:
        response = client.chat.completions.create(model=MODEL, messages=msgs)
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"API call failed: {e}")


conv = []

# ───────────────────────── Task-generation Agent ─────────────────────────

def generate_subtasks():
    txt = chat(conv + [
        {"role": "system", "content": "Return exactly TWO subtasks as JSON: {\"subtasks\": [\"first task\", \"second task\"]}"}
    ])
    try:
        data = json.loads(txt)
        subtasks = data["subtasks"]
        if len(subtasks) != 2:
            raise ValueError(f"Expected 2 subtasks, got {len(subtasks)}")
        conv.append({"role": "assistant", "content": txt})
        return subtasks[0].strip(), subtasks[1].strip()
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {txt}")

# ───────────────────────── First Sub-agent ─────────────────────────

def subagent_1(prompt):
    result = chat(conv + [
        {"role": "system", "content": "You are Sub-agent 1."},
        {"role": "user", "content": f"{prompt} Answer in short."}
    ])
    print(f"\n{'─' * 50}")
    print(f"{BLUE}🔹 Sub-agent 1 Response:{RESET}")
    print(f"{BLUE}{textwrap.indent(result, '    ')}{RESET}")
    print(f"{'─' * 50}")
    return result

# ───────────────────────── Second Sub-agent ─────────────────────────

def subagent_2(prompt):
    result = chat(conv + [
        {"role": "system", "content": "You are Sub-agent 2."},
        {"role": "user", "content": f"{prompt} Answer in short."}
    ])
    print(f"\n{'─' * 50}")
    print(f"{RED}🔹 Sub-agent 2 Response:{RESET}")
    print(f"{RED}{textwrap.indent(result, '    ')}{RESET}")
    print(f"{'─' * 50}")
    return result

# ───────────────────────── Merge Agent ─────────────────────────

def merge_results():
    return chat(conv + [
        {"role": "system", "content": "Combine the two sub-results into ONE clear answer."}
    ])

# ───────────────────────── Main Flow ─────────────────────────

def main():
    task = input("📝 MAIN TASK → ").strip()
    if not task:
        raise ValueError("No task given.")
    
    conv.append({"role": "user", "content": task})

    sub1, sub2 = generate_subtasks()
    print(f"\n📦 Subtasks:\n 1) {sub1}\n 2) {sub2}")

    r1 = subagent_1(sub1)
    conv.append({"role": "assistant", "content": f"[Sub-agent 1] {r1}"})

    r2 = subagent_2(sub2)
    conv.append({"role": "assistant", "content": f"[Sub-agent 2] {r2}"})

    final_answer = merge_results()
    print(f"\n{'─' * 50}")
    print(f"✅ FINAL ANSWER")
    print(f"{textwrap.indent(final_answer, '    ')}")
    print(f"{'─' * 50}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        exit(1)
