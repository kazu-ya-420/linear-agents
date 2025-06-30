# Multi-Agent Task Breakdown Examples

Four different approaches to breaking down tasks into subtasks using AI agents.

## Setup

1. Create conda environment:
```bash
conda create -n testing python=3.12 -y
conda activate testing
```

2. Install dependencies:
```bash
pip install uv
uv pip install openai
uv pip install python-dotenv
```

3. Create `.env` file:
```bash
OPENROUTER_API_KEY=your_api_key_here
```

## Files

**01-unreliable.py** - Parallel sub-agents. No shared context.

**02-still-unreliable.py** - Parallel sub-agents. Shared conversation log.

**03-simple-and-reliable.py** - Sequential sub-agents. Full shared context.

**04-reliable-on-longer-tasks.py** - Sequential sub-agents. Context compression between steps.

## Usage

Run any file:
```bash
python 01-unreliable.py
```

Enter your task when prompted. The agent will break it into two subtasks and execute them.

## Notes

All files use OpenRouter API with GPT-4o model. You need an OpenRouter API key to run these examples. 