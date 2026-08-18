# TrustCheck — GenLayer Claim Verification

TrustCheck is a GenLayer dApp for verifying a claim against a supplied web source. The Intelligent Contract fetches the source, evaluates the evidence through non-deterministic execution, and uses GenLayer's consensus principle to store one of three outcomes: `VERIFIED`, `REFUTED`, or `UNCERTAIN`.

## What is included

- `contract.py` — the GenLayer Intelligent Contract.
- `src/main.ts` — browser dApp logic using GenLayerJS.
- `src/style.css` — responsive interface.
- `index.html` — app entry point.
- `vite.config.ts` — static hosting configuration.

## Problem

Online claims are easy to repeat but difficult to verify consistently when the evidence lives on the web. TrustCheck turns a claim plus a source URL into a consensus-backed verification result.

## How it works

A user submits a claim and a source URL. The Intelligent Contract fetches the source through GenLayer's nondeterministic web access. An LLM classifies the evidence as `VERIFIED`, `REFUTED`, or `UNCERTAIN`, and `gl.eq_principle.prompt_comparative()` is used so validators independently perform the same task and compare the outcome. Only the consensus-agreed result is written to contract state.

## Why GenLayer is central

The core product is the Intelligent Contract itself: web access and LLM evaluation are nondeterministic, so the result cannot simply be calculated by a conventional deterministic smart contract. GenLayer's Equivalence Principle provides the validator consensus needed before the result becomes persistent state.

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
5. reads `get_result()` after successful execution
6. displays the on-chain verification result

Set the full deployed contract address in `.env`:

```text
VITE_CONTRACT_ADDRESS=0xYOUR_FULL_DEPLOYED_ADDRESS
```

Then run:

```bash
npm install
npm run dev
```

Open the local Vite URL, connect a wallet configured for GenLayer Studionet, submit a claim and source URL, and wait for finalization.

## Network

The frontend targets GenLayer **Studionet**. Current GenLayer documentation lists the Studionet RPC as `https://studio.genlayer.com/api` with chain ID `61999`.

## Verified development test

The deployed contract was exercised in GenLayer Studio with a real GenLayer documentation source:

```text
Claim: GenLayer is an AI-native blockchain that uses decentralized AI-validator consensus to resolve contracts that require judgment.
Source: https://docs.genlayer.com/understand-genlayer-protocol/what-is-genlayer
Result: VERIFIED
```

The Studio transaction history showed finalized deployment, `evaluate`, and `submit_claim` transactions, followed by `get_result()` returning `VERIFIED`.

## Limitations

TrustCheck verifies a claim against the supplied source; it does not prove that the source itself is truthful or authoritative. `UNCERTAIN` is preferred when the source cannot provide enough evidence rather than forcing a binary verdict.

Do not put a private key in this repository. The browser wallet signs transactions locally.
