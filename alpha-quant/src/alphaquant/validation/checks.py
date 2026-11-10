"""A gate is a list of checks; it passes when none of them fails.

A check with passed=None could not be evaluated (a number that does not exist
for this sample, a period not given): it does not fail the gate, but the gate is
then not `complete`, and the report says so. "Could not judge" must never read
as "passed".
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Check:
    name: str
    passed: bool | None
    value: str
    threshold: str


@dataclass(frozen=True)
class GateResult:
    stage: int
    title: str
    checks: list[Check]
    data: dict = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return all(c.passed is not False for c in self.checks)

    @property
    def complete(self) -> bool:
        return all(c.passed is not None for c in self.checks)

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.checks if c.passed is False]

    def report(self) -> str:
        mark = {True: "OK ", False: "NO ", None: "?  "}
        lines = [f"Gate {self.stage} - {self.title}"]
        lines += [f"  {mark[c.passed]} {c.name:<34} {c.value:<22} {c.threshold}" for c in self.checks]
        verdict = "PASS" if self.passed else "FAIL"
        if self.passed and not self.complete:
            verdict += " (incomplete: checks marked ? not evaluated)"
        lines.append(f"  VERDICT: {verdict}")
        return "\n".join(lines)
