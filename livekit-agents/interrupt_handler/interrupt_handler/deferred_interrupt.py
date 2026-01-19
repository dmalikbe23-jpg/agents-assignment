import re
import asyncio
from typing import Optional

IGNORE_WORDS = {
    "yeah", "ok", "okay", "hmm", "right", "uh", "uh-huh", "yes"
}

INTERRUPT_WORDS = {
    "stop", "wait", "no", "hold", "pause"
}

INTERRUPT_WINDOW_MS = 120


def normalize(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def is_filler(text: str) -> bool:
    words = normalize(text).split()
    return len(words) > 0 and all(w in IGNORE_WORDS for w in words)


def is_interrupt(text: str) -> bool:
    clean = normalize(text)
    return any(cmd in clean for cmd in INTERRUPT_WORDS)


class DeferredInterruptController:
    def __init__(self):
        self.pending_task: Optional[asyncio.Task] = None

    async def handle_vad_trigger(
        self,
        agent_speaking: bool,
        get_partial_transcript,
        interrupt_cb,
        cancel_cb,
    ):
        if not agent_speaking:
            return

        async def decision():
            await asyncio.sleep(INTERRUPT_WINDOW_MS / 1000)
            text = get_partial_transcript()

            if text and is_interrupt(text):
                await interrupt_cb()
            else:
                await cancel_cb()

        self.pending_task = asyncio.create_task(decision())
