# logic_module.py
# Logic / Knowledge Base module.
# Responsibilities:
#   1. Role-based resource & category authorization
#   2. FOL forward-chaining entailment (UsesLab queries)
#   3. GPA eligibility check for students
#   4. CSP Scheduler — conflict-free room/slot assignment

import itertools


# =====================================================================
# HELPERS
# =====================================================================

def normalize(text):
    return str(text).strip().replace(" ", "_").lower()


# =====================================================================
# KNOWLEDGE BASE
# =====================================================================

# Resources each role may access
ALLOWED_RESOURCES = {
    "student":    ["Library", "AI_Lab", "Cafeteria", "Hostel",
                   "Science_Block", "OS_Lab"],
    "instructor": ["Admin_Block", "Exam_Hall", "Seminar_Room", "AI_Lab",
                   "Science_Block", "Library", "Parking", "OS_Lab",
                   "Research_Lab", "Faculty_Block"],
    "staff":      ["Admin_Block", "Parking", "Medical_Center", "Cafeteria",
                   "Science_Block", "Seminar_Room", "Hostel"]
}

# Categories each role is permitted to request
ROLE_ALLOWED_CATEGORIES = {
    "student":    ["AI_Lab_Support", "Viva_Scheduling", "Course_Help",
                   "Library_Access", "Lab_Access"],
    "instructor": ["Viva_Scheduling", "Research_Lab", "Faculty_Meeting",
                   "Lab_Access", "AI_Lab_Support"],
    "staff":      ["Maintenance", "Hostel_Maintenance", "Electrical_Issue",
                   "Parking_Management", "Admin_Support", "Security_Support"]
}

# Minimum GPA / employment requirements
ROLE_ELIGIBILITY_RULES = {
    "student":    {"min_gpa": 2.0},
    "instructor": {"employment_required": True},
    "staff":      {"employment_required": True}
}

# FOL knowledge base
KNOWLEDGE_BASE = {
    "Teaches": {
        "DrKhan":  ["AI", "Math"],
        "ProfAli": ["Networks", "OS"]
    },
    "Enrolled": {
        "Ali":  ["AI", "Networks"],
        "Sara": ["Math"]
    },
    "Lab_For_Subject": {
        "AI":       "AI_Lab",
        "Math":     "Science_Block",
        "Networks": "Science_Block",
        "OS":       "OS_Lab"
    }
}


# =====================================================================
# FOL FORWARD CHAINING
# =====================================================================

def entail_lab_access(person, lab, role):
    """
    Rule:
      instructor: Teaches(x, S)  ∧ Lab_For_Subject(S, Lab) ⟹ UsesLab(x, Lab)
      student:    Enrolled(x, S) ∧ Lab_For_Subject(S, Lab) ⟹ UsesLab(x, Lab)
    """
    subjects = (KNOWLEDGE_BASE["Teaches"].get(person, [])
                if role == "instructor"
                else KNOWLEDGE_BASE["Enrolled"].get(person, []))

    for subj in subjects:
        assigned = KNOWLEDGE_BASE["Lab_For_Subject"].get(subj, "")
        if normalize(assigned) == normalize(lab):
            verb = "teaches" if role == "instructor" else "is enrolled in"
            return (
                True,
                f"{person} {verb} {subj}, which uses {lab}. "
                f"Therefore UsesLab({person}, {lab}) is entailed."
            )

    return False, f"No entailment found for {person} to access {lab}."


# =====================================================================
# LOGIC GATEKEEPER
# =====================================================================

def logic_gatekeeper(req):
    """
    Main validation function.
    Returns (bool, explanation_string).
    """
    try:
        role         = normalize(req.get("role", ""))
        resource     = normalize(req.get("resource", ""))
        category     = normalize(req.get("category", ""))
        name         = req.get("name", "").strip()
        request_type = normalize(req.get("request_type", ""))

        if not role:
            raise KeyError("Missing 'role'.")

        if role not in ALLOWED_RESOURCES:
            return False, f"Auth Error: Role '{role}' is not recognized."

        # -------------------------------------------------------
        # ELIGIBILITY CHECK
        # -------------------------------------------------------
        if request_type == "eligibility_check":
            query = req.get("query", "")

            # FOL query: UsesLab(Person, Lab)
            if "UsesLab" in query:
                try:
                    inner  = query.replace("UsesLab(", "").rstrip(")")
                    parts  = [p.strip() for p in inner.split(",")]
                    if len(parts) == 2:
                        person, lab = parts
                        return entail_lab_access(person, lab, role)
                except Exception:
                    pass

            # GPA check for students
            if role == "student":
                score   = float(req.get("eligibility_score", 0))
                min_gpa = ROLE_ELIGIBILITY_RULES["student"]["min_gpa"]
                if score < min_gpa:
                    return (
                        False,
                        f"Eligibility Error: GPA {score} is below "
                        f"minimum required {min_gpa}."
                    )

            return True, f"Eligibility check passed for {name}."

        # -------------------------------------------------------
        # CATEGORY AUTHORIZATION
        # -------------------------------------------------------
        allowed_cats = [normalize(c) for c in ROLE_ALLOWED_CATEGORIES.get(role, [])]
        if category and category not in allowed_cats:
            return (
                False,
                f"Logic Error: Role '{role}' is not permitted "
                f"for category '{category}'."
            )

        # -------------------------------------------------------
        # RESOURCE AUTHORIZATION
        # -------------------------------------------------------
        if resource:
            allowed_res = [normalize(r) for r in ALLOWED_RESOURCES[role]]
            if resource not in allowed_res:
                return (
                    False,
                    f"Logic Error: '{role}' is not authorized "
                    f"to access '{resource}'."
                )

        # -------------------------------------------------------
        # GPA CHECK FOR STUDENTS
        # -------------------------------------------------------
        if role == "student":
            score   = float(req.get("eligibility_score", 0))
            min_gpa = ROLE_ELIGIBILITY_RULES["student"]["min_gpa"]
            if score < min_gpa:
                return (
                    False,
                    f"Eligibility Error: GPA {score} is below "
                    f"minimum required {min_gpa}."
                )

        # -------------------------------------------------------
        # SUCCESS
        # -------------------------------------------------------
        target = resource if resource else category
        return (
            True,
            f"Logic Check Passed: {name} ({role}) is authorized "
            f"to access '{target}'."
        )

    except KeyError as ke:
        return False, f"Field Error: {str(ke)}"
    except ValueError:
        return False, "Data Error: eligibility_score must be numeric."
    except Exception as e:
        return False, f"System Error: {str(e)}"


