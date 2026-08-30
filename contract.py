# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import hashlib
import json


class TrustCheck(gl.Contract):
    """
    TrustCheck Milestone 2

    Consensus-based claim verification using two independent
    web sources.

    Each claim receives a durable, claim-indexed receipt containing:
    - unique claim ID
    - verification result
    - evidence digest
    - primary source provenance
    - corroborating source provenance
    """

    claim_counter: u256
    latest_claim_id: str
    latest_result: str
    claims: TreeMap[str, str]

    def __init__(self):
        self.claim_counter = u256(0)
        self.latest_claim_id = ""
        self.latest_result = "UNCERTAIN"

    @gl.public.view
    def get_latest_claim_id(self) -> str:
        return self.latest_claim_id

    @gl.public.view
    def get_receipt(self, claim_id: str) -> str:
        return self.claims.get(claim_id, "")

    @gl.public.view
    def get_result(self) -> str:
        return self.latest_result

    @gl.public.write
    def submit_claim(
        self,
        claim: str,
        source_url: str,
        corroborating_source_url: str,
    ) -> str:
        self.claim_counter = self.claim_counter + u256(1)

        claim_id = hashlib.sha256(
            (
                claim
                + "|"
                + source_url
                + "|"
                + corroborating_source_url
                + "|"
                + str(self.claim_counter)
            ).encode("utf-8")
        ).hexdigest()

        result, evidence_digest = self._evaluate_claim(
            claim,
            source_url,
            corroborating_source_url,
        )

        receipt = {
            "claim_id": claim_id,
            "claim": claim,
            "result": result,
            "source_url": source_url,
            "corroborating_source_url": corroborating_source_url,
            "evidence_digest": evidence_digest,
        }

        self.claims[claim_id] = json.dumps(
            receipt,
            sort_keys=True,
        )

        self.latest_claim_id = claim_id
        self.latest_result = result

        return result

    @gl.public.write
    def evaluate(self) -> str:
        if not self.latest_claim_id:
            self.latest_result = "UNCERTAIN"
            return self.latest_result

        receipt = self.claims.get(
            self.latest_claim_id,
            "",
        )

        if not receipt:
            self.latest_result = "UNCERTAIN"
            return self.latest_result

        try:
            data = json.loads(receipt)

            result, evidence_digest = self._evaluate_claim(
                data["claim"],
                data["source_url"],
                data["corroborating_source_url"],
            )

            data["result"] = result
            data["evidence_digest"] = evidence_digest

            self.claims[self.latest_claim_id] = json.dumps(
                data,
                sort_keys=True,
            )

            self.latest_result = result
            return result

        except Exception:
            self.latest_result = "UNCERTAIN"
            return self.latest_result

    def _evaluate_claim(
        self,
        claim: str,
        source_url: str,
        corroborating_source_url: str,
    ):
        def analyze_sources() -> str:
            try:
                response_a = gl.nondet.web.get(source_url)
                response_b = gl.nondet.web.get(corroborating_source_url)

                content_a = response_a.body.decode(
                    "utf-8",
                    errors="ignore",
                )[:10000]

                content_b = response_b.body.decode(
                    "utf-8",
                    errors="ignore",
                )[:10000]

                evidence_material = (
                    claim
                    + "|SOURCE_A|"
                    + source_url
                    + "|"
                    + content_a
                    + "|SOURCE_B|"
                    + corroborating_source_url
                    + "|"
                    + content_b
                )

                evidence_digest = hashlib.sha256(
                    evidence_material.encode("utf-8")
                ).hexdigest()

                prompt = f"""
You are a careful claim verification agent.

Verify the following claim using TWO independent web sources.

CLAIM:
{claim}

PRIMARY SOURCE:
{source_url}

PRIMARY SOURCE CONTENT:
{content_a}

CORROBORATING SOURCE:
{corroborating_source_url}

CORROBORATING SOURCE CONTENT:
{content_b}

Rules:

VERIFIED:
Both sources independently support the claim.

REFUTED:
The available evidence clearly contradicts the claim.

UNCERTAIN:
The sources are unavailable, ambiguous, irrelevant,
contradictory, or insufficient.

Do not invent information.
Do not use knowledge outside the supplied source content.

Return exactly one label:

VERIFIED
REFUTED
UNCERTAIN
"""

                answer = gl.nondet.exec_prompt(
                    prompt
                ).strip().upper()

                if answer == "VERIFIED":
                    result = "VERIFIED"
                elif answer == "REFUTED":
                    result = "REFUTED"
                else:
                    result = "UNCERTAIN"

                return json.dumps(
                    {
                        "result": result,
                        "evidence_digest": evidence_digest,
                    },
                    sort_keys=True,
                )

            except Exception:
                return json.dumps(
                    {
                        "result": "UNCERTAIN",
                        "evidence_digest": "",
                    },
                    sort_keys=True,
                )

        consensus_result = gl.eq_principle.prompt_comparative(
            analyze_sources,
            principle=(
                "Validators must independently evaluate the claim "
                "using both supplied sources. The result field must "
                "agree exactly. VERIFIED requires both sources to "
                "support the claim. REFUTED requires clear "
                "contradictory evidence. Otherwise use UNCERTAIN."
            ),
        )

        try:
            data = json.loads(str(consensus_result))
            result = data.get("result", "UNCERTAIN")
            evidence_digest = data.get("evidence_digest", "")
        except Exception:
            result = "UNCERTAIN"
            evidence_digest = ""

        if result not in (
            "VERIFIED",
            "REFUTED",
            "UNCERTAIN",
        ):
            result = "UNCERTAIN"

        return result, evidence_digest
