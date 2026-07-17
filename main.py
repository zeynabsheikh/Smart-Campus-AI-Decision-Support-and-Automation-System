# main.py
# Smart Campus AI Decision Support System — CLI Entry Point
#
# Role-based menus per handout:
#   Student    → Navigation Only / Eligibility Check / Booking / Urgent / Full
#   Instructor → Navigation Only / Eligibility Check / Booking / Full
#   Staff      → Navigation Only / Maintenance / Admin Support / Urgent / Full
#
# IMPORTANT: Menu labels differ per role, but they always map to one of the
# five canonical request types.  Category is a separate field.

import sys
from preprocessing import preprocess_request
from router        import route_request
from ann_module    import ann_priority_layer
from logic_module  import logic_gatekeeper, csp_scheduler
from search_module import search_route
from response      import generate_response, pretty_print_response


# =====================================================================
# ROLE MENU DEFINITIONS
# =====================================================================
# Each entry: (display_label, request_type, default_category_hint)
# default_category_hint is shown in the category prompt as an example.

STUDENT_MENU = {
    "1": ("Navigation Only",        "Navigation_Only",       None),
    "2": ("Eligibility Check",      "Eligibility_Check",     None),
    "3": ("Booking or Scheduling",  "Booking_or_Scheduling", "AI_Lab_Support / Viva_Scheduling / Course_Help / Library_Access / Lab_Access"),
    "4": ("Urgent Service Request", "Urgent_Service_Request","AI_Lab_Support / Viva_Scheduling"),
    "5": ("Full Service Request",   "Full_Service_Request",  "AI_Lab_Support / Viva_Scheduling / Course_Help")
}

INSTRUCTOR_MENU = {
    "1": ("Navigation Only",        "Navigation_Only",       None),
    "2": ("Eligibility Check",      "Eligibility_Check",     None),
    "3": ("Booking or Scheduling",  "Booking_or_Scheduling", "Viva_Scheduling / Research_Lab / Faculty_Meeting / Lab_Access / AI_Lab_Support"),
    "4": ("Full Service Request",   "Full_Service_Request",  "Viva_Scheduling / Research_Lab / Faculty_Meeting")
}

STAFF_MENU = {
    "1": ("Navigation Only",        "Navigation_Only",       None),
    "2": ("Maintenance Request",    "Booking_or_Scheduling", "Maintenance / Hostel_Maintenance / Electrical_Issue"),
    "3": ("Admin Support",          "Booking_or_Scheduling", "Admin_Support / Security_Support / Parking_Management"),
    "4": ("Urgent Service Request", "Urgent_Service_Request","Maintenance / Electrical_Issue / Security_Support"),
    "5": ("Full Service Request",   "Full_Service_Request",  "Maintenance / Admin_Support / Parking_Management")
}

MENUS = {
    "student":    STUDENT_MENU,
    "instructor": INSTRUCTOR_MENU,
    "staff":      STAFF_MENU
}

MENU_TITLES = {
    "student":    "Student Menu",
    "instructor": "Instructor Menu",
    "staff":      "Staff Menu"
}


# =====================================================================
# INPUT HELPERS
# =====================================================================

def clean_text(text):
    """Converts 'AI Lab Support' → 'AI_Lab_Support'."""
    return "_".join(text.strip().split())


def get_int(prompt, lo=None, hi=None):
    while True:
        raw = input(prompt).strip()
        try:
            val = int(raw)
            if lo is not None and val < lo:
                print(f"  ❌ Value must be ≥ {lo}.")
                continue
            if hi is not None and val > hi:
                print(f"  ❌ Value must be ≤ {hi}.")
                continue
            return val
        except ValueError:
            print("  ❌ Please enter a valid integer.")


def get_float(prompt):
    while True:
        raw = input(prompt).strip()
        try:
            return float(raw)
        except ValueError:
            print("  ❌ Please enter a valid number.")


# =====================================================================
# ROLE-SPECIFIC FIELD COLLECTION
# =====================================================================

