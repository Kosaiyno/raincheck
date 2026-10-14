import { createClient, createAccount, chains } from 'genlayer-js';

// Configuration: Replace with your StudioNet account private key and deployed contract address
const PRIVATE_KEY = process.env.GENLAYER_PRIVATE_KEY || '0xYOUR_PRIVATE_KEY';
const CONTRACT_ADDRESS = process.env.CONTRACT_ADDRESS || '0xYOUR_DEPLOYED_CONTRACT_ADDRESS';

async function main() {
  const account = createAccount(PRIVATE_KEY);
  const client = createClient({
    chain: chains.studionet,
    account
  });

  console.log('--- 1. Creating Weather Agreement ---');
  // Beneficiary address, Location, Target Date, Rainfall Threshold in mm (e.g. 50), Simulated Payout (e.g. $10.00 -> 1000)
  const createTx = await client.writeContract({
    address: CONTRACT_ADDRESS,
    functionName: 'create_agreement',
    args: [
      account.address,            // Beneficiary
      'Austin, TX',               // Location
      '2026-10-12',               // Target date
      50n,                        // 50 mm threshold
      1000n                       // 1000 cents ($10)
    ],
    value: 0n,
    leaderOnly: false
  });

  const createReceipt = await client.waitForTransactionReceipt({ hash: createTx });
  console.log('Agreement created! Status:', createReceipt.status_name);

  // Retrieve agreement 0
  const agreement = await client.readContract({
    address: CONTRACT_ADDRESS,
    functionName: 'get_agreement',
    args: [0n]
  });
  console.log('Agreement #0 Details:', agreement);

  console.log('--- 2. Evaluating Weather Evidence ---');
  // Pass archive URL or meteorological report evidence
  const evaluateTx = await client.writeContract({
    address: CONTRACT_ADDRESS,
    functionName: 'evaluate_and_settle',
    args: [
      0n, // Agreement ID
      '', // Evidence URL (leave empty or use permanent archive link)
      'National Weather Service Austin Station USW00013904 reported 64.2 mm total precipitation on 2026-10-12 due to a localized severe storm.'
    ],
    value: 0n,
    leaderOnly: false
  });

  const evalReceipt = await client.waitForTransactionReceipt({ hash: evaluateTx });
  console.log('Evaluation consensus status:', evalReceipt.status_name);

  // Read updated state
  const updated = await client.readContract({
    address: CONTRACT_ADDRESS,
    functionName: 'get_agreement',
    args: [0n]
  });
  console.log('Settlement Result:', updated);
}

main().catch(console.error);
