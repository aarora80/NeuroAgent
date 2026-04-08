"""
Neurology triage constants extracted from Neurology_Clinic_Triage_Form.pdf
Feel free to import everything from this file:

    from neurology_triage_schema import (
        DEMO_QUESTIONS, SYMPTOM_FLOW,
        RED_FLAG_KEYWORDS, SUBSPECIALTY_MAP
    )
"""

# ---------------------------------------------------------------------------
# Demographics (ordered)
# ---------------------------------------------------------------------------

DEMO_QUESTIONS = [
    ("name", "May I have your full name?"),
    ("dob", "What is your date of birth?"),
    ("contact", "What is the best phone number to reach you?"),
    ("insurance", "Which insurance provider do you have?"),
    ("referring_physician", "Who is your referring physician, if any?"),
    ("reason_for_visit", "What is the main concern for today's visit?"),
    ("symptom_onset", "When did your symptoms start and how long have they been present?"),
    ("urgency", "Would you describe this concern as routine, urgent, or an emergency?"),
]

# ---------------------------------------------------------------------------
# Symptom flow: (key, yes/no screening question, follow‑up questions list)
# ---------------------------------------------------------------------------

SYMPTOM_FLOW = [
    ("headaches_migraines", "Do you have headaches or migraines?", [
        "How frequent and severe are your headaches or migraines?",
        "Do you experience any aura or nausea with them?",
        ("Have you experienced a sudden severe headache or the worst headache of your life?", "sudden_severe_headache")
    ]),
    ("seizures_spells", "Have you experienced seizures or spells?", [
        "Did you notice any jerking movements?",
        "Were you confused afterwards?",
        ("Did you lose consciousness during the event?", "loss_of_consciousness")
    ]),
    ("weakness_paralysis", "Have you had any weakness or paralysis?", [
        "Was the weakness on one side or both sides of your body?",
        "Did you notice any facial droop?",
        ("Did the weakness start suddenly?", "sudden_weakness")
    ]),
    ("tingling_numbness", "Have you had tingling or numbness?", [
        "Where do you feel the tingling or numbness?",
        "Is it symmetric on both sides or only one side?",
        ("Did the numbness start suddenly?", "sudden_weakness")
    ]),
    ("movement_issues_tremors", "Do you have movement issues or tremors?", [
        "Do you experience shaking while at rest?",
        "Do you have an unsteady gait when walking?",
        ("Are the symptoms rapidly worsening?", "rapidly_worsening")
    ]),
    ("memory_loss_cognitive", "Have you experienced memory loss or cognitive issues?", [
        "Has it been progressively worsening?",
        "Is it affecting your daily life or activities?",
        ("Are the symptoms rapidly worsening?", "rapidly_worsening")
    ]),
    ("vision_changes", "Have you had any vision changes?", [
        "Was there a sudden loss of vision?",
        "Do you experience double vision?",
        ("Was your vision loss sudden or accompanied by slurred speech?", "slurred_speech_or_vision_loss")
    ]),
    ("speech_difficulty", "Have you had any speech difficulty?", [
        "Do you have trouble forming words?",
        "Is your speech slurred?",
        ("Was the speech difficulty sudden or accompanied by vision loss?", "slurred_speech_or_vision_loss")
    ]),
    ("back_pain_sciatica", "Do you have back pain or sciatica?", [
        "Is the pain radiating down your leg?",
        ("Have you noticed any bowel or bladder changes?", "bowel_bladder_change")
    ]),
    ("sleep_problems", "Do you have sleep problems?", [
        "Do you experience excessive daytime sleepiness?",
        "Do you snore loudly at night?",
        ("Are the symptoms rapidly worsening?", "rapidly_worsening")
    ]),
    ("dizziness_vertigo", "Have you experienced dizziness or vertigo?", [
        "Do you feel a spinning sensation?",
        "Do you experience imbalance while standing or walking?",
        ("Was there any loss of consciousness or blacking out?", "loss_of_consciousness")
    ]),
]

# ---------------------------------------------------------------------------
# Red‑flag keywords map -> canonical flag label
# ---------------------------------------------------------------------------

RED_FLAG_KEYWORDS = {}  # Red flags are now handled directly in SYMPTOM_FLOW

# ---------------------------------------------------------------------------
# Subspecialty routing map
# ---------------------------------------------------------------------------

SUBSPECIALTY_MAP = {
    "headaches_migraines": "Headache Specialist / General Neurology",
    "seizures_spells": "Epilepsy Specialist",
    "weakness_paralysis": "Stroke / General Neurology",
    "tingling_numbness": "Neuromuscular / General Neurology",
    "movement_issues_tremors": "Movement Disorders",
    "memory_loss_cognitive": "Cognitive Neurology",
    "vision_changes": "Neuro-ophthalmology",
    "speech_difficulty": "Stroke / General Neurology",
    "back_pain_sciatica": "Spine / Neuromuscular",
    "sleep_problems": "Sleep Neurology",
    "dizziness_vertigo": "General / Vestibular Neurology",
}