def collect_fields(rtype, role, cat_hint):
    """
    Collects the conditional fields required by the given request type.
    Returns a partial request dict (without name/role/request_type).
    """
    data = {}

    # ------------------------------------------------------------------
    # Navigation_Only
    # ------------------------------------------------------------------
    if rtype == "Navigation_Only":
        print()
        data["current_location"] = clean_text(input("  Enter Current Location : "))
        data["destination"]      = clean_text(input("  Enter Destination      : "))

    # ------------------------------------------------------------------
    # Eligibility_Check
    # ------------------------------------------------------------------
    elif rtype == "Eligibility_Check":
        print()
        print("  Example query: UsesLab(DrKhan, AI_Lab)  |  UsesLab(Ali, AI_Lab)")
        data["query"]    = input("  Enter Query    : ").strip()
        data["resource"] = clean_text(input("  Enter Resource (e.g. AI_Lab): "))
        if role == "student":
            data["eligibility_score"] = get_float("  Enter GPA       : ")

    # ------------------------------------------------------------------
    # Booking_or_Scheduling
    # ------------------------------------------------------------------
    elif rtype == "Booking_or_Scheduling":
        print()
        hint = cat_hint or "category"
        data["category"]         = clean_text(input(f"  Enter Category ({hint}): "))
        data["resource"]         = clean_text(input("  Enter Resource         : "))
        data["current_location"] = clean_text(input("  Enter Current Location : "))
        data["preferred_slot"]   = get_int("  Enter Preferred Slot (1-4): ", 1, 4)
        if role == "student":
            data["eligibility_score"] = get_float("  Enter GPA              : ")

    # ------------------------------------------------------------------
    # Urgent_Service_Request
    # ------------------------------------------------------------------
    elif rtype == "Urgent_Service_Request":
        print()
        hint = cat_hint or "category"
        data["category"]         = clean_text(input(f"  Enter Category ({hint}): "))
        data["resource"]         = clean_text(input("  Enter Resource         : "))
        data["current_location"] = clean_text(input("  Enter Current Location : "))
        data["preferred_slot"]   = get_int("  Enter Preferred Slot (1-4) [optional, 0 to skip]: ", 0, 4)
        if data["preferred_slot"] == 0:
            del data["preferred_slot"]
        print("\n  [ANN Priority Inputs]")
        data["severity"]         = get_int("  Enter Severity (1-10)         : ", 1, 10)
        data["time_sensitivity"] = get_int("  Enter Time Sensitivity (1-10) : ", 1, 10)
        data["crowd_level"]      = get_int("  Enter Crowd Level (1-10)      : ", 1, 10)
        if role == "student":
            data["eligibility_score"] = get_float("  Enter GPA                     : ")

    # ------------------------------------------------------------------
    # Full_Service_Request
    # ------------------------------------------------------------------
    elif rtype == "Full_Service_Request":
        print()
        hint = cat_hint or "category"
        data["category"]         = clean_text(input(f"  Enter Category ({hint}): "))
        data["resource"]         = clean_text(input("  Enter Resource         : "))
        data["current_location"] = clean_text(input("  Enter Current Location : "))
        data["preferred_slot"]   = get_int("  Enter Preferred Slot (1-4): ", 1, 4)
        print("\n  [ANN Priority Inputs]")
        data["severity"]         = get_int("  Enter Severity (1-10)         : ", 1, 10)
        data["time_sensitivity"] = get_int("  Enter Time Sensitivity (1-10) : ", 1, 10)
        data["crowd_level"]      = get_int("  Enter Crowd Level (1-10)      : ", 1, 10)
        note = input("  Enter Description Note (optional, Enter to skip): ").strip()
        if note:
            data["description_note"] = note
        if role == "student":
            data["eligibility_score"] = get_float("  Enter GPA                     : ")

    return data


# =====================================================================
# INPUT COLLECTION
# =====================================================================

def get_user_input():
    print("\n" + "=" * 70)
    print("    Smart Campus AI Decision Support System")
    print("=" * 70 + "\n")

    # ---- Name ----
    name = input("Enter Name: ").strip()
    if not name:
        print("❌ Name cannot be empty.")
        return None

    # ---- Role ----
    print("Roles: student / instructor / staff")
    role = input("Enter Role: ").strip().lower()
    if role not in ["student", "instructor", "staff"]:
        print("❌ Invalid role. Choose: student, instructor, or staff.")
        return None

    # ---- Role-based menu ----
    menu = MENUS[role]
    print(f"\n{MENU_TITLES[role]}:")
    for key, (label, _, _) in menu.items():
        print(f"  {key}. {label}")

    choice = input("\nEnter choice: ").strip()
    if choice not in menu:
        print(f"❌ Invalid choice '{choice}'.")
        return None

    label, rtype, cat_hint = menu[choice]
    print(f"\n  → {label}  (Request Type: {rtype})\n")

    # ---- Collect conditional fields ----
    fields = collect_fields(rtype, role, cat_hint)
    if fields is None:
        return None

    # ---- Assemble request ----
    request = {"name": name, "role": role, "request_type": rtype}
    request.update(fields)

    return request


