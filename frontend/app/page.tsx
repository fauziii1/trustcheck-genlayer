"use client";

import { useEffect, useState } from "react";
import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { ExecutionResult, TransactionStatus } from "genlayer-js/types";

const CONTRACT_ADDRESS = process.env.NEXT_PUBLIC_TRUSTCHECK_ADDRESS as `0x${string}` | undefined;

type EthereumProvider = {
  request: (args: { method: string; params?: unknown[] }) => Promise<unknown>;
};

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

export default function Home() {
  const [claim, setClaim] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [result, setResult] = useState("UNCERTAIN");
  const [address, setAddress] = useState("");
  const [txHash, setTxHash] = useState("");
  const [status, setStatus] = useState("Ready");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!CONTRACT_ADDRESS) setStatus("Set NEXT_PUBLIC_TRUSTCHECK_ADDRESS first.");
  }, []);

  async function connectWallet() {
    if (!window.ethereum) throw new Error("No browser wallet detected.");
    const accounts = (await window.ethereum.request({ method: "eth_requestAccounts" })) as string[];
    if (!accounts[0]) throw new Error("No wallet account returned.");
    setAddress(accounts[0]);
    setStatus("Wallet connected");
  }

  async function readResult() {
    if (!CONTRACT_ADDRESS) throw new Error("Contract address is not configured.");
    const client = createClient({ chain: studionet });
    const value = await client.readContract({
      address: CONTRACT_ADDRESS,
      functionName: "get_result",
      args: [],
    });
    setResult(String(value));
  }

  async function submitClaim() {
    if (!CONTRACT_ADDRESS) throw new Error("Contract address is not configured.");
    if (!address) await connectWallet();
    if (!window.ethereum) throw new Error("No browser wallet detected.");

    const accounts = (await window.ethereum.request({ method: "eth_accounts" })) as string[];
    const walletAddress = (accounts[0] || address) as `0x${string}`;
    const client = createClient({
      chain: studionet,
      account: walletAddress,
      provider: window.ethereum as any,
    });

    await client.connect("studionet");
    setStatus("Sending transaction…");
    const hash = await client.writeContract({
      address: CONTRACT_ADDRESS,
      functionName: "submit_claim",
      args: [claim, sourceUrl],
      value: BigInt(0),
    });
    setTxHash(hash);
    setStatus("Transaction submitted. Waiting for finalization…");

    const receipt = await client.waitForTransactionReceipt({
      hash,
      status: TransactionStatus.FINALIZED,
    });

    if (receipt.txExecutionResultName !== ExecutionResult.FINISHED_WITH_RETURN) {
      throw new Error(`Transaction finalized but execution failed: ${receipt.txExecutionResultName}`);
    }

    setStatus("Finalized successfully.");
    await readResult();
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    try {
      await submitClaim();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : String(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ maxWidth: 760, margin: "40px auto", padding: 24, fontFamily: "system-ui" }}>
      <h1>TrustCheck</h1>
      <p>Verify an online claim using GenLayer web access, LLM evaluation, and validator consensus.</p>

      <form onSubmit={handleSubmit} style={{ display: "grid", gap: 12 }}>
        <label>
          Claim
          <textarea value={claim} onChange={(e) => setClaim(e.target.value)} required rows={5} style={{ width: "100%" }} />
        </label>
        <label>
          Source URL
          <input value={sourceUrl} onChange={(e) => setSourceUrl(e.target.value)} type="url" required style={{ width: "100%" }} />
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          <button type="button" onClick={connectWallet}>Connect wallet</button>
          <button type="submit" disabled={busy || !claim || !sourceUrl}>
            {busy ? "Processing…" : "Verify claim"}
          </button>
          <button type="button" onClick={() => readResult().catch((e) => setStatus(e.message))}>Refresh result</button>
        </div>
      </form>

      <section style={{ marginTop: 28 }}>
        <strong>Result: {result}</strong>
        <p>Status: {status}</p>
        {address && <p>Wallet: {address}</p>}
        {txHash && <p>Transaction: {txHash}</p>}
      </section>
    </main>
  );
}