# =====================================================================
# CSP SCHEDULER
# =====================================================================

# Preferred room per normalized category
CATEGORY_ROOM_MAP = {
    "ai_lab_support":    "AI_Lab",
    "viva_scheduling":   "Seminar_Room",
    "access_request":    "Admin_Block",
    "lab_access":        "OS_Lab",
    "library_access":    "Library",
    "course_help":       "Library",
    "research_lab":      "Research_Lab",
    "faculty_meeting":   "Faculty_Block",
    "maintenance":       "Science_Block",
    "hostel_maintenance":"Hostel",
    "electrical_issue":  "Science_Block",
    "parking_management":"Parking",
    "admin_support":     "Admin_Block",
    "security_support":  "Admin_Block",
    "medical_support":   "Medical_Center",
    "seminar_management":"Seminar_Room"
}

ALL_ROOMS = [
    "AI_Lab", "Seminar_Room", "Exam_Hall", "Admin_Block",
    "Library", "Parking", "Medical_Center", "Science_Block",
    "OS_Lab", "Research_Lab", "Faculty_Block", "Room_A", "Room_B"
]

# Already-booked (room, slot) pairs
EXISTING_BOOKINGS = [
    ("AI_Lab",      1),
    ("Room_A",      2),
    ("Seminar_Room",3)
]


def csp_scheduler(req):
    """
    Assigns a conflict-free (room, slot) pair.
    Priority affects slot ordering; category determines preferred room.
    Returns a standard CSP output dict.
    """
    try:
        priority       = normalize(req.get("predicted_priority", "normal"))
        preferred_slot = req.get("preferred_slot")
        category       = normalize(req.get("category", ""))

        # Slot ordering by priority
        if priority == "urgent":
            slots = [1, 2, 3, 4]
        elif priority == "high":
            slots = [2, 1, 3, 4]
        else:
            slots = [3, 4, 2, 1]

        preferred_room = CATEGORY_ROOM_MAP.get(category, "Room_A")
        ordered_rooms  = [preferred_room] + [r for r in ALL_ROOMS if r != preferred_room]
        domain         = list(itertools.product(ordered_rooms, slots))

        # 1. Try preferred room + preferred slot
        if preferred_slot:
            for room, slot in domain:
                if room == preferred_room and slot == preferred_slot:
                    if (room, slot) not in EXISTING_BOOKINGS:
                        return {
                            "status":      "Success",
                            "assignment":  {"room": room, "slot": slot},
                            "destination": room,
                            "message":
                                f"Scheduled in {room} at Slot {slot}. "
                                f"Preferred slot assigned."
                        }

        # 2. Try any available (room, slot)
        for room, slot in domain:
            if (room, slot) not in EXISTING_BOOKINGS:
                note = (f"Preferred slot {preferred_slot} unavailable. "
                        if preferred_slot else "")
                return {
                    "status":      "Success",
                    "assignment":  {"room": room, "slot": slot},
                    "destination": room,
                    "message":     f"{note}Scheduled in {room} at Slot {slot}."
                }

        # 3. All slots fully booked
        return {
            "status":      "Failed",
            "assignment":  {},
            "destination": "",
            "message":     "CSP Error: All slots are currently fully booked."
        }

    except Exception as e:
        return {
            "status":      "Error",
            "assignment":  {},
            "destination": "",
            "message":     f"Scheduling failed: {str(e)}"
        }


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    req = {
        "role":              "student",
        "name":              "Ali",
        "resource":          "AI_Lab",
        "eligibility_score": 3.8,
        "request_type":      "Booking_or_Scheduling",
        "category":          "AI_Lab_Support",
        "preferred_slot":    1
    }
    valid, msg = logic_gatekeeper(req)
    print(f"Logic: {msg}")
    if valid:
        result = csp_scheduler(req)
        print(f"CSP:   {result['message']}")