# TrustCheck — GenLayer Intelligent Contract

TrustCheck is a GenLayer application for consensus-based verification of online claims.

## What it does

A user submits:

- a claim to evaluate
- an authoritative source URL

The Intelligent Contract retrieves the source content through GenLayer's nondeterministic web access and asks validators to evaluate the evidence. GenLayer consensus then determines one of three outcomes:

- `VERIFIED` — the source supports the claim
- `REFUTED` — the source contradicts the claim
- `UNCERTAIN` — the evidence is unavailable, ambiguous, irrelevant, or insufficient

The result is stored in the contract state.

## Why GenLayer is central

TrustCheck is not a conventional frontend around a normal smart contract. The core verification step depends on GenLayer's nondeterministic web access, LLM evaluation, and validator consensus. The contract only writes the final result after the consensus step.

## Contract

`contract.py` contains the complete Intelligent Contract.

Public methods:

- `get_result()` — read the latest verification result
- `submit_claim(claim, source_url)` — submit a claim and source for verification
- `evaluate()` — re-evaluate the currently stored claim and source

The contract has no constructor parameters.

## Deployment

The latest deployment used for the project was finalized in GenLayer Studio.

Latest contract address:

`0x0B...B37e`

> Replace the shortened address above with the full deployed address when publishing a public deployment record.

## Example workflow

1. Deploy `contract.py` in GenLayer Studio.
2. Call `submit_claim` with a factual claim and an authoritative source URL.
3. Wait for the transaction to reach consensus/finalization.
4. Call `get_result()` to read the stored result.

Example input:

```text
claim: The Earth orbits the Sun.
source_url: https://example.com/authoritative-source
```

## Development notes

The contract follows GenLayer Intelligent Contract conventions:

- `gl.Contract` for the contract class
- `@gl.public.view` for read-only access
- `@gl.public.write` for state-changing methods
- `gl.nondet.web.get()` for external web data
- `gl.nondet.exec_prompt()` for the verification model
- `gl.eq_principle.prompt_comparative()` for validator consensus

Before deploying changes, validate the contract with the GenLayer tooling/linter and test the complete transaction lifecycle.

## Project status

The contract has been deployed and finalized in GenLayer Studio. This repository contains the source code and project documentation used for the GenLayer Project contribution.
