"""Auto‑generated subspecialty keyword mapping from triage spreadsheet."""

SUBSPECIALTY_MAPPING = [
    {
        "subspecialty": "Epileptology",
        "aliases": ["seizures", "spells"],
        "keywords": ["seizure", "convulsion", "blackout", "aura"],
        "common_symptoms": "Seizures, epilepsy, convulsions, staring spells"
    },
    {
        "subspecialty": "Movement Disorders",
        "aliases": ["tremor", "movement issues"],
        "keywords": ["shaking", "tremor", "rigidity", "balance"],
        "common_symptoms": "Parkinsonism, tremors, dystonia, gait instability"
    },
    {
        "subspecialty": "Neuromuscular",
        "aliases": ["tingling", "numbness", "weakness", "sciatica"],
        "keywords": ["tingling", "numbness", "weakness", "fatigue"],
        "common_symptoms": "Muscle weakness, neuropathy, ALS, myasthenia"
    },
    {
        "subspecialty": "Cognitive Neurology",
        "aliases": ["memory loss", "cognitive"],
        "keywords": ["memory", "confused", "dementia", "forget"],
        "common_symptoms": "Dementia, Alzheimer's, confusion, forgetfulness"
    },
    {
        "subspecialty": "Headache Specialist",
        "aliases": ["headaches", "migraines"],
        "keywords": ["headache", "migraine", "throbbing", "aura"],
        "common_symptoms": "Migraine, cluster headache, chronic daily headache"
    },
    {
        "subspecialty": "Neuroimmunology",
        "aliases": [],
        "keywords": ["MS", "autoimmune", "numb", "vision loss"],
        "common_symptoms": "Multiple sclerosis, CNS vasculitis, autoimmune encephalitis"
    },
    {
        "subspecialty": "Stroke / Vascular",
        "aliases": ["speech difficulty", "paralysis", "weakness"],
        "keywords": ["stroke", "TIA", "paralysis", "slurred"],
        "common_symptoms": "Stroke, TIA, sudden weakness/speech loss"
    },
    {
        "subspecialty": "General Neurology",
        "aliases": ["dizziness", "vertigo", "unknown", "headaches", "tingling"],
        "keywords": ["dizzy", "faint", "lightheaded", "unknown"],
        "common_symptoms": "Dizziness, syncope, non-localizing symptoms"
    },
    {
        "subspecialty": "Sleep Neurology",
        "aliases": ["sleep problems"],
        "keywords": ["sleepy", "snoring", "REM", "sleep walking"],
        "common_symptoms": "Narcolepsy, sleep apnea, REM behavior disorder"
    },
    {
        "subspecialty": "Neuro-oncology",
        "aliases": [],
        "keywords": ["mass", "tumor", "glioma", "lesion"],
        "common_symptoms": "Brain tumors, metastases, neoplasms"
    },
    {
        "subspecialty": "Pain / Spine",
        "aliases": ["back pain", "sciatica"],
        "keywords": ["sciatica", "back pain", "disc", "numb leg"],
        "common_symptoms": "Radiculopathy, back pain, nerve root compression"
    },
    {
        "subspecialty": "Pediatric Neurology",
        "aliases": [],
        "keywords": ["developmental", "child", "infant", "autism"],
        "common_symptoms": "Developmental delay, pediatric seizures, genetic syndromes"
    },
    {
        "subspecialty": "Neuro-ophthalmology",
        "aliases": ["vision changes"],
        "keywords": ["vision", "double vision", "sudden vision loss"],
        "common_symptoms": "Visual processing issues, double vision"
    },
    {
        "subspecialty": "Vestibular Neurology",
        "aliases": ["vertigo", "dizziness"],
        "keywords": ["spinning", "imbalance"],
        "common_symptoms": "Inner ear disorders, positional vertigo, imbalance"
    }
]

# Backward compatibility - create the old format for existing code
SUBSPECIALTY_INFO = SUBSPECIALTY_MAPPING

# Create keyword mapping for backward compatibility
SUBSPECIALTY_KEYWORDS = {}
for subspecialty in SUBSPECIALTY_MAPPING:
    # Add keywords
    for keyword in subspecialty["keywords"]:
        SUBSPECIALTY_KEYWORDS[keyword.lower()] = subspecialty["subspecialty"]
    # Add aliases
    for alias in subspecialty["aliases"]:
        SUBSPECIALTY_KEYWORDS[alias.lower()] = subspecialty["subspecialty"]