# router.py
# Request Router — selects the module pipeline based on request_type.
#
# Pipeline rules (from manual):
#   Navigation_Only        → [Search]
#   Eligibility_Check      → [Logic_KB]
#   Booking_or_Scheduling  → [Logic_KB, CSP]
#   Urgent_Service_Request → [ANN, Logic_KB, CSP]
#   Full_Service_Request   → [ANN, Logic_KB, CSP, Search]


def route_request(req):
    """
    Reads request_type from the request dict and returns the ordered
    pipeline list.  Also updates the needs_* flags on the dict.
    Raises ValueError for unknown request types.
    """
    rtype = req.get("request_type", "")

    if rtype == "Navigation_Only":
        pipeline = ["Search"]

    elif rtype == "Eligibility_Check":
        pipeline = ["Logic_KB"]

    elif rtype == "Booking_or_Scheduling":
        pipeline = ["Logic_KB", "CSP"]

    elif rtype == "Urgent_Service_Request":
        pipeline = ["ANN", "Logic_KB", "CSP"]

    elif rtype == "Full_Service_Request":
        pipeline = ["ANN", "Logic_KB", "CSP", "Search"]

    else:
        raise ValueError(
            f"Unknown request type: '{rtype}'. "
            f"Must be one of: Navigation_Only, Eligibility_Check, "
            f"Booking_or_Scheduling, Urgent_Service_Request, Full_Service_Request"
        )

    # Keep pipeline flags in sync
    req["needs_ann"]    = "ANN"      in pipeline
    req["needs_logic"]  = "Logic_KB" in pipeline
    req["needs_csp"]    = "CSP"      in pipeline
    req["needs_search"] = "Search"   in pipeline

    return pipeline