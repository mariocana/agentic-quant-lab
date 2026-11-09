"""Phase 2. LLM agents live here (Analyst, Adversary, Quant, Journal).

Contract: they read desk.schemas and the journal, and they emit Thesis / Review.
They never import desk.execution and never construct an OrderIntent.
Nothing in this package exists yet, on purpose: phase 1 ships without it.
"""
