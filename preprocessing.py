# preprocessing.py
# Validates, normalizes, and standardizes the raw request into a structured object.
# Prepares pipeline flags for the router.

import uuid

# =====================================================================
# VALID VALUES
# =====================================================================

VALID_ROLES = ["student", "instructor", "staff"]

ROLE_ALIASES = {
    "teacher":   "instructor",
    "professor": "instructor",
    "faculty":   "instructor"
}

VALID_REQUEST_TYPES = [
    "Navigation_Only",
    "Eligibility_Check",
    "Booking_or_Scheduling",
    "Urgent_Service_Request",
    "Full_Service_Request"
]

VALID_LOCATIONS = [
    "Hostel", "Cafeteria", "AI_Lab", "Library", "Admin_Block",
    "Parking", "Medical_Center", "Exam_Hall", "Seminar_Room",
    "Science_Block", "OS_Lab", "Research_Lab", "Faculty_Block"
]

# All categories across all roles
VALID_CATEGORIES = [
    # Student
    "AI_Lab_Support", "Viva_Scheduling", "Course_Help",
    "Library_Access", "Lab_Access",
    # Instructor
    "Research_Lab", "Faculty_Meeting",
    # Staff
    "Maintenance", "Hostel_Maintenance", "Electrical_Issue",
    "Parking_Management", "Admin_Support", "Security_Support",
    # Shared / legacy
    "Access_Request", "Emergency_Help", "Medical_Support", "Seminar_Management"
]

# Per-role allowed categories (also used by Logic gatekeeper)
ROLE_ALLOWED_CATEGORIES = {
    "student":    ["AI_Lab_Support", "Viva_Scheduling", "Course_Help",
                   "Library_Access", "Lab_Access"],
    "instructor": ["Viva_Scheduling", "Research_Lab", "Faculty_Meeting",
                   "Lab_Access", "AI_Lab_Support"],
    "staff":      ["Maintenance", "Hostel_Maintenance", "Electrical_Issue",
                   "Parking_Management", "Admin_Support", "Security_Support"]
}

# =====================================================================
# NORMALISATION MAPS
# =====================================================================

LOCATION_NORMALIZE = {
    "hostel":         "Hostel",
    "cafeteria":      "Cafeteria",
    "ai lab":         "AI_Lab",
    "ai_lab":         "AI_Lab",
    "ailab":          "AI_Lab",
    "library":        "Library",
    "admin block":    "Admin_Block",
    "admin_block":    "Admin_Block",
    "parking":        "Parking",
    "medical center": "Medical_Center",
    "medical_center": "Medical_Center",
    "exam hall":      "Exam_Hall",
    "exam_hall":      "Exam_Hall",
    "seminar room":   "Seminar_Room",
    "seminar_room":   "Seminar_Room",
    "science block":  "Science_Block",
    "science_block":  "Science_Block",
    "os lab":         "OS_Lab",
    "os_lab":         "OS_Lab",
    "research lab":   "Research_Lab",
    "research_lab":   "Research_Lab",
    "faculty block":  "Faculty_Block",
    "faculty_block":  "Faculty_Block"
}

CATEGORY_NORMALIZE = {
    "ai lab support":     "AI_Lab_Support",
    "ai_lab_support":     "AI_Lab_Support",
    "viva scheduling":    "Viva_Scheduling",
    "viva_scheduling":    "Viva_Scheduling",
    "course help":        "Course_Help",
    "course_help":        "Course_Help",
    "library access":     "Library_Access",
    "library_access":     "Library_Access",
    "lab access":         "Lab_Access",
    "lab_access":         "Lab_Access",
    "research lab":       "Research_Lab",
    "research_lab":       "Research_Lab",
    "faculty meeting":    "Faculty_Meeting",
    "faculty_meeting":    "Faculty_Meeting",
    "maintenance":        "Maintenance",
    "hostel maintenance": "Hostel_Maintenance",
    "hostel_maintenance": "Hostel_Maintenance",
    "electrical issue":   "Electrical_Issue",
    "electrical_issue":   "Electrical_Issue",
    "parking management": "Parking_Management",
    "parking_management": "Parking_Management",
    "admin support":      "Admin_Support",
    "admin_support":      "Admin_Support",
    "security support":   "Security_Support",
    "security_support":   "Security_Support",
    "access request":     "Access_Request",
    "access_request":     "Access_Request",
    "emergency help":     "Emergency_Help",
    "emergency_help":     "Emergency_Help",
    "medical support":    "Medical_Support",
    "medical_support":    "Medical_Support",
    "seminar management": "Seminar_Management",
    "seminar_management": "Seminar_Management"
}


