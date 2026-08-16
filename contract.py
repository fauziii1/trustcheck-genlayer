# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json


class TrustCheck(gl.Contract):
    """Consensus-based claim verification using a supplied source URL."""

    claim: str
    source_url: str
    result: str

    def __init__(self):
        self.claim = ""
        self.source_url = ""
        self.result = "UNCERTAIN"

    @gl.public.view
    def get_result(self) -> str:
        return self.result

    @gl.public.write
    def submit_claim(self, claim: str, source_url: str) -> str:
        self.claim = claim
        self.source_url = source_url
        return self._evaluate_claim()

    @gl.public.write
    def evaluate(self) -> str:
        if not self.claim or not self.source_url:
            self.result = "UNCERTAIN"
            return self.result
        return self._evaluate_claim()

    def _evaluate_claim(self) -> str:
        claim = self.claim
        source_url = self.source_url

        def analyze_source() -> str:
            response = gl.nondet.web.get(source_url)
            content = response.body.decode("utf-8", errors="ignore")
            content = content[:12000]

            prompt = f"""
You are a careful claim verifier.

Claim to evaluate:
{claim}

Source URL:
{source_url}

Source content:
{content}

Determine whether the source supports or contradicts the claim.
Return exactly one label and nothing else:
VERIFIED - the source directly supports the claim.
REFUTED - the source directly contradicts the claim.
UNCERTAIN - the source is unavailable, ambiguous, irrelevant, or insufficient.
"""
            answer = gl.nondet.exec_prompt(prompt).strip().upper()
            if "REFUTED" in answer:
                return "REFUTED"
            if "VERIFIED" in answer:
                return "VERIFIED"
            return "UNCERTAIN"

        consensus_result = gl.eq_principle.prompt_comparative(
            analyze_source,
            "The validators should agree on the same claim-verification label. "
            "Treat VERIFIED, REFUTED, and UNCERTAIN as distinct outcomes. "
            "Use UNCERTAIN when evidence is insufficient."
        )

        normalized = str(consensus_result).upper()
        if "REFUTED" in normalized:
            self.result = "REFUTED"
        elif "VERIFIED" in normalized:
            self.result = "VERIFIED"
        else:
            self.result = "UNCERTAIN"

        return self.result
