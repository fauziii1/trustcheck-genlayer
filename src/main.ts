import { createClient } from "genlayer-js";
import { studionet } from "genlayer-js/chains";
import { TransactionStatus } from "genlayer-js/types";
import "./style.css";

declare global {
  interface Window {
    ethereum?: any;
  }
}

const CONTRACT_ADDRESS = (import.meta.env.VITE_CONTRACT_ADDRESS || "PASTE_STUDIONET_CONTRACT_ADDRESS") as `0x${string}`;

const app = document.querySelector<HTMLDivElement>("#app")!;

app.innerHTML = `
  <main class="shell">
    <section class="hero">
      <div class="eyebrow">GENLAYER · STUDIONET</div>
      <h1>TrustCheck</h1>
      <p class="lead">Verify a web-based claim using GenLayer's consensus-based Intelligent Contract execution.</p>
      <div class="hero-actions">
        <button id="connect" class="primary">Connect wallet</button>
        <span id="account" class="account">Not connected</span>
      </div>
    </section>

    <section class="card">
      <div class="section-head">
        <div>
          <h2>Check a claim</h2>
          <p>Provide a claim and an authoritative source URL. The contract evaluates the evidence and stores the consensus result.</p>
        </div>
        <span id="network" class="pill">Studionet</span>
      </div>

      <label for="claim">Claim</label>
      <textarea id="claim" rows="5" placeholder="Example: GenLayer is an AI-native blockchain that uses decentralized AI-validator consensus to resolve contracts that require judgment."></textarea>

      <label for="source">Source URL</label>
      <input id="source" type="url" placeholder="https://docs.genlayer.com/..." />

      <button id="submit" class="primary full">Submit claim to GenLayer</button>
      <div id="status" class="status">Connect your wallet to submit a claim.</div>
    </section>

    <section class="result-card">
      <div>
        <div class="eyebrow">ON-CHAIN RESULT</div>
        <h2 id="result">UNCERTAIN</h2>
        <p id="resultText">The current contract result will appear here after a finalized transaction.</p>
      </div>
      <button id="refresh" class="secondary">Refresh result</button>
    </section>

    <footer>
      <span>Contract</span>
      <code id="contract">${CONTRACT_ADDRESS}</code>
    </footer>
  </main>
`;

const connectButton = document.querySelector<HTMLButtonElement>("#connect")!;
const submitButton = document.querySelector<HTMLButtonElement>("#submit")!;
const refreshButton = document.querySelector<HTMLButtonElement>("#refresh")!;
const accountEl = document.querySelector<HTMLSpanElement>("#account")!;
const statusEl = document.querySelector<HTMLDivElement>("#status")!;
const resultEl = document.querySelector<HTMLHeadingElement>("#result")!;
const resultTextEl = document.querySelector<HTMLParagraphElement>("#resultText")!;
const claimEl = document.querySelector<HTMLTextAreaElement>("#claim")!;
const sourceEl = document.querySelector<HTMLInputElement>("#source")!;

let account: `0x${string}` | undefined;
let writeClient: any;

const readClient = createClient({ chain: studionet });

function setStatus(message: string, kind = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`;
}

function shorten(address: string) {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

async function connectWallet() {
  if (!window.ethereum) {
    setStatus("MetaMask was not detected. Install a browser wallet first.", "error");
    return;
  }

  try {
    const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
    account = accounts[0] as `0x${string}`;
    writeClient = createClient({
      chain: studionet,
      account,
      provider: window.ethereum,
    });

    await writeClient.connect("studionet");
    accountEl.textContent = shorten(account);
    connectButton.textContent = "Wallet connected";
    setStatus("Wallet connected to Studionet. Ready to submit.", "success");
    await refreshResult();
  } catch (error) {
    console.error(error);
    setStatus(error instanceof Error ? error.message : "Wallet connection failed.", "error");
  }
}

async function refreshResult() {
  if (CONTRACT_ADDRESS.startsWith("PASTE_")) {
    setStatus("Set VITE_CONTRACT_ADDRESS before using the app.", "error");
    return;
  }

  try {
    const value = await readClient.readContract({
      address: CONTRACT_ADDRESS,
      functionName: "get_result",
      args: [],
      stateStatus: "accepted",
    });

    const result = String(value).toUpperCase();
    resultEl.textContent = result;
    resultEl.dataset.result = result;
    resultTextEl.textContent =
      result === "VERIFIED"
        ? "The supplied source supports the submitted claim according to the contract's consensus result."
        : result === "REFUTED"
          ? "The supplied source contradicts the submitted claim according to the contract's consensus result."
          : "The available evidence was insufficient or ambiguous. The contract returned UNCERTAIN.";
  } catch (error) {
    console.error(error);
    resultTextEl.textContent = "Unable to read the contract result right now.";
  }
}

async function submitClaim() {
  if (!account || !writeClient) {
    setStatus("Connect your wallet first.", "error");
    return;
  }
  if (CONTRACT_ADDRESS.startsWith("PASTE_")) {
    setStatus("Set VITE_CONTRACT_ADDRESS before submitting.", "error");
    return;
  }

  const claim = claimEl.value.trim();
  const sourceUrl = sourceEl.value.trim();

  if (!claim || !sourceUrl) {
    setStatus("Enter both a claim and a source URL.", "error");
    return;
  }

  submitButton.disabled = true;
  try {
    setStatus("Requesting wallet signature…");

    const txHash = await writeClient.writeContract({
      address: CONTRACT_ADDRESS,
      functionName: "submit_claim",
      args: [claim, sourceUrl],
      value: BigInt(0),
    });

    setStatus(`Transaction submitted: ${txHash.slice(0, 10)}… Waiting for finalization.`);

    const receipt = await readClient.waitForTransactionReceipt({
      hash: txHash,
      status: TransactionStatus.FINALIZED,
    });

    if (receipt.txExecutionResultName && String(receipt.txExecutionResultName).includes("ERROR")) {
      throw new Error("The transaction finalized but contract execution returned an error.");
    }

    setStatus("Transaction FINALIZED. Reading the consensus result…", "success");
    await refreshResult();
  } catch (error) {
    console.error(error);
    setStatus(error instanceof Error ? error.message : "Transaction failed.", "error");
  } finally {
    submitButton.disabled = false;
  }
}

connectButton.addEventListener("click", connectWallet);
submitButton.addEventListener("click", submitClaim);
refreshButton.addEventListener("click", refreshResult);

void refreshResult();