def normalize_location(loc):
    key = loc.strip().lower().replace("_", " ")
    return (LOCATION_NORMALIZE.get(key)
            or LOCATION_NORMALIZE.get(loc.strip().lower())
            or loc.strip())


def normalize_category(cat):
    key = cat.strip().lower().replace("_", " ")
    return (CATEGORY_NORMALIZE.get(key)
            or CATEGORY_NORMALIZE.get(cat.strip().lower())
            or cat.strip())


# =====================================================================
# MAIN PREPROCESSOR
# =====================================================================

def preprocess_request(req):
    """
    Validates, normalizes, and enriches the raw request dict.
    Raises ValueError on invalid data.
    Returns the enriched standardized request dict.
    """

    # ---- ROLE ----
    role = req.get("role", "").lower().strip()
    role = ROLE_ALIASES.get(role, role)
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid role '{role}'. Must be one of: {VALID_ROLES}")
    req["role"] = role

    # ---- REQUEST TYPE ----
    rtype = req.get("request_type", "")
    if rtype not in VALID_REQUEST_TYPES:
        raise ValueError(
            f"Invalid request type '{rtype}'. "
            f"Must be one of: {VALID_REQUEST_TYPES}"
        )
    req["request_type"] = rtype

    # ---- CATEGORY ----
    if req.get("category"):
        req["category"] = normalize_category(req["category"])
        if req["category"] not in VALID_CATEGORIES:
            raise ValueError(
                f"Invalid category '{req['category']}'. "
                f"Valid: {VALID_CATEGORIES}"
            )

    # ---- CURRENT LOCATION ----
    if req.get("current_location"):
        req["current_location"] = normalize_location(req["current_location"])
        if req["current_location"] not in VALID_LOCATIONS:
            raise ValueError(
                f"Unknown location '{req['current_location']}'. "
                f"Valid: {VALID_LOCATIONS}"
            )

    # ---- DESTINATION ----
    if req.get("destination"):
        req["destination"] = normalize_location(req["destination"])
        if req["destination"] not in VALID_LOCATIONS:
            raise ValueError(
                f"Unknown destination '{req['destination']}'. "
                f"Valid: {VALID_LOCATIONS}"
            )

    # ---- RESOURCE ----
    if req.get("resource"):
        req["resource"] = normalize_location(req["resource"])

    # ---- PREFERRED SLOT ----
    if req.get("preferred_slot") is not None:
        if req["preferred_slot"] not in [1, 2, 3, 4]:
            raise ValueError("preferred_slot must be 1, 2, 3, or 4.")

    # ---- NUMERIC RANGE FIELDS ----
    for field in ["severity", "time_sensitivity", "crowd_level"]:
        if field in req and req[field] is not None:
            if not (1 <= req[field] <= 10):
                raise ValueError(f"'{field}' must be between 1 and 10.")

    # ---- ELIGIBILITY SCORE ----
    if "eligibility_score" in req:
        try:
            req["eligibility_score"] = float(req["eligibility_score"])
        except (ValueError, TypeError):
            raise ValueError("eligibility_score (GPA) must be numeric.")

    # ---- REQUEST ID ----
    if not req.get("request_id"):
        req["request_id"] = "REQ-" + str(uuid.uuid4())[:8].upper()

    # ---- GRAPH TYPE ----
    req["graph_type"] = (
        "weighted"
        if rtype in ("Full_Service_Request", "Urgent_Service_Request")
        else "unweighted"
    )

    # ---- PIPELINE FLAGS ----
    req["needs_ann"]    = rtype in ("Urgent_Service_Request", "Full_Service_Request")
    req["needs_logic"]  = rtype in ("Eligibility_Check", "Booking_or_Scheduling",
                                     "Urgent_Service_Request", "Full_Service_Request")
    req["needs_csp"]    = rtype in ("Booking_or_Scheduling", "Urgent_Service_Request",
                                     "Full_Service_Request")
    req["needs_search"] = rtype in ("Navigation_Only", "Full_Service_Request")

    return req