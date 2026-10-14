# RainCheck — Weather-Triggered Parametric Payouts

> **Prototype Disclaimer**: This is an experimental prototype demonstrating GenLayer Intelligent Contracts and the Equivalence Principle. It is not licensed insurance or a regulated financial product.

RainCheck is a decentralized, weather-triggered parametric agreement smart contract deployed on [GenLayer](https://genlayer.com). It resolves weather agreements without centralized oracles by allowing GenLayer validator committees to retrieve meteorological evidence, interpret conditions using LLMs under the Equivalence Principle, and reach consensus on payouts.

## How It Works

1. **Agreement Creation**: A creator sets a beneficiary, target location (e.g., `Austin, TX`), observation date (`YYYY-MM-DD`), rainfall threshold in mm (e.g., `50`), and simulated payout amount.
2. **Evidence Ingestion**: Meteorological reports (or archived web sources) are submitted to the contract.
3. **Consensus Validation**: Multi-model GenLayer validators evaluate the evidence with strict schema formatting (`CONDITION_MET` vs `CONDITION_NOT_MET`) and integer rounding to prevent consensus splits.
4. **Deterministic Settlement**: The contract transitions state to `PAID_OUT` or `NOT_TRIGGERED` and triggers payout logic.

## Project Structure

- `rain_check.py`: The complete GenLayer Intelligent Contract written in Python.
- `interact.ts`: Client integration script using `genlayer-js`.

## Quickstart

### In GenLayer Studio
1. Open [GenLayer Studio](https://studio.genlayer.com).
2. Create a file named `rain_check.py` and paste the contents of `rain_check.py`.
3. Select **GenLayer Simulator** to test agreement creation and consensus evaluation locally.
4. Switch to **StudioNet (Chain ID: 61999)** and click **Deploy**.
