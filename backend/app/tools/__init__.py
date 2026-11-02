"""Tool registry.

Phase 4 turns this package into the LLM function-calling surface: a registry
of callables the model may invoke, plus the confirmation gate that protects
tools which message people, delete data, or spend money.

Phase 1 ships the package only so the module layout is in place.
"""
