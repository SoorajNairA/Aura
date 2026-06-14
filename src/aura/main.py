from __future__ import annotations

import logging
import sys
from pathlib import Path

from .config import Settings, ensure_runtime_dirs
from .conversation_model import OllamaConversationModel
from .gui import AuraAppUI
from .orchestrator import AuraSupervisor


def _build_conversation_model(settings: Settings) -> OllamaConversationModel | None:
    """Construct the local ConversationModel from settings.

    Returns None if conversation_backend is not 'ollama' (reserved for future
    backends).  The caller handles None gracefully — OpenAI falls back.
    """
    if settings.conversation_backend != "ollama":
        logging.getLogger("aura").warning(
            f"main: conversation_backend='{settings.conversation_backend}' "
            "is not 'ollama'. Local conversation model will not be loaded."
        )
        return None
    return OllamaConversationModel(
        model=settings.ollama_conversation_model,
        base_url=settings.ollama_base_url,
        timeout=settings.ollama_request_timeout,
        context_length=settings.ollama_context_length,
    )


def _setup_logging(settings: Settings) -> None:
    root = logging.getLogger("aura")
    if root.handlers:
        return
    root.setLevel(logging.DEBUG)

    fmt_console = logging.Formatter("[AURA] %(levelname)-8s %(message)s")
    fmt_file = logging.Formatter("%(asctime)s [AURA] %(levelname)-8s %(message)s")
    fmt_trace = logging.Formatter("%(asctime)s  %(message)s")

    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(fmt_console)
    root.addHandler(sh)

    try:
        log_path = Path(settings.log_dir) / "aura.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt_file)
        root.addHandler(fh)
    except Exception as e:
        root.warning(f"Could not open log file: {e}")

    # Dedicated conversation trace logger — every classification, LLM call,
    # fast-path hit, memory lookup, and planner activation is recorded here.
    trace_logger = logging.getLogger("aura.trace")
    trace_logger.setLevel(logging.DEBUG)
    trace_logger.propagate = False  # keep trace out of the main aura log

    trace_sh = logging.StreamHandler(sys.stdout)
    trace_sh.setLevel(logging.INFO)
    trace_sh.setFormatter(logging.Formatter("[TRACE] %(message)s"))
    trace_logger.addHandler(trace_sh)

    try:
        trace_path = Path(settings.log_dir) / "conversation_trace.log"
        trace_fh = logging.FileHandler(trace_path, encoding="utf-8")
        trace_fh.setLevel(logging.DEBUG)
        trace_fh.setFormatter(fmt_trace)
        trace_logger.addHandler(trace_fh)
    except Exception as e:
        root.warning(f"Could not open trace log file: {e}")


def _print_capability_report(settings: Settings, supervisor: AuraSupervisor) -> None:
    logger = logging.getLogger("aura")
    openai_loaded = bool(settings.openai_api_key)
    elevenlabs_loaded = bool(settings.elevenlabs_api_key)

    stt_diag = supervisor.stt.get_diagnostics()
    stt_backend = (
        f"Faster-Whisper  model={stt_diag['model']}  "
        f"device={stt_diag['device_requested']}  "
        f"compute={stt_diag['compute_type']}"
    )
    tts_diag = supervisor.tts.get_diagnostics()
    tts_backend = str(tts_diag["backend"])
    cuda_info = (
        f"{stt_diag['cuda_device_count']} device(s) available"
        if stt_diag["cuda_available"]
        else "not available"
    )

    lines = [
        "=" * 60,
        "  AURA Capability Report",
        "=" * 60,
        f"  STT Backend          : {stt_backend}",
        f"  STT Model Load Time  : {stt_diag['load_time_s']}s",
        f"  STT Avg Latency      : {stt_diag['avg_transcription_ms']}ms  (no samples yet)",
        f"  GPU / CUDA           : {cuda_info}",
        f"  OpenAI STT           : Not supported (Faster-Whisper only)",
        f"  STT Backend Switch   : Not supported",
        f"  TTS Backend          : {tts_backend}",
        f"  TTS Device           : {tts_diag['device']}",
        f"  TTS Voice            : {tts_diag['voice']}",
        f"  TTS Warmup           : {'Complete' if tts_diag['warmup'] else 'Not run'}",
        f"  TTS Fallback         : {tts_diag['fallback']}",
        "-" * 60,
        "  Conversation Brain",
        "-" * 60,
        f"  Conv Backend         : {settings.conversation_backend}",
        f"  Conv Model           : {settings.ollama_conversation_model}",
        f"  Ollama URL           : {settings.ollama_base_url}",
        f"  Context Length       : {settings.ollama_context_length}",
        f"  Streaming Enabled    : True",
        f"  Memory Enabled       : True",
        "-" * 60,
        "  OpenAI (Planner only)",
        "-" * 60,
        f"  Planner Model        : {settings.openai_planner_model}",
        f"  Fallback Models      : {', '.join(settings.openai_fallback_models) or 'none'}",
        f"  OpenAI Key Loaded    : {openai_loaded}",
        f"  ElevenLabs Loaded    : {elevenlabs_loaded}",
        "=" * 60,
    ]
    report = "\n".join(lines)
    print(report)
    logger.debug("Capability report logged.")

    if not openai_loaded:
        logger.warning("OpenAI API key missing. All LLM features will be unavailable.")
    if not elevenlabs_loaded:
        logger.warning("ElevenLabs API key missing. TTS will use local pyttsx3.")


def main() -> None:
    settings = Settings()
    ensure_runtime_dirs(settings)
    _setup_logging(settings)
    conv_model = _build_conversation_model(settings)
    supervisor = AuraSupervisor(settings, conversation_model=conv_model)
    _print_capability_report(settings, supervisor)
    try:
        AuraAppUI(supervisor).run()
    except Exception:
        supervisor.run()


if __name__ == "__main__":
    main()
