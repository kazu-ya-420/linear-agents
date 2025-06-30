# Agent Structure 01: parallel agents (unreliable)
# break → two parallel sub-agents → merge (no shared context)

import os
import json
import asyncio
import textwrap
import openai
from dotenv import load_dotenv

load_dotenv()

# ───────────────────────── Config & Helper ─────────────────────────

MODEL = "openai/gpt-4.1-mini"

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


def ask(msgs):
    try:
        response = client.chat.completions.create(model=MODEL, messages=msgs)
        return response.choices[0].message.content.strip()
    except Exception as e:
        raise RuntimeError(f"API call failed: {e}")


# ───────────────────────── Task-generation Agent ─────────────────────────

def generate_subtasks(task):
    # ask ai to break down the main task into exactly 2 smaller tasks
    # using json format makes parsing more reliable than regex
    reply = ask([
        {"role": "system", "content": "Return exactly TWO subtasks as JSON: {\"subtasks\": [\"first task\", \"second task\"]}"},
        {"role": "user", "content": task}
    ])
    try:
        # parse the json response to extract the two subtasks
        data = json.loads(reply)
        subtasks = data["subtasks"]
        if len(subtasks) != 2:
            raise ValueError(f"Expected 2 subtasks, got {len(subtasks)}")
        return subtasks[0].strip(), subtasks[1].strip()
    except (json.JSONDecodeError, KeyError) as e:
        raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {reply}")


# ───────────────────────── First Sub-agent ─────────────────────────

async def run_sub1(prompt):
    # this agent works in complete isolation - no context from other agents
    # it only knows its own subtask, nothing else
    result = ask([{"role": "user", "content": f"{prompt} Answer in short."}])
    print(f"\n{'─' * 50}")
    print(f"{BLUE}🔹 Sub-agent 1 Response:{RESET}")
    print(f"{BLUE}{textwrap.indent(result, '    ')}{RESET}")
    print(f"{'─' * 50}")
    return ("1", result)


# ───────────────────────── Second Sub-agent ─────────────────────────

async def run_sub2(prompt):
    # this agent also works in isolation - can't see what sub-agent 1 did
    # this is why results often don't work well together
    result = ask([{"role": "user", "content": f"{prompt} Answer in short."}])
    print(f"\n{'─' * 50}")
    print(f"{RED}🔹 Sub-agent 2 Response:{RESET}")
    print(f"{RED}{textwrap.indent(result, '    ')}{RESET}")
    print(f"{'─' * 50}")
    return ("2", result)


# ───────────────────────── Merge Agent ─────────────────────────

def merge_results(r1, r2):
    # the merge agent faces a tough job: combining two potentially unrelated results
    # since the sub-agents worked independently, their outputs might not fit together
    # this often leads to forced or awkward combinations
    return ask([
        {"role": "system", "content": "Combine the two results into ONE clear answer. be concise."},
        {"role": "user", "content": f"RESULT-1:\n{r1}\n\nRESULT-2:\n{r2}"}
    ])


# ───────────────────────── Main Flow ─────────────────────────

async def main():
    # get the main task from user
    task = input("📝 MAIN TASK → ").strip()
    if not task:
        raise ValueError("No task given.")
    
    # break the main task into 2 subtasks
    sub1, sub2 = generate_subtasks(task)
    print(f"\n📦 Subtasks:\n 1) {sub1}\n 2) {sub2}")

    # run both sub-agents at the same time (parallel execution)
    # this is fast but problematic - they can't coordinate with each other
    agent_results = await asyncio.gather(
        run_sub1(sub1),
        run_sub2(sub2)
    )

    # collect the results from both agents
    results = {}
    for tag, out in agent_results:
        results[tag] = out

    # try to merge the disconnected results into one answer
    # this is where the problems become obvious
    final = merge_results(results["1"], results["2"])
    print(f"\n{'─' * 50}")
    print(f"✅ FINAL ANSWER")
    print(f"{textwrap.indent(final, '    ')}")
    print(f"{'─' * 50}")


if __name__ == "__main__":
    # run the main function and handle any errors gracefully
    try:
        asyncio.run(main())
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
        exit(1)
