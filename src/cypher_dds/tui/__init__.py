"""Terminal UI presentation layer (Textual).

Talks to cypher_dds.core only through its public interfaces (SerialConnection,
ELM327, PID/DTC/VIN modules) and to cypher_dds.profiles through the registry in
cypher_dds.profiles.base. Core logic must never import from here, so a future
GUI can sit alongside this package without touching core.
"""
