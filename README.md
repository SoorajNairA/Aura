# AURA

AURA is a fully local AI executive assistant with memory, desktop automation,
offline LLMs, and natural voice interaction.

It is built for a personal workstation: speech in, local reasoning, safe tool
execution, visible results, and spoken confirmation without relying on cloud AI
APIs.

## Features

- Offline Qwen conversation via Ollama
- XTTS-v2 voice synthesis
- Voice cloning with a local reference sample
- Faster-Whisper speech recognition
- Persistent memory and project memory
- Desktop automation for apps, URLs, files, and folders
- Executive agent for project creation
- Tool calling with a registered safe tool catalog
- Starter project generation
- Result auto-reveal in Explorer or VS Code
- Safety layer for destructive or unknown actions

## Architecture

```text
Speech
↓
Faster-Whisper
↓
Qwen (Ollama)
↓
Intent Router
↓
Executive Agent / Tool Registry
↓
Tools
↓
Memory
↓
XTTS-v2
```

## Screenshots

Screenshots and demo media will be added under `assets/`.

## Installation

1. Install Python 3.9.

2. Install Ollama and pull the local conversation model:

```bash
ollama pull qwen2.5:14b
```

3. Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

4. Install dependencies:

```bash
pip install -r requirements.txt
```

5. Copy the environment template:

```bash
copy .env.example .env
```

6. Run AURA:

```bash
python -m aura.main
```

For XTTS-v2 voice synthesis, install the optional voice requirements:

```bash
pip install -r requirements-xtts.txt
```

XTTS model files are downloaded at runtime into `models/xtts/`, which is ignored
by Git. If you use voice cloning, place a clean 10-60 second sample at
`voices/aura_voice.wav`.

## Hardware Used

The validated demo machine used:

- NVIDIA RTX 3050 Laptop GPU, 4 GB VRAM
- XTTS-v2 on CUDA
- Faster-Whisper small on CPU int8
- Ollama running Qwen locally

## Validation

Current local certification artifacts:

- Jarvis acceptance: 39/39
- XTTS activation: 7/7
- Tool routing, memory, planner isolation, offline mode, and visibility tests pass

See `docs/` for audit, security, release, and certification reports.

## Repository Hygiene

The public repository excludes:

- `.env`
- logs
- memory state
- generated projects
- local model caches
- virtual environments

Large optional media and model formats are configured for Git LFS.

## License

MIT License.

XTTS-v2 model usage is subject to Coqui's model license. Review the applicable
license before downloading or redistributing model artifacts.
