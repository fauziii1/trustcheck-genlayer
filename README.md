# TrustCheck — GenLayer Intelligent Contract

TrustCheck is a GenLayer application for consensus-based verification of online claims.

## Problem

Online claims are easy to repeat but difficult to verify consistently when the evidence lives on the web. TrustCheck turns a claim plus a source URL into a consensus-backed verification result.

## How it works

A user submits:

- a claim to evaluate
- a source URL containing the evidence

The Intelligent Contract fetches the source through GenLayer's nondeterministic web access. An LLM classifies the evidence as `VERIFIED`, `REFUTED`, or `UNCERTAIN`, and `gl.eq_principle.prompt_comparative()` is used so validators independently perform the same task and compare the outcome. Only the consensus-agreed result is written to contract state.

Results:

- `VERIFIED` — the source directly supports the claim
- `REFUTED` — the source directly contradicts the claim
- `UNCERTAIN` — evidence is unavailable, ambiguous, irrelevant, or insufficient

## Why GenLayer is central

The core product is the Intelligent Contract itself: web access and LLM evaluation are nondeterministic, so the result cannot simply be calculated by a conventional deterministic smart contract. GenLayer's Equivalence Principle provides the validator consensus needed before the result becomes persistent state.

## Repository structure

```text
contract.py              # GenLayer Intelligent Contract
frontend/                # Next.js + GenLayerJS dApp
  app/page.tsx           # claim form, wallet connection, read/write lifecycle
  app/layout.tsx
  package.json
  tsconfig.json
```

## Contract API

- `get_result()` — read the latest verification result
- `submit_claim(claim, source_url)` — store the claim/source and verify it through consensus
- `evaluate()` — re-evaluate the currently stored claim/source

The constructor has no parameters.

## Frontend

The frontend is a real GenLayerJS client rather than a mock UI. It:

1. connects to a browser wallet
2. switches the client to Studionet
3. sends `submit_claim` through `writeContract()`
4. waits for the transaction to reach `FINALIZED`
5. checks the transaction execution result
6. reads `get_result()` after successful execution

Set the deployed contract address before running the frontend:

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```text
NEXT_PUBLIC_TRUSTCHECK_ADDRESS=0xYOUR_FULL_DEPLOYED_ADDRESS
```

Then run:

```bash
npm run dev
```

Open the local Next.js URL, connect a wallet configured for GenLayer Studionet, submit a claim and source URL, and wait for finalization.

## Deployment

The contract was deployed and finalized in GenLayer Studio during development. The currently referenced deployment is the TrustCheck instance whose Studio UI showed an address beginning `0x0B` and ending `B37e`.

Do not treat the shortened address as a complete on-chain identifier. Put the full address in `NEXT_PUBLIC_TRUSTCHECK_ADDRESS` when running the dApp.

## Example

```text
Claim: The Earth orbits the Sun.
Source URL: https://example.org/authoritative-source
```

## Development and verification

The contract follows the current GenLayer Intelligent Contract model:

- `gl.Contract` for the contract class
- typed persistent state fields
- `@gl.public.view` for read-only methods
- `@gl.public.write` for state-changing methods
- `gl.nondet.web.get()` for external web data
- `gl.nondet.exec_prompt()` for LLM evaluation
- `gl.eq_principle.prompt_comparative()` for independent validator comparison

Before a production/testnet redeployment, run the GenLayer linter and test the complete transaction lifecycle. The frontend intentionally checks both consensus finalization and `txExecutionResultName`; a finalized transaction with failed execution is not treated as a successful verification.

## Limitations

TrustCheck verifies a claim against the supplied source; it does not prove that the source itself is truthful or authoritative. `UNCERTAIN` is preferred when the source cannot provide enough evidence rather than forcing a binary verdict.
