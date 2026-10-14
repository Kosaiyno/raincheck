# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

class RainCheck(gl.Contract):
    """
    RainCheck - Weather-Triggered Parametric Payout Contract (Prototype)
    
    Demonstrates weather condition verification using GenLayer Intelligent Contract execution.
    Validators evaluate external meteorological evidence against predefined threshold criteria
    under the Equivalence Principle to reach consensus on payout triggering.
    """
    owner: Address
    agreement_counter: u256

    # Agreement Storage (Indexed by agreement_id)
    agreement_creator: TreeMap[u256, Address]
    agreement_beneficiary: TreeMap[u256, Address]
    agreement_location: TreeMap[u256, str]
    agreement_date: TreeMap[u256, str]             # e.g., "YYYY-MM-DD"
    agreement_threshold_mm: TreeMap[u256, u256]    # Integer mm of precipitation
    agreement_payout_simulated: TreeMap[u256, u256]# Simulated payout amount (in cents or tokens)
    agreement_status: TreeMap[u256, str]           # "ACTIVE", "PAID_OUT", "NOT_TRIGGERED", "VOID"
    
    # Evidence & Settlement Records
    agreement_evidence_source: TreeMap[u256, str]  # URL or data source description
    agreement_reported_rainfall_mm: TreeMap[u256, u256]
    agreement_resolution_notes: TreeMap[u256, str]

    def __init__(self):
        self.owner = gl.message.sender_address
        self.agreement_counter = u256(0)

    # =========================================================================
    # VIEW METHODS (Read-Only, Zero-Gas)
    # =========================================================================

    @gl.public.view
    def get_total_agreements(self) -> u256:
        """Returns the total number of agreements created."""
        return self.agreement_counter

    @gl.public.view
    def get_agreement(self, agreement_id: u256) -> dict:
        """Retrieves complete details for a given agreement ID."""
        if agreement_id >= self.agreement_counter:
            return {"error": "Agreement does not exist"}

        return {
            "agreement_id": int(agreement_id),
            "creator": str(self.agreement_creator[agreement_id]),
            "beneficiary": str(self.agreement_beneficiary[agreement_id]),
            "location": self.agreement_location[agreement_id],
            "target_date": self.agreement_date[agreement_id],
            "threshold_mm": int(self.agreement_threshold_mm[agreement_id]),
            "payout_simulated": int(self.agreement_payout_simulated[agreement_id]),
            "status": self.agreement_status[agreement_id],
            "evidence_source": self.agreement_evidence_source[agreement_id],
            "reported_rainfall_mm": int(self.agreement_reported_rainfall_mm[agreement_id]),
            "resolution_notes": self.agreement_resolution_notes[agreement_id],
            "is_prototype": True
        }

    # =========================================================================
    # WRITE METHODS (State-Changing, Requires Validator Committee Consensus)
    # =========================================================================

    @gl.public.write
    def create_agreement(
        self,
        beneficiary: Address,
        location: str,
        target_date: str,
        threshold_mm: u256,
        payout_simulated: u256
    ) -> u256:
        """
        Creates a new weather trigger agreement.
        
        :param beneficiary: Address that receives simulated payout if threshold is met.
        :param location: Target city / station (e.g., "Austin, TX" or "Station USW00013904").
        :param target_date: The observation date ("YYYY-MM-DD").
        :param threshold_mm: Rainfall threshold in millimeters (e.g. 50 mm).
        :param payout_simulated: Simulated settlement value (e.g. 1000 for $10.00).
        """
        current_id = self.agreement_counter

        self.agreement_creator[current_id] = gl.message.sender_address
        self.agreement_beneficiary[current_id] = beneficiary
        self.agreement_location[current_id] = location
        self.agreement_date[current_id] = target_date
        self.agreement_threshold_mm[current_id] = threshold_mm
        self.agreement_payout_simulated[current_id] = payout_simulated
        self.agreement_status[current_id] = "ACTIVE"
        
        self.agreement_evidence_source[current_id] = ""
        self.agreement_reported_rainfall_mm[current_id] = u256(0)
        self.agreement_resolution_notes[current_id] = ""

        self.agreement_counter = current_id + u256(1)
        return current_id

    @gl.public.write
    def evaluate_and_settle(
        self,
        agreement_id: u256,
        evidence_url: str,
        evidence_text: str
    ) -> str:
        """
        Evaluates weather evidence against the agreement threshold and triggers payout.
        
        Validators execute this method independently:
        1. If evidence_url is provided, validators fetch web content deterministically.
        2. LLM extracts observed precipitation and classifies the condition categorically.
        3. Agreement state updates to 'PAID_OUT' or 'NOT_TRIGGERED'.
        """
        # 1. State Preconditions
        if agreement_id >= self.agreement_counter:
            return "ERROR: Agreement not found"
        
        if self.agreement_status[agreement_id] != "ACTIVE":
            return f"ERROR: Agreement already finalized with status: {self.agreement_status[agreement_id]}"

        location = self.agreement_location[agreement_id]
        target_date = self.agreement_date[agreement_id]
        threshold = int(self.agreement_threshold_mm[agreement_id])

        # 2. Gather Evidence (Web page or supplied report text)
        collected_evidence = evidence_text
        if len(evidence_url.strip()) > 0:
            try:
                # Fetch immutable/durable archive or disclosure page
                web_content = gl.get_web_page(evidence_url)
                # Keep prompt payload bounded
                collected_evidence += f"\n[Web Source Content]:\n{web_content[:2500]}"
            except Exception:
                collected_evidence += "\n[Warning: Web source fetch failed or timed out]"

        # 3. Equivalence Principle Compliant Prompting
        # Strict categorical decision & integer extraction to ensure multi-model validator agreement
        prompt = f"""
You are an objective weather auditor validating a parametric weather insurance trigger.

AGREEMENT TERMS:
- Target Location: {location}
- Target Date: {target_date}
- Required Rainfall Threshold: >= {threshold} mm within 24h

EVIDENCE PROVIDED:
{collected_evidence}

TASK:
1. Determine the official total rainfall (precipitation) in mm recorded for {location} on {target_date}.
2. Compare the recorded rainfall against the threshold of {threshold} mm.
3. Make a binary decision:
   - "CONDITION_MET" if rainfall >= {threshold} mm.
   - "CONDITION_NOT_MET" if rainfall < {threshold} mm.
   - "INCONCLUSIVE" if no credible evidence exists for this location and date.

Respond ONLY with valid raw JSON matching this schema:
{{
  "decision": "CONDITION_MET" | "CONDITION_NOT_MET" | "INCONCLUSIVE",
  "recorded_rainfall_mm": <integer rounded to nearest whole mm, 0 if unknown>,
  "rationale": "<brief 1-sentence explanation of finding>"
}}
"""

        # 4. Invoke LLM under Consensus Schema
        raw_response = gl.call_llm(prompt=prompt, response_format="json")

        # 5. Safe Parsing with Fallback Consensus Guard
        decision = "INCONCLUSIVE"
        recorded_mm = 0
        rationale = "Execution or parsing error occurred"

        try:
            parsed = json.loads(raw_response)
            parsed_decision = str(parsed.get("decision", "")).strip().upper()
            if parsed_decision in ["CONDITION_MET", "CONDITION_NOT_MET", "INCONCLUSIVE"]:
                decision = parsed_decision
            
            raw_mm = parsed.get("recorded_rainfall_mm", 0)
            if isinstance(raw_mm, (int, float)):
                recorded_mm = max(0, int(round(raw_mm)))
            
            rationale = str(parsed.get("rationale", "No rationale supplied"))[:250]
        except Exception as e:
            rationale = f"Parsing fallback: {str(e)[:100]}"

        # 6. Deterministic Settlement & State Transition
        self.agreement_evidence_source[agreement_id] = evidence_url if evidence_url else "Direct text report"
        self.agreement_reported_rainfall_mm[agreement_id] = u256(recorded_mm)
        self.agreement_resolution_notes[agreement_id] = rationale

        if decision == "CONDITION_MET":
            # Condition satisfied: Trigger simulated payout
            self.agreement_status[agreement_id] = "PAID_OUT"
            return f"PAID_OUT: Trigger met ({recorded_mm} mm >= {threshold} mm). Payout simulated to {self.agreement_beneficiary[agreement_id]}."
        elif decision == "CONDITION_NOT_MET":
            # Condition not satisfied: No payout triggered
            self.agreement_status[agreement_id] = "NOT_TRIGGERED"
            return f"NOT_TRIGGERED: Rainfall was {recorded_mm} mm (threshold: {threshold} mm)."
        else:
            # Evidence insufficient: Retain ACTIVE for resubmission or manual void
            return f"INCONCLUSIVE: Evidence could not verify weather for {location} on {target_date}."