# =====================================================================
# MAIN PIPELINE
# =====================================================================

def main():
    try:
        # 1. Collect raw input
        req = get_user_input()
        if req is None:
            print("\n❌ Request aborted.\n")
            return

        print("\n" + "=" * 70)
        print("  Processing Request...")
        print("=" * 70)

        # 2. Preprocess (validate + normalize)
        try:
            req = preprocess_request(req)
        except ValueError as ve:
            print(f"\n❌ Validation Error: {ve}\n")
            return

        print(f"  Request ID  : {req['request_id']}")
        print(f"  Name        : {req['name']}  |  Role: {req['role']}")
        print(f"  Type        : {req['request_type']}")

        # 3. Route → pipeline
        pipeline = route_request(req)
        print(f"  Pipeline    : {' → '.join(pipeline)}\n")

        outputs = {}

        # ---------------------------------------------------------------
        # ANN MODULE
        # ---------------------------------------------------------------
        if "ANN" in pipeline:
            print("[ANN Module]")
            priority = ann_priority_layer(req)
            outputs["priority"]          = priority
            req["predicted_priority"]    = priority.get("final_priority", "normal")

            print(f"  Binary Priority  : {priority['binary_priority']}")
            print(f"  Final Priority   : {priority['final_priority']}")
            print(f"  Confidence       : {priority['confidence'] * 100:.0f}%\n")

        # ---------------------------------------------------------------
        # LOGIC / KB MODULE
        # ---------------------------------------------------------------
        if "Logic_KB" in pipeline:
            print("[Logic / KB Module]")
            valid, explanation = logic_gatekeeper(req)
            outputs["eligibility"] = {"allowed": valid, "explanation": explanation}

            status_str = "✅ ALLOWED" if valid else "❌ DENIED"
            print(f"  Status  : {status_str}")
            print(f"  Detail  : {explanation}\n")

            if not valid:
                outputs["decision"] = "rejected"
                final = generate_response(req, outputs)
                print("=" * 70)
                print("FINAL RESPONSE")
                print("=" * 70)
                pretty_print_response(final)
                return

        # ---------------------------------------------------------------
        # CSP SCHEDULER
        # ---------------------------------------------------------------
        if "CSP" in pipeline:
            print("[CSP Scheduler]")
            csp_result = csp_scheduler(req)
            outputs["assignment"] = csp_result

            if csp_result.get("status") == "Success":
                asgn = csp_result["assignment"]
                print(f"  Room    : {asgn.get('room')}")
                print(f"  Slot    : {asgn.get('slot')}")
                print(f"  Note    : {csp_result['message']}\n")
                req["destination"] = csp_result.get("destination", "")
            else:
                outputs["decision"] = "rejected"
                final = generate_response(req, outputs)
                print("=" * 70)
                print("FINAL RESPONSE")
                print("=" * 70)
                pretty_print_response(final)
                return

        # ---------------------------------------------------------------
        # SEARCH MODULE
        # ---------------------------------------------------------------
        if "Search" in pipeline:
            print("[Search Module]")
            src = req.get("current_location", "")
            dst = req.get("destination", "")

            if src and dst:
                route_result = search_route(src, dst, req.get("graph_type", "unweighted"))
                outputs["route"] = route_result

                if route_result.get("path"):
                    print(f"  Algorithm : {route_result['algorithm_used']}")
                    print(f"  Path      : {' → '.join(route_result['path'])}")
                    print(f"  Cost      : {route_result['cost']}")
                    print(f"  Steps     : {route_result['steps']}\n")
                else:
                    print(f"  ⚠️  {route_result['message']}\n")
            else:
                print("  ⚠️  Source or destination missing — skipping route.\n")

        # ---------------------------------------------------------------
        # FINAL RESPONSE
        # ---------------------------------------------------------------
        print("=" * 70)
        print("FINAL RESPONSE")
        print("=" * 70)
        final = generate_response(req, outputs)
        pretty_print_response(final)

    except KeyboardInterrupt:
        print("\n\nCancelled.\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ System Error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# =====================================================================
# ENTRY POINT
# =====================================================================
if __name__ == "__main__":
    main()