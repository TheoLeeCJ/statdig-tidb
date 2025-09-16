import random
import string

# Analyze state constants
ANALYZE_STATE_UPLOADED = 0  # freshly uploaded, not extracted
ANALYZE_STATE_EXTRACTING = 1  # extracting
ANALYZE_STATE_EXTRACTED = 2  # extracted, ready for analysis
ANALYZE_STATE_ANALYSING = 3  # analysing
ANALYZE_STATE_ANALYSED = 4  # analyzed
ANALYZE_STATE_ORGANISING = 5  # agent is organising...
ANALYZE_STATE_ORGANISED = 6  # organised

ANALYZE_STATE_LABELS = {
    0: "Uploaded",
    1: "Extracting",
    2: "Extracted",
    3: "Analysing",
    4: "Analysed",
    5: "Organising...",
    6: "Organised"
}

UN_INDEXED_STRING = "UN_IDX_aedb8b3c-94f6-4090-870f-e7e11123497b"

def random_id():
    return ''.join(random.choice(string.ascii_lowercase + string.digits + string.ascii_uppercase) for _ in range(8))
