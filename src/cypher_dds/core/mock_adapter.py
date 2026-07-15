"""Mock ELM327 serial adapter for development without a car or hardware.

Implements the same SerialLike surface as a real pyserial connection, so it
can be handed to SerialConnection/ELM327 unchanged. Everything above this
layer should be unable to tell the difference between a real adapter and
this one.
"""

from __future__ import annotations


class MockELM327Adapter:
    """In-memory stand-in for a pyserial ``Serial`` talking to a real ELM327.

    TODO:
      - canned response table keyed by AT/PID command string
      - simulate the '>' prompt terminator ELM327 uses to end a response
      - configurable scenario presets (e.g. "gm_2015_idle", "no_adapter",
        "dtc_present") so the TUI can be exercised against varied fake data
      - write(data) queues a command; read()/readline() drain the canned
        response for the last command written
    """

    def __init__(self, scenario: str = "default") -> None:
        self.scenario = scenario
        self._is_open = True

    def write(self, data: bytes) -> int:
        raise NotImplementedError

    def read(self, size: int = 1) -> bytes:
        raise NotImplementedError

    def readline(self) -> bytes:
        raise NotImplementedError

    def close(self) -> None:
        self._is_open = False

    @property
    def in_waiting(self) -> int:
        raise NotImplementedError

    @property
    def is_open(self) -> bool:
        return self._is_open
