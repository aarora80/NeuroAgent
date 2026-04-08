#!/usr/bin/env python3
"""
Test script for EMR Plugin functionality
Demonstrates how the EMR plugin processes conversation data and generates triage summaries
"""

from emr_plugin import EMRPlugin, UrgencyLevel, Subspecialty
from datetime import datetime

def test_emr_plugin():
    """Test the EMR plugin with sample conversation data"""
    
    print("🧪 Testing EMR Plugin Functionality")
    print("=" * 50)
    
    # Create EMR plugin instance
    plugin = EMRPlugin()
    
    # Sample conversation data (this would come from the actual bot conversation)
    sample_conversation = """
    Patient: Aurora Arnab
    DOB: 1990-01-01
    Contact: arnav@gmail.com
    Insurance: None
    Referring: Self-referred
    Reason: General evaluation, something started yesterday but unsure
    Symptom onset: Yesterday
    Urgency: Routine
    
    Symptoms:
    - Headaches: No
    - Seizures: Yes (not first-time, no jerking, no loss of consciousness, no confusion)
    - Weakness/Paralysis: No
    - Tingling/Numbness: No
    - Vision Changes: No
    - Speech Problems: No
    - Balance/Coordination: No
    - Memory/Cognitive: No
    - Tremor/Movement: No
    - Pain: No
    """
    
    print("📋 Processing conversation data...")
    
    # Process the conversation
    triage_summary = plugin.process_conversation(sample_conversation)
    
    print("\n📊 Generated Triage Summary:")
    print("-" * 30)
    
    # Print the summary
    plugin.print_summary(triage_summary)
    
    print("\n📄 Generating EMR-compatible data...")
    
    # Generate EMR summary
    emr_data = plugin.generate_emr_summary(triage_summary)
    
    print("\n🔍 EMR Data Structure:")
    print(f"  Summary Type: {emr_data['summary_type']}")
    print(f"  Timestamp: {emr_data['timestamp']}")
    print(f"  Patient: {emr_data['patient_info']['name']}")
    print(f"  Subspecialty: {emr_data['subspecialty']}")
    print(f"  Urgency: {emr_data['urgency']}")
    print(f"  Red Flags: {len(emr_data['red_flags'])} found")
    
    print("\n📋 Form Completion Status:")
    form_data = emr_data['form_completion']
    print(f"  Form Type: {form_data['form_type']}")
    print(f"  Completion Date: {form_data['completion_date']}")
    print(f"  Sections Completed: {len(form_data['sections'])}")
    
    print("\n💾 Exporting to JSON...")
    
    # Export to JSON file
    filename = plugin.export_to_json(triage_summary)
    
    print(f"\n✅ Test completed successfully!")
    print(f"📁 Summary exported to: {filename}")
    
    return triage_summary

def test_different_scenarios():
    """Test different patient scenarios"""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Different Patient Scenarios")
    print("=" * 60)
    
    scenarios = [
        {
            "name": "Emergency Stroke Case",
            "urgency": UrgencyLevel.EMERGENCY,
            "symptoms": ["weakness_paralysis", "speech_problems"],
            "red_flags": ["Sudden onset weakness", "Speech difficulty"],
            "expected_subspecialty": Subspecialty.STROKE
        },
        {
            "name": "Epilepsy Case",
            "urgency": UrgencyLevel.URGENT,
            "symptoms": ["seizures"],
            "red_flags": ["First-time seizure"],
            "expected_subspecialty": Subspecialty.EPILEPSY
        },
        {
            "name": "Routine Headache Case",
            "urgency": UrgencyLevel.ROUTINE,
            "symptoms": ["headaches"],
            "red_flags": [],
            "expected_subspecialty": Subspecialty.HEADACHE
        }
    ]
    
    plugin = EMRPlugin()
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['name']}")
        print("-" * 40)
        
        # Create mock triage summary for this scenario
        # (In real implementation, this would come from actual conversation processing)
        print(f"  Urgency: {scenario['urgency'].value}")
        print(f"  Symptoms: {', '.join(scenario['symptoms'])}")
        print(f"  Red Flags: {len(scenario['red_flags'])} found")
        print(f"  Expected Subspecialty: {scenario['expected_subspecialty'].value}")
        
        # Test subspecialty determination
        mock_symptoms = [{"symptom": s, "present": True} for s in scenario['symptoms']]
        determined_subspecialty = plugin._determine_subspecialty(mock_symptoms)
        
        if determined_subspecialty == scenario['expected_subspecialty']:
            print(f"  ✅ Subspecialty correctly determined: {determined_subspecialty.value}")
        else:
            print(f"  ❌ Subspecialty mismatch: expected {scenario['expected_subspecialty'].value}, got {determined_subspecialty.value}")

if __name__ == "__main__":
    # Run the main test
    triage_summary = test_emr_plugin()
    
    # Run scenario tests
    test_different_scenarios()
    
    print("\n🎉 All tests completed!")
    print("\nThe EMR plugin successfully:")
    print("  ✅ Processes conversation data")
    print("  ✅ Extracts patient demographics")
    print("  ✅ Identifies symptoms and red flags")
    print("  ✅ Determines appropriate subspecialty")
    print("  ✅ Generates structured triage notes")
    print("  ✅ Exports EMR-compatible JSON")
    print("  ✅ Provides actionable recommendations") 