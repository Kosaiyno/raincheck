# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
import json

def _to_address(val) -> Address:
    """Safely converts input (Address, int big-number from Studio, or hex str) to an Address instance."""
    if isinstance(val, Address):
        return val
    if isinstance(val, int):
        return Address(f"0x{val:040x}")
    s = str(val).strip()
    if s.startswith("0x"):
        return Address(s)
    if s.isdigit():
        return Address(f"0x{int(s):040x}")
    return Address(s)

class RainCheck(gl.Contract):
    """
    RainCheck - Weather-Triggered Parametric Payout Contract (Prototype)
    
    Demonstrates weather condition verification using GenLayer Intelligent Contract execution.
    Validators evaluate external meteorological evidence against predefined threshold criteria
    under the Equivalence Principle (gl.eq_principle.prompt_non_comparative).
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
        aid = u256(agreement_id)
        if aid >= self.agreement_counter:
            return {"error": "Agreement does not exist"}

        return {
            "agreement_id": int(aid),
            "creator": str(self.agreement_creator[aid]),
            "beneficiary": str(self.agreement_beneficiary[aid]),
            "location": self.agreement_location[aid],
            "target_date": self.agreement_date[aid],
            "threshold_mm": int(self.agreement_threshold_mm[aid]),
            "payout_simulated": int(self.agreement_payout_simulated[aid]),
            "status": self.agreement_status[aid],
            "evidence_source": self.agreement_evidence_source[aid],
            "reported_rainfall_mm": int(self.agreement_reported_rainfall_mm[aid]),
            "resolution_notes": self.agreement_resolution_notes[aid],
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
        """
        current_id = self.agreement_counter
        b_addr = _to_address(beneficiary)
        t_mm = u256(threshold_mm)
        p_sim = u256(payout_simulated)

        self.agreement_creator[current_id] = gl.message.sender_address
        self.agreement_beneficiary[current_id] = b_addr
        self.agreement_location[current_id] = location
        self.agreement_date[current_id] = target_date
        self.agreement_threshold_mm[current_id] = t_mm
        self.agreement_payout_simulated[current_id] = p_sim
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
        Uses GenLayer's Equivalence Principle: gl.eq_principle.prompt_non_comparative.
        """
        aid = u256(agreement_id)

        # 1. State Preconditions
        if aid >= self.agreement_counter:
            return "ERROR: Agreement not found"
        
        if self.agreement_status[aid] != "ACTIVE":
            return f"ERROR: Agreement already finalized with status: {self.agreement_status[aid]}"

        location = self.agreement_location[aid]
        target_date = self.agreement_date[aid]
        threshold = int(self.agreement_threshold_mm[aid])

        # 2. Non-deterministic data gathering function for validators
        def get_input() -> str:
            collected = str(evidence_text)
            clean_url = str(evidence_url).strip()
            if len(clean_url) > 0:
                try:
                    resp = gl.nondet.web.get(clean_url)
                    body_text = resp.body.decode("utf-8") if hasattr(resp, "body") else str(resp)
                    collected += f"\n[Web Source Content]:\n{body_text[:2000]}"
                except Exception as e:
                    collected += f"\n[Warning: Web fetch error: {str(e)[:100]}]"

            return (
                f"Target Location: {location}\n"
                f"Target Observation Date: {target_date}\n"
                f"Required Rainfall Threshold: >= {threshold} mm within 24 hours\n\n"
                f"Acquired Weather Evidence:\n{collected}\n"
            )

        # 3. Equivalence Principle Task & Criteria
        task = (
            f"Act as an objective weather auditor. Evaluate the acquired weather evidence for {location} on {target_date}. "
            f"Determine the total recorded rainfall in whole mm. Compare against the threshold of {threshold} mm. "
            f"Output a JSON object with keys: 'decision' ('CONDITION_MET', 'CONDITION_NOT_MET', or 'INCONCLUSIVE'), "
            f"'recorded_rainfall_mm' (integer rounded to nearest mm, 0 if unknown), and 'rationale' (concise 1-sentence explanation)."
        )

        criteria = f"""
            1. The response must be valid JSON with keys: 'decision', 'recorded_rainfall_mm', and 'rationale'.
            2. The 'decision' must be exactly 'CONDITION_MET' (if recorded_rainfall_mm >= {threshold}), 'CONDITION_NOT_MET' (if recorded_rainfall_mm < {threshold}), or 'INCONCLUSIVE'.
            3. The 'recorded_rainfall_mm' must be an integer rounded to the nearest millimeter.
            4. The 'decision' MUST be factually justified by and consistent with the acquired weather evidence in the input.
            5. The 'rationale' must concisely state how the evidence justifies the decision.
        """

        # 4. Execute through GenLayer Equivalence Principle consensus
        raw_result = gl.eq_principle.prompt_non_comparative(
            get_input,
            task=task,
            criteria=criteria,
        )

        # 5. Safe Parsing with Fallback Consensus Guard
        decision = "INCONCLUSIVE"
        recorded_mm = 0
        rationale = "Execution or parsing error occurred"

        try:
            parsed = json.loads(str(raw_result))
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
        self.agreement_evidence_source[aid] = evidence_url if evidence_url else "Direct meteorological report"
        self.agreement_reported_rainfall_mm[aid] = u256(recorded_mm)
        self.agreement_resolution_notes[aid] = rationale

        if decision == "CONDITION_MET":
            self.agreement_status[aid] = "PAID_OUT"
            return f"PAID_OUT: Trigger met ({recorded_mm} mm >= {threshold} mm). Payout simulated to {self.agreement_beneficiary[aid]}."
        elif decision == "CONDITION_NOT_MET":
            self.agreement_status[aid] = "NOT_TRIGGERED"
            return f"NOT_TRIGGERED: Rainfall was {recorded_mm} mm (threshold: {threshold} mm)."
        else:
            return f"INCONCLUSIVE: Evidence could not verify weather for {location} on {target_date}."
