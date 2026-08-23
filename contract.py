# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import hashlib
import json


class TrustCheck(gl.Contract):
    """Consensus-based claim verification with durable, claim-indexed receipts."""

    claim_counter: int
    latest_claim_id: str
    claims: dict

    def __init__(self):
        self.claim_counter = 0
        self.latest_claim_id = ""
        self.claims = {}

    @gl.public.view
    def get_latest_claim_id(self) -> str:
        return self.latest_claim_id

    @gl.public.view
    def get_receipt(self, claim_id: str) -> str:
        receipt = self.claims.get(claim_id)
        if receipt is None:
            return ""
        return json.dumps(receipt, sort_keys=True)

    @gl.public.view
    def get_result(self) -> str:
        if not self.latest_claim_id:
            return "UNCERTAIN"
        receipt = self.claims.get(self.latest_claim_id)
        if receipt is None:
            return "UNCERTAIN"
        return receipt["result"]

    @gl.public.write
    def submit_claim(self, claim: str, source_url: str) -> str:
        self.claim_counter += 1
        claim_id = hashlib.sha256(
            f"{self.claim_counter}:{claim}:{source_url}".encode("utf-8")
        ).hexdigest()
        self.latest_claim_id = claim_id

        result, evidence_digest = self._evaluate_claim(claim, source_url)

        self.claims[claim_id] = {
            "claim_id": claim_id,
            "claim": claim,
            "source_url": source_url,
            "evidence_digest": evidence_digest,
            "result": result,
        }
        return result

    @gl.public.write
    def evaluate(self) -> str:
        if not self.latest_claim_id:
            return "UNCERTAIN"

        receipt = self.claims.get(self.latest_claim_id)
        if receipt is None:
            return "UNCERTAIN"

        result, evidence_digest = self._evaluate_claim(
            receipt["claim"], receipt["source_url"]
        )
        receipt["result"] = result
        receipt["evidence_digest"] = evidence_digest
        self.claims[self.latest_claim_id] = receipt
        return result

    def _evaluate_claim(self, claim: str, source_url: str):
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
        if normalized not in {"VERIFIED", "REFUTED", "UNCERTAIN"}:
            normalized = "UNCERTAIN"

        evidence_digest = hashlib.sha256(
            f"{claim}\n{source_url}\n{normalized}".encode("utf-8")
        ).hexdigest()
        return normalized, evidence_digest
