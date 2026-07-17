# search_module.py
# Search and Navigation module.
#
# Operational algorithms:
#   BFS  — unweighted graph (shortest hops)
#   A*   — weighted graph + heuristic available
#   UCS  — weighted graph, no heuristic (fallback)
#
# Academic / comparison algorithms also included:
#   DFS, DLS, IDS, Bidirectional BFS, Greedy Best-First, RBFS

import heapq
from collections import deque

# =====================================================================
# CAMPUS GRAPHS
# =====================================================================

UNWEIGHTED_GRAPH = {
    "Hostel":         ["Cafeteria"],
    "Cafeteria":      ["Hostel", "AI_Lab", "Library"],
    "AI_Lab":         ["Cafeteria", "Science_Block"],
    "Library":        ["Cafeteria", "Admin_Block"],
    "Admin_Block":    ["Library", "Exam_Hall", "Parking", "Faculty_Block"],
    "Exam_Hall":      ["Admin_Block", "Seminar_Room"],
    "Seminar_Room":   ["Exam_Hall"],
    "Science_Block":  ["AI_Lab", "Medical_Center", "OS_Lab"],
    "Medical_Center": ["Science_Block"],
    "Parking":        ["Admin_Block"],
    "OS_Lab":         ["Science_Block"],
    "Research_Lab":   ["Science_Block", "AI_Lab"],
    "Faculty_Block":  ["Admin_Block"]
}

WEIGHTED_GRAPH = {
    "Hostel":         [("Cafeteria", 2)],
    "Cafeteria":      [("Hostel", 2), ("AI_Lab", 3), ("Library", 2)],
    "AI_Lab":         [("Cafeteria", 3), ("Science_Block", 2), ("Research_Lab", 2)],
    "Library":        [("Cafeteria", 2), ("Admin_Block", 3)],
    "Admin_Block":    [("Library", 3), ("Exam_Hall", 2), ("Parking", 1),
                       ("Faculty_Block", 1)],
    "Exam_Hall":      [("Admin_Block", 2), ("Seminar_Room", 1)],
    "Seminar_Room":   [("Exam_Hall", 1)],
    "Science_Block":  [("AI_Lab", 2), ("Medical_Center", 3), ("OS_Lab", 1)],
    "Medical_Center": [("Science_Block", 3)],
    "Parking":        [("Admin_Block", 1)],
    "OS_Lab":         [("Science_Block", 1)],
    "Research_Lab":   [("Science_Block", 2), ("AI_Lab", 2)],
    "Faculty_Block":  [("Admin_Block", 1)]
}

# Heuristics: estimated distance from each node TO the named destination
HEURISTICS = {
    "AI_Lab": {
        "Hostel": 5, "Cafeteria": 3, "AI_Lab": 0, "Library": 4,
        "Admin_Block": 5, "Exam_Hall": 6, "Seminar_Room": 7,
        "Science_Block": 2, "Medical_Center": 5, "Parking": 6,
        "OS_Lab": 3, "Research_Lab": 2, "Faculty_Block": 6
    },
    "Library": {
        "Hostel": 2, "Cafeteria": 1, "Library": 0, "AI_Lab": 3,
        "Admin_Block": 2, "Science_Block": 4, "Parking": 3,
        "Exam_Hall": 3, "Seminar_Room": 4, "Faculty_Block": 3
    },
    "Seminar_Room": {
        "Hostel": 6, "Cafeteria": 5, "AI_Lab": 6, "Library": 4,
        "Admin_Block": 3, "Exam_Hall": 1, "Seminar_Room": 0,
        "Science_Block": 7, "Parking": 4, "Faculty_Block": 4
    },
    "Admin_Block": {
        "Hostel": 4, "Cafeteria": 3, "AI_Lab": 5, "Library": 2,
        "Admin_Block": 0, "Exam_Hall": 2, "Seminar_Room": 3,
        "Parking": 1, "Faculty_Block": 1
    },
    "Research_Lab": {
        "Hostel": 4, "Cafeteria": 3, "AI_Lab": 2, "Science_Block": 2,
        "Research_Lab": 0, "OS_Lab": 3, "Medical_Center": 5
    }
}


# =====================================================================
# OPERATIONAL ALGORITHMS
# =====================================================================

def bfs(start, goal, graph):
    """BFS — shortest path by hop count (unweighted)."""
    if start == goal:
        return [start]
    visited = set()
    queue   = deque([(start, [start])])
    while queue:
        node, path = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        for nb in graph.get(node, []):
            if nb not in visited:
                new_path = path + [nb]
                if nb == goal:
                    return new_path
                queue.append((nb, new_path))
    return []


def astar(start, goal, graph, heuristic):
    """A* — least cost path using f = g + h."""
    open_set = []
    heapq.heappush(open_set, (heuristic.get(start, 0), 0, start, [start]))
    visited  = {}
    while open_set:
        f, cost, node, path = heapq.heappop(open_set)
        if node in visited and visited[node] <= cost:
            continue
        visited[node] = cost
        if node == goal:
            return path, cost
        for nb, w in graph.get(node, []):
            nc = cost + w
            h  = heuristic.get(nb, 0)
            heapq.heappush(open_set, (nc + h, nc, nb, path + [nb]))
    return [], float("inf")


