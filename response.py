# response.py
# Builds and pretty-prints the final standard response object.

import json
from datetime import datetime


def generate_response(req, outputs):
    """
    Combines module outputs into one final response dict.
    Only populates sections for modules that actually ran.
    """
    request_id   = req.get("request_id", "UNKNOWN")
    request_type = req.get("request_type", "")

    # ---- Base skeleton ----
    response = {
        "request_id":    request_id,
        "timestamp":     datetime.now().isoformat(),
        "decision":      outputs.get("decision", "completed"),
        "priority":      outputs.get("priority", {}),
        "eligibility":   outputs.get("eligibility", {}),
        "assignment":    {},
        "route":         outputs.get("route", {}),
        "message":       "",
        "status_code":   200,
        "failure_stage": None
    }

    # ---- Normalize CSP assignment ----
    if "assignment" in outputs:
        raw = outputs["assignment"]
        if isinstance(raw, dict):
            response["assignment"] = raw.get("assignment", raw)

    eligibility_info = outputs.get("eligibility", {})
    assignment_info  = response["assignment"]
    route_info       = outputs.get("route", {})
    priority_info    = outputs.get("priority", {})

    # ---------------------------------------------------------------
    # REJECTED — Logic/KB
    # ---------------------------------------------------------------
    if outputs.get("decision") == "rejected" or \
       not eligibility_info.get("allowed", True):

        response["decision"]      = "rejected"
        response["status_code"]   = 403
        response["failure_stage"] = "Logic_KB"
        reason = eligibility_info.get("explanation",
                                      "Request could not be processed.")
        response["message"] = f"❌ Request rejected. Reason: {reason}"

    # ---------------------------------------------------------------
    # REJECTED — CSP
    # ---------------------------------------------------------------
    elif outputs.get("assignment", {}).get("status") == "Failed":

        response["decision"]      = "rejected"
        response["status_code"]   = 409
        response["failure_stage"] = "CSP"
        response["message"]       = (outputs["assignment"]
                                      .get("message", "Scheduling conflict."))

    # ---------------------------------------------------------------
    # Navigation_Only
    # ---------------------------------------------------------------
    elif request_type == "Navigation_Only":

        path     = route_info.get("path", [])
        algo     = route_info.get("algorithm_used", "BFS")
        path_str = " → ".join(path) if path else "No path found"
        response["decision"] = "completed"
        response["message"]  = f"✅ Route ({algo}): {path_str}"

    # ---------------------------------------------------------------
    # Eligibility_Check
    # ---------------------------------------------------------------
    elif request_type == "Eligibility_Check":

        allowed = eligibility_info.get("allowed", False)
        expl    = eligibility_info.get("explanation", "")
        flag    = "✅ Allowed" if allowed else "❌ Not Allowed"
        response["decision"] = "answered"
        response["message"]  = f"Eligibility: {flag}. {expl}"

    # ---------------------------------------------------------------
    # Booking_or_Scheduling
    # ---------------------------------------------------------------
    elif request_type == "Booking_or_Scheduling":

        room = assignment_info.get("room", "N/A") if isinstance(assignment_info, dict) else "N/A"
        slot = assignment_info.get("slot", "N/A") if isinstance(assignment_info, dict) else "N/A"
        response["decision"] = "accepted"
        response["message"]  = f"✅ Booking confirmed. Room: {room}, Slot: {slot}."

    # ---------------------------------------------------------------
    # Urgent_Service_Request
    # ---------------------------------------------------------------
    elif request_type == "Urgent_Service_Request":

        room  = assignment_info.get("room", "N/A") if isinstance(assignment_info, dict) else "N/A"
        slot  = assignment_info.get("slot", "N/A") if isinstance(assignment_info, dict) else "N/A"
        plabel = priority_info.get("final_priority", "N/A").upper()
        path  = route_info.get("path", [])
        route_str = f" Route: {' → '.join(path)}." if path else ""
        response["decision"] = "accepted"
        response["message"]  = (
            f"✅ Urgent request accepted. Priority: {plabel}. "
            f"Room: {room}, Slot: {slot}.{route_str}"
        )

    # ---------------------------------------------------------------
    # Full_Service_Request
    # ---------------------------------------------------------------
    elif request_type == "Full_Service_Request":

        room  = assignment_info.get("room", "N/A") if isinstance(assignment_info, dict) else "N/A"
        slot  = assignment_info.get("slot", "N/A") if isinstance(assignment_info, dict) else "N/A"
        plabel = priority_info.get("final_priority", "N/A").upper()
        path  = route_info.get("path", [])
        route_str = f" Route: {' → '.join(path)}." if path else ""
        response["decision"] = "accepted"
        response["message"]  = (
            f"✅ Full service request accepted. Priority: {plabel}. "
            f"You are assigned {room} in Slot {slot}. "
            f"Please follow the recommended route.{route_str}"
        )

    # ---------------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------------
    else:
        response["decision"] = "completed"
        response["message"]  = "✅ Request processed successfully."

    return response


def pretty_print_response(response):
    """Human-readable summary of the final response."""

    decision = response.get("decision", "unknown").upper()
    status_map = {
        "ACCEPTED":  "✅ ACCEPTED",
        "REJECTED":  "❌ REJECTED",
        "ANSWERED":  "ℹ️  ANSWERED",
        "COMPLETED": "✓  COMPLETED"
    }
    status = status_map.get(decision, f"✓  {decision}")

    print(f"  Request ID  : {response.get('request_id')}")
    print(f"  Timestamp   : {response.get('timestamp')}")
    print(f"  Status      : {status}")
    print(f"  Message     : {response.get('message', '')}")

    if response.get("priority"):
        p = response["priority"]
        print(f"\n  [Priority]")
        print(f"    Binary    : {p.get('binary_priority', 'N/A')}")
        print(f"    Final     : {p.get('final_priority',  'N/A')}")
        print(f"    Confidence: {p.get('confidence', 0) * 100:.0f}%")

    if response.get("eligibility"):
        e = response["eligibility"]
        print(f"\n  [Eligibility]")
        print(f"    Allowed   : {'Yes' if e.get('allowed') else 'No'}")
        if e.get("explanation"):
            print(f"    Detail    : {e['explanation']}")

    if response.get("assignment"):
        a = response["assignment"]
        if isinstance(a, dict) and (a.get("room") or a.get("slot")):
            print(f"\n  [Assignment]")
            print(f"    Room      : {a.get('room', 'N/A')}")
            print(f"    Slot      : {a.get('slot', 'N/A')}")

    if response.get("route"):
        r = response["route"]
        if r.get("path"):
            print(f"\n  [Route]")
            print(f"    Algorithm : {r.get('algorithm_used', 'N/A')}")
            print(f"    Path      : {' → '.join(r['path'])}")
            print(f"    Cost      : {r.get('cost', 0)}")
            print(f"    Steps     : {r.get('steps', 0)}")

    print("\n" + "=" * 70 + "\n")


def print_response_json(response):
    print(json.dumps(response, indent=4))