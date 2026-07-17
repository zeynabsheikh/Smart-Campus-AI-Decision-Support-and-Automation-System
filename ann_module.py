# ann_module.py
# ANN Priority Module.
#
# Perceptron → binary classifier  : Urgent  vs  Not_Urgent
# SimpleMLP  → multiclass         : low / normal / high / urgent
#
# ann_priority_layer() is the main entry point called by main.py.

import numpy as np

# =====================================================================
# ENCODING MAPS
# =====================================================================

ROLE_ENCODING = {
    "student":    0,
    "instructor": 1,
    "staff":      2
}

CATEGORY_ENCODING = {
    "AI_Lab_Support":    0,
    "Viva_Scheduling":   1,
    "Access_Request":    2,
    "Maintenance":       3,
    "Emergency_Help":    4,
    "Course_Help":       5,
    "Library_Access":    6,
    "Lab_Access":        7,
    "Research_Lab":      8,
    "Faculty_Meeting":   9,
    "Hostel_Maintenance":10,
    "Electrical_Issue":  11,
    "Parking_Management":12,
    "Admin_Support":     13,
    "Security_Support":  14
}

PRIORITY_CLASSES = ["low", "normal", "high", "urgent"]

# =====================================================================
# FEATURE BUILDER
# Feature order (7 values):
#   [role, category, severity, time_sensitivity, crowd_level, distance, eligibility]
# =====================================================================

def build_feature_vector(req):
    """
    Converts a structured request dict into a 7-element numeric feature vector.
    """
    role_enc     = float(ROLE_ENCODING.get(req.get("role", "student"), 0))
    cat_enc      = float(CATEGORY_ENCODING.get(req.get("category", "AI_Lab_Support"), 0))
    severity     = float(req.get("severity", 5))
    time_sens    = float(req.get("time_sensitivity", 5))
    crowd        = float(req.get("crowd_level", 5))
    distance     = float(req.get("distance", 4))
    eligibility  = 1.0 if float(req.get("eligibility_score", 3.0)) >= 2.0 else 0.0

    return [role_enc, cat_enc, severity, time_sens, crowd, distance, eligibility]


# =====================================================================
# PERCEPTRON — Binary Classifier
# =====================================================================

class Perceptron:
    """
    Binary classifier: Urgent (1) vs Not_Urgent (0).
    Pre-trained weights for a 7-feature input vector.
    """

    def __init__(self):
        # Weights: [role, category, severity, time_sens, crowd, distance, eligibility]
        self.weights = np.array([0.05, 0.05, 0.35, 0.35, 0.10, 0.05, 0.05])
        self.bias    = -3.5

    def sigmoid(self, x):
        return 1.0 / (1.0 + np.exp(-np.clip(x, -500, 500)))

    def predict(self, features):
        """Returns (label_str, confidence_float)."""
        x          = np.array(features, dtype=float)
        z          = np.dot(x, self.weights) + self.bias
        activation = self.sigmoid(z)
        label      = "urgent" if activation >= 0.5 else "not_urgent"
        return label, round(float(activation), 4)


# =====================================================================
# MLP — Multiclass Priority Classifier
# =====================================================================

class SimpleMLP:
    """
    Multiclass classifier: low / normal / high / urgent.
    Two fully-connected layers with fixed (pre-trained) weights.
    Layer 1: 7 inputs  → 8 hidden  (ReLU)
    Layer 2: 8 hidden  → 4 outputs (Softmax)
    """

    def __init__(self):
        np.random.seed(42)

        # Layer 1 weights  shape (8, 7)
        self.W1 = np.array([
            [ 0.30, -0.10,  0.40,  0.35, -0.20,  0.10,  0.20],
            [ 0.10,  0.40,  0.25,  0.30,  0.10, -0.10,  0.15],
            [-0.20,  0.30,  0.50,  0.45,  0.00,  0.20,  0.10],
            [ 0.20, -0.20,  0.35,  0.50,  0.20,  0.30, -0.10],
            [ 0.10,  0.10,  0.20,  0.15,  0.40,  0.10,  0.20],
            [ 0.30,  0.20,  0.15, -0.10,  0.30,  0.40,  0.10],
            [-0.10,  0.30,  0.45,  0.35,  0.10,  0.20,  0.25],
            [ 0.20,  0.10,  0.30,  0.40, -0.10,  0.10,  0.35]
        ])
        self.b1 = np.zeros(8)

        # Layer 2 weights  shape (4, 8)
        self.W2 = np.array([
            [0.40, 0.20, 0.10, 0.30, 0.20, 0.10, 0.30, 0.10],
            [0.10, 0.40, 0.30, 0.20, 0.10, 0.30, 0.20, 0.40],
            [0.30, 0.10, 0.40, 0.10, 0.30, 0.20, 0.10, 0.30],
            [0.20, 0.30, 0.20, 0.40, 0.40, 0.40, 0.40, 0.20]
        ])
        self.b2 = np.zeros(4)

    def relu(self, x):
        return np.maximum(0, x)

    def softmax(self, x):
        e = np.exp(x - np.max(x))
        return e / e.sum()

    def predict(self, features):
        """Returns (priority_label_str, confidence_float)."""
        x         = np.array(features, dtype=float)
        h         = self.relu(self.W1 @ x + self.b1)
        out       = self.softmax(self.W2 @ h + self.b2)
        idx       = int(np.argmax(out))
        return PRIORITY_CLASSES[idx], round(float(out[idx]), 4)


# =====================================================================
# MAIN ENTRY POINT
# =====================================================================

def ann_priority_layer(req):
    """
    Called by main.py for Urgent_Service_Request and Full_Service_Request.

    Required fields in req:
        severity, time_sensitivity, crowd_level

    Optional fields:
        role, category, eligibility_score, distance

    Returns:
        {
            "binary_priority": "urgent" | "not_urgent",
            "final_priority":  "low" | "normal" | "high" | "urgent",
            "confidence":      float
        }
    """
    features = build_feature_vector(req)

    perceptron           = Perceptron()
    binary_label, _      = perceptron.predict(features)

    mlp                  = SimpleMLP()
    final_priority, conf = mlp.predict(features)

    return {
        "binary_priority": binary_label,
        "final_priority":  final_priority,
        "confidence":      conf
    }


# =====================================================================
# STANDALONE TEST
# =====================================================================
if __name__ == "__main__":
    sample = {
        "role":              "student",
        "category":          "AI_Lab_Support",
        "severity":          8,
        "time_sensitivity":  9,
        "crowd_level":       5,
        "eligibility_score": 3.8,
        "distance":          4
    }
    print("ANN Output:", ann_priority_layer(sample))