# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *


class TrustCheck(gl.Contract):
    """Consensus-based verification of a claim against a supplied web source."""

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
            try:
                response = gl.nondet.web.get(source_url)
                content = response.body.decode("utf-8", errors="ignore")[:12000]

                prompt = f"""
You are a careful claim verifier.

Claim:
{claim}

Source URL:
{source_url}

Source content:
{content}

Classify the claim using only the supplied source content.
Return exactly one of these labels and nothing else:
VERIFIED
REFUTED
UNCERTAIN

VERIFIED means the source directly supports the claim.
REFUTED means the source directly contradicts the claim.
UNCERTAIN means the source is unavailable, ambiguous, irrelevant, or insufficient.
"""
                answer = gl.nondet.exec_prompt(prompt).strip().upper()
                if answer == "VERIFIED":
                    return "VERIFIED"
                if answer == "REFUTED":
                    return "REFUTED"
                return "UNCERTAIN"
            except Exception:
                return "UNCERTAIN"

        consensus_result = gl.eq_principle.prompt_comparative(
            analyze_source,
            principle=(
                "The validators must agree on exactly the same claim-verification "
                "label. VERIFIED, REFUTED, and UNCERTAIN are distinct outcomes. "
                "Use UNCERTAIN when the source or evidence is insufficient."
            ),
        )

        normalized = str(consensus_result).strip().upper()
        if normalized == "VERIFIED":
            self.result = "VERIFIED"
        elif normalized == "REFUTED":
            self.result = "REFUTED"
        else:
            self.result = "UNCERTAIN"

        return self.result
