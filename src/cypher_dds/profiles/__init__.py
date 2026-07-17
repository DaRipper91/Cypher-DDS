"""Brand-specific vehicle profiles (plugin layer).

Each profile is a self-contained module exposing a VehicleProfile subclass
and registering itself via cypher_dds.profiles.base.register_profile. Nothing in
cypher_dds.core should import from here — profiles depend on core, never the
reverse.

Importing this package registers all built-in profiles as a side effect.
"""

from cypher_dds.profiles import dodge_chrysler, ford, gm, honda_acura, kia, toyota_lexus  # noqa: F401
