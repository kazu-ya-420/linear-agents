# Agent Structure 02: parallel agents with shared context (still unreliable)
# break → two parallel sub-agents with shared log → merge
# 
# why still unreliable:
# - agents share conversation history but still run in parallel
# - race conditions: agents might start before others finish writing
# - timing issues can cause inconsistent behavior

import os
import json
import threading
import queue
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


# ───────────────────────── Shared Conversation Log ─────────────────────────

# shared memory that all agents can read from and write to
# lock prevents multiple agents from writing at the same time
conv = []
lock = threading.Lock()

# ───────────────────────── Task-generation Agent ─────────────────────────

def generate_subtasks():
    # break down task using current conversation context
    txt = chat(conv + [
        {"role": "system", "content": "Return exactly TWO subtasks as JSON: {\"subtasks\": [\"first task\", \"second task\"]}"}
    ])
    try:
        data = json.loads(txt)
        subtasks = data["subtasks"]
        if len(subtasks) != 2:
            raise ValueError(f"Expected 2 subtasks, got {len(subtasks)}")
        # safely add to shared conversation log
        with lock:
            conv.append({"role": "assistant", "content": txt})
        return subtasks[0].strip(), subtasks[1].strip()
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {txt}")


# ───────────────────────── Shared-log Sub-agent Template ─────────────────────────

def run_sub(prompt, tag, out_q):
    # each agent gets a copy of the shared conversation history
    # this gives context but doesn't prevent parallel execution issues
    msgs = conv.copy() + [
        {"role": "system", "content": f"You are Sub-agent {tag}."},
        {"role": "user", "content": f"{prompt} Answer in short."}
    ]
    res = chat(msgs)
    
    # print results immediately (order may vary due to parallel execution)
    color = BLUE if tag == "1" else RED
    print(f"\n{'─' * 50}")
    print(f"{color}🔹 Sub-agent {tag} Response:{RESET}")
    print(f"{color}{textwrap.indent(res, '    ')}{RESET}")
    print(f"{'─' * 50}")
    
    out_q.put((tag, res))
    # safely write back to shared log
    with lock:
        conv.append({"role": "assistant", "content": f"[Sub-agent {tag}] {res}"})


# ───────────────────────── Merge Agent ─────────────────────────

def merge_results(r1, r2):
    # merge agent has full conversation context
    # better than isolated merge but still dealing with parallel execution artifacts
    return chat(conv + [
        {"role": "system", "content": "Combine the two sub-results into ONE clear answer."},
        {"role": "user", "content": f"RESULT-1:\n{r1}\n\nRESULT-2:\n{r2}"}
    ])


# ───────────────────────── Main Flow ─────────────────────────

def main():
    task = input("📝 MAIN TASK → ").strip()
    if not task:
        raise ValueError("No task given.")
    
    # add user task to shared conversation
    conv.append({"role": "user", "content": task})

    sub1, sub2 = generate_subtasks()
    print(f"\n📦 Subtasks:\n 1) {sub1}\n 2) {sub2}")

    # run agents in parallel but with shared conversation access
    # improvement: agents can see context
    # problem: still parallel timing issues and race conditions
    q = queue.Queue()
    threading.Thread(target=run_sub, args=(sub1, "1", q)).start()
    threading.Thread(target=run_sub, args=(sub2, "2", q)).start()

    # collect results as they complete (order may vary)
    results = {}
    while len(results) < 2:
        tag, out = q.get()
        results[tag] = out

    # merge with full conversation context
    final = merge_results(results["1"], results["2"])
    print(f"\n{'─' * 50}")
    print(f"✅ FINAL ANSWER")
    print(f"{textwrap.indent(final, '    ')}")
    print(f"{'─' * 50}")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        exit(1)