def ucs(start, goal, graph):
    """UCS — least cost path without heuristic."""
    open_set = []
    heapq.heappush(open_set, (0, start, [start]))
    visited  = {}
    while open_set:
        cost, node, path = heapq.heappop(open_set)
        if node in visited and visited[node] <= cost:
            continue
        visited[node] = cost
        if node == goal:
            return path, cost
        for nb, w in graph.get(node, []):
            heapq.heappush(open_set, (cost + w, nb, path + [nb]))
    return [], float("inf")


# =====================================================================
# ACADEMIC / COMPARISON ALGORITHMS
# =====================================================================

def dfs(start, goal, graph):
    """DFS — may not give shortest path (academic use)."""
    visited = set()
    stack   = [(start, [start])]
    while stack:
        node, path = stack.pop()
        if node == goal:
            return path
        if node in visited:
            continue
        visited.add(node)
        for nb in reversed(graph.get(node, [])):
            if nb not in visited:
                stack.append((nb, path + [nb]))
    return []


def dls(start, goal, graph, limit):
    """Depth-Limited Search (academic use)."""
    def _dls(node, path, depth):
        if node == goal:
            return path
        if depth == 0:
            return None
        for nb in graph.get(node, []):
            if nb not in path:
                result = _dls(nb, path + [nb], depth - 1)
                if result is not None:
                    return result
        return None
    return _dls(start, [start], limit) or []


def ids(start, goal, graph, max_depth=20):
    """Iterative Deepening Search (academic use)."""
    for depth in range(max_depth + 1):
        result = dls(start, goal, graph, depth)
        if result:
            return result
    return []


def bidirectional_bfs(start, goal, graph):
    """Bidirectional BFS (academic use)."""
    if start == goal:
        return [start]

    # Build reverse graph
    reverse = {node: [] for node in graph}
    for node, neighbors in graph.items():
        for nb in neighbors:
            if nb not in reverse:
                reverse[nb] = []
            reverse[nb].append(node)

    front_visited = {start: [start]}
    back_visited  = {goal:  [goal]}
    front_queue   = deque([start])
    back_queue    = deque([goal])

    while front_queue and back_queue:
        # Expand forward
        node = front_queue.popleft()
        for nb in graph.get(node, []):
            if nb not in front_visited:
                front_visited[nb] = front_visited[node] + [nb]
                front_queue.append(nb)
            if nb in back_visited:
                return front_visited[nb] + back_visited[nb][-2::-1]

        # Expand backward
        node = back_queue.popleft()
        for nb in reverse.get(node, []):
            if nb not in back_visited:
                back_visited[nb] = back_visited[node] + [nb]
                back_queue.append(nb)
            if nb in front_visited:
                return front_visited[nb] + back_visited[node][-2::-1]

    return []


def greedy_bfs(start, goal, graph, heuristic):
    """Greedy Best-First Search (academic use)."""
    open_set = []
    heapq.heappush(open_set, (heuristic.get(start, 0), start, [start]))
    visited  = set()
    while open_set:
        _, node, path = heapq.heappop(open_set)
        if node == goal:
            return path
        if node in visited:
            continue
        visited.add(node)
        for nb, _ in graph.get(node, []):
            if nb not in visited:
                heapq.heappush(open_set, (heuristic.get(nb, 0), nb, path + [nb]))
    return []


# =====================================================================
# MAIN SEARCH INTERFACE
# =====================================================================

def search_route(source, destination, graph_type="unweighted"):
    """
    Selects the appropriate algorithm based on graph_type and heuristic availability.

    Policy:
      unweighted               → BFS
      weighted + heuristic     → A*
      weighted, no heuristic   → UCS

    Returns a standard search output dict.
    """
    try:
        if not source or not destination:
            return {"algorithm_used": "None", "path": [], "cost": 0, "steps": 0,
                    "message": "Error: Source or destination is missing."}

        if source == destination:
            return {"algorithm_used": "None", "path": [source], "cost": 0, "steps": 0,
                    "message": "Already at destination."}

        if graph_type == "weighted":
            heuristic = HEURISTICS.get(destination)
            if heuristic:
                path, cost = astar(source, destination, WEIGHTED_GRAPH, heuristic)
                algo       = "A*"
            else:
                path, cost = ucs(source, destination, WEIGHTED_GRAPH)
                algo       = "UCS"
        else:
            path = bfs(source, destination, UNWEIGHTED_GRAPH)
            cost = len(path) - 1 if path else 0
            algo = "BFS"

        if not path:
            return {"algorithm_used": algo, "path": [], "cost": 0, "steps": 0,
                    "message": f"No route found from {source} to {destination}."}

        return {
            "algorithm_used": algo,
            "path":           path,
            "cost":           cost,
            "steps":          len(path) - 1,
            "message":        f"Route found from {source} to {destination} using {algo}."
        }

    except Exception as e:
        return {"algorithm_used": "Error", "path": [], "cost": 0, "steps": 0,
                "message": f"Search failed: {str(e)}"}


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    tests = [
        ("Hostel", "AI_Lab",       "unweighted"),
        ("Hostel", "AI_Lab",       "weighted"),
        ("Hostel", "Seminar_Room", "weighted"),
        ("Hostel", "Research_Lab", "weighted"),
    ]
    for src, dst, gtype in tests:
        r = search_route(src, dst, gtype)
        print(f"{gtype:12}  {src} → {dst}")
        print(f"  Algo: {r['algorithm_used']}  Path: {' → '.join(r['path'])}  Cost: {r['cost']}\n")