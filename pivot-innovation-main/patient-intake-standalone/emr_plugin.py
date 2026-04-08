import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class UrgencyLevel(Enum):
    ROUTINE = "Routine"
    URGENT = "Urgent"
    EMERGENCY = "Emergency"

# REMOVED Subspecialty Enum

@dataclass
class PatientDemographics:
    name: str
    dob: str
    contact: str
    insurance: str
    referring_physician: str
    reason_for_visit: str
    symptom_onset: str
    urgency: UrgencyLevel

@dataclass
class SymptomAssessment:
    symptom: str
    present: bool
    details: Optional[str] = None
    red_flags: List[str] = None
    follow_up_questions: List[str] = None

@dataclass
class TriageSummary:
    patient: PatientDemographics
    symptoms: List[SymptomAssessment]
    red_flags_found: List[str]
    recommended_subspecialty: str  # Now a string
    urgency_level: UrgencyLevel
    triage_notes: str
    recommended_action: str
    created_at: str

class EMRPlugin:
    def __init__(self):
        self.conversation_data = {}
        self.symptom_mapping = {
            "headaches": "Headaches",
            "seizures": "Seizures/Epilepsy",
            "weakness_paralysis": "Weakness/Paralysis",
            "tingling_numbness": "Tingling/Numbness",
            "vision_changes": "Vision Changes",
            "speech_problems": "Speech Problems",
            "balance_coordination": "Balance/Coordination",
            "memory_cognitive": "Memory/Cognitive Issues",
            "tremor_movement": "Tremor/Movement Disorders",
            "pain": "Pain Syndromes"
        }
        # Removed self.subspecialty_rules

    def process_conversation(self, conversation_log: str) -> TriageSummary:
        """Process conversation log and generate triage summary"""
        # Parse conversation data
        self._parse_conversation(conversation_log)
        
        # Extract patient demographics
        patient = self._extract_demographics()
        
        # Extract symptom assessments
        symptoms = self._extract_symptoms()
        
        # Identify red flags
        red_flags = self._identify_red_flags(symptoms)
        
        # Use the recommended subspecialty string from the context
        recommended_subspecialty = self.conversation_data.get("recommended_subspecialty", "General Neurology")
        
        # Generate triage notes
        triage_notes = self._generate_triage_notes(patient, symptoms, red_flags)
        
        # Determine recommended action
        recommended_action = self._determine_action(patient.urgency, red_flags)
        
        # Check if conversation was completed
        conversation_completed = len(symptoms) >= 5  # At least 5 symptoms screened
        
        return TriageSummary(
            patient=patient,
            symptoms=symptoms,
            red_flags_found=red_flags,
            recommended_subspecialty=recommended_subspecialty,  # Now a string
            urgency_level=patient.urgency,
            triage_notes=triage_notes,
            recommended_action=recommended_action,
            created_at=datetime.now().isoformat()
        )

    def _parse_conversation(self, conversation_log: str):
        """Parse conversation log to extract structured data"""
        try:
            # Parse the conversation data string from the bot
            import ast
            self.conversation_data = ast.literal_eval(conversation_log)
            print(f"DEBUG: Parsed conversation data: {self.conversation_data}")
        except Exception as e:
            print(f"DEBUG: Error parsing conversation data: {e}")
            # Fallback to empty data
            self.conversation_data = {
                "demographics": {},
                "symptoms": {},
                "red_flags": []
            }

    def _extract_demographics(self) -> PatientDemographics:
        """Extract patient demographics from conversation"""
        # Extract from parsed conversation data
        demographics = self.conversation_data.get("demographics", {})
        
        # Get urgency level
        urgency_str = demographics.get("urgency", "Routine")
        try:
            urgency = UrgencyLevel(urgency_str)
        except ValueError:
            urgency = UrgencyLevel.ROUTINE
        
        return PatientDemographics(
            name=demographics.get("name", "Unknown"),
            dob=demographics.get("dob", "Unknown"),
            contact=demographics.get("contact", "Not provided"),
            insurance=demographics.get("insurance", "Not provided"),
            referring_physician=demographics.get("referring_physician", "Not specified"),
            reason_for_visit=demographics.get("reason_for_visit", "Not specified"),
            symptom_onset=demographics.get("symptom_onset", "Not specified"),
            urgency=urgency
        )

    def _extract_symptoms(self) -> List[SymptomAssessment]:
        """Extract symptom assessments from conversation"""
        symptoms = []
        
        # Get symptoms from parsed conversation data
        symptom_data = self.conversation_data.get("symptoms", {})
        
        # Map symptom keys to readable names
        symptom_mapping = {
            "headaches_migraines": "Headaches/Migraines",
            "seizures_spells": "Seizures/Epilepsy",
            "weakness_paralysis": "Weakness/Paralysis",
            "tingling_numbness": "Tingling/Numbness",
            "movement_issues_tremors": "Movement Issues/Tremors",
            "memory_loss_cognitive": "Memory Loss/Cognitive Issues",
            "vision_changes": "Vision Changes",
            "speech_difficulty": "Speech Difficulty",
            "back_pain_sciatica": "Back Pain/Sciatica",
            "sleep_problems": "Sleep Problems",
            "dizziness_vertigo": "Dizziness/Vertigo"
        }
        
        for symptom_key, symptom_info in symptom_data.items():
            if isinstance(symptom_info, dict):
                present = symptom_info.get("yes", False)
                symptom_name = symptom_mapping.get(symptom_key, symptom_key.replace("_", " ").title())
                
                # Build details from follow-ups
                details = []
                if present:
                    details.append("Patient reported this symptom")
                    if "followups" in symptom_info:
                        details.extend(symptom_info["followups"])
                else:
                    details.append("Patient denied this symptom")
                
                symptoms.append(SymptomAssessment(
                    symptom=symptom_name,
                    present=present,
                    details="; ".join(details) if details else "No details available",
                    follow_up_questions=symptom_info.get("followups", []) if present else None
                ))
        
        return symptoms

    def _identify_red_flags(self, symptoms: List[SymptomAssessment]) -> List[str]:
        """Identify red flags from symptoms"""
        red_flags = []
        
        # Get red flags from conversation data
        conversation_red_flags = self.conversation_data.get("red_flags", [])
        red_flags.extend(conversation_red_flags)
        
        # Also check symptoms for red flags
        for symptom in symptoms:
            if symptom.symptom == "Seizures/Epilepsy" and symptom.present:
                # Check for red flags in seizure follow-ups
                if "first-time" in symptom.details.lower():
                    red_flags.append("First-time seizure - requires urgent evaluation")
                if "loss of consciousness" in symptom.details.lower():
                    red_flags.append("Seizure with loss of consciousness")
            elif symptom.symptom == "Weakness/Paralysis" and symptom.present:
                if "sudden" in symptom.details.lower():
                    red_flags.append("Sudden weakness - possible stroke")
            elif symptom.symptom == "Vision Changes" and symptom.present:
                if "sudden" in symptom.details.lower() or "loss" in symptom.details.lower():
                    red_flags.append("Sudden vision changes - requires urgent evaluation")
                    
        return red_flags

    # REMOVED _determine_subspecialty

    def _generate_triage_notes(self, patient: PatientDemographics, 
                              symptoms: List[SymptomAssessment], 
                              red_flags: List[str]) -> str:
        """Generate triage notes"""
        notes = f"""
TRIAGE SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}

PATIENT: {patient.name} (DOB: {patient.dob})
CONTACT: {patient.contact}
REFERRING: {patient.referring_physician}
URGENCY: {patient.urgency.value}

CHIEF COMPLAINT: {patient.reason_for_visit}
SYMPTOM ONSET: {patient.symptom_onset}

SYMPTOM ASSESSMENT:
"""
        
        for symptom in symptoms:
            status = "POSITIVE" if symptom.present else "NEGATIVE"
            notes += f"- {symptom.symptom}: {status}\n"
            if symptom.details:
                notes += f"  Details: {symptom.details}\n"
        
        if red_flags:
            notes += f"\nRED FLAGS IDENTIFIED:\n"
            for flag in red_flags:
                notes += f"- {flag}\n"
        else:
            notes += f"\nNo red flags identified.\n"
        
        return notes

    def _determine_action(self, urgency: UrgencyLevel, red_flags: List[str]) -> str:
        """Determine recommended action based on urgency and red flags"""
        if red_flags:
            return "URGENT: Patient has red flags - schedule urgent appointment or refer to emergency care"
        elif urgency == UrgencyLevel.EMERGENCY:
            return "EMERGENCY: Immediate medical attention required"
        elif urgency == UrgencyLevel.URGENT:
            return "URGENT: Schedule appointment within 1-2 weeks"
        else:
            return "ROUTINE: Schedule routine appointment"

    def generate_emr_summary(self, triage_summary: TriageSummary) -> Dict[str, Any]:
        """Generate EMR-compatible summary"""
        return {
            "summary_type": "neurology_triage",
            "timestamp": triage_summary.created_at,
            "patient_info": asdict(triage_summary.patient),
            "symptoms": [asdict(s) for s in triage_summary.symptoms],
            "red_flags": triage_summary.red_flags_found,
            "subspecialty": triage_summary.recommended_subspecialty,  # Use string
            "urgency": triage_summary.urgency_level.value,
            "triage_notes": triage_summary.triage_notes,
            "recommended_action": triage_summary.recommended_action,
            "form_completion": self._generate_form_completion(triage_summary)
        }

    def _generate_form_completion(self, triage_summary: TriageSummary) -> Dict[str, Any]:
        """Generate completed triage form"""
        return {
            "form_type": "Neurology Triage Form",
            "completion_date": triage_summary.created_at,
            "sections": {
                "demographics": {
                    "name": triage_summary.patient.name,
                    "dob": triage_summary.patient.dob,
                    "contact": triage_summary.patient.contact,
                    "insurance": triage_summary.patient.insurance,
                    "referring_physician": triage_summary.patient.referring_physician
                },
                "chief_complaint": triage_summary.patient.reason_for_visit,
                "symptom_onset": triage_summary.patient.symptom_onset,
                "urgency_level": triage_summary.urgency_level.value,
                "symptom_screening": {
                    symptom.symptom: {
                        "present": symptom.present,
                        "details": symptom.details
                    } for symptom in triage_summary.symptoms
                },
                "red_flags": triage_summary.red_flags_found,
                "subspecialty_recommendation": triage_summary.recommended_subspecialty,  # Use string
                "triage_notes": triage_summary.triage_notes,
                "recommended_action": triage_summary.recommended_action
            }
        }

    def export_to_json(self, triage_summary: TriageSummary, filename: str = None):
        """Export triage summary to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"triage_summary_{timestamp}.json"
        
        emr_data = self.generate_emr_summary(triage_summary)
        
        with open(filename, 'w') as f:
            json.dump(emr_data, f, indent=2, default=str)
        
        print(f"Triage summary exported to: {filename}")
        return filename

    def print_summary(self, triage_summary: TriageSummary):
        """Print formatted triage summary"""
        print("=" * 60)
        print("NEUROLOGY CLINIC TRIAGE SUMMARY")
        print("=" * 60)
        print(f"Patient: {triage_summary.patient.name}")
        print(f"DOB: {triage_summary.patient.dob}")
        print(f"Contact: {triage_summary.patient.contact}")
        print(f"Urgency: {triage_summary.urgency_level.value}")
        print(f"Subspecialty: {triage_summary.recommended_subspecialty}")  # Use string
        print(f"Status: {'COMPLETED' if len(triage_summary.symptoms) >= 5 else 'INCOMPLETE'}")
        print()
        
        print("SYMPTOMS:")
        for symptom in triage_summary.symptoms:
            status = "✓" if symptom.present else "✗"
            print(f"  {status} {symptom.symptom}")
            if symptom.details:
                print(f"    Details: {symptom.details}")
        
        if triage_summary.red_flags_found:
            print("\nRED FLAGS:")
            for flag in triage_summary.red_flags_found:
                print(f"  ⚠️  {flag}")
        
        print(f"\nRECOMMENDED ACTION: {triage_summary.recommended_action}")
        
        if len(triage_summary.symptoms) < 5:
            print(f"\n⚠️  NOTE: Conversation was incomplete. Only {len(triage_summary.symptoms)} symptoms were screened.")
        
        print("=" * 60)

# Example usage
if __name__ == "__main__":
    plugin = EMRPlugin()
    
    # Process conversation (this would be the actual conversation log)
    conversation_log = "Sample conversation log..."
    triage_summary = plugin.process_conversation(conversation_log)
    
    # Print summary
    plugin.print_summary(triage_summary)
    
    # Export to JSON
    plugin.export_to_json(triage_summary) 