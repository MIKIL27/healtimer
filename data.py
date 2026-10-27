# TODO: verify all numbers with medical sources
# Healing durations and activity guidance are approximate typical ranges only.

ACTIVITIES = [
    "Walking",
    "Running",
    "Swimming",
    "Gym / lifting",
    "Driving",
    "Contact sports",
    "Desk work",
]

STAGES = [
    {
        "name": "Protect & rest",
        "color": "red",
        "css_class": "stage-1",
    },
    {
        "name": "Early recovery",
        "color": "orange",
        "css_class": "stage-2",
    },
    {
        "name": "Gradual return",
        "color": "yellow",
        "css_class": "stage-3",
    },
    {
        "name": "Full recovery",
        "color": "green",
        "css_class": "stage-4",
    },
]

# Each activity has four statuses, one per shared stage.
# Status values are: Allowed, Limited, or Prohibited.
CATEGORIES = {
    "sprains-strains": {
        "name": "Sprains & strains",
        "description": "Common muscle and ligament injuries.",
        "activity_matrix": {
            "Walking": ["Limited", "Allowed", "Allowed", "Allowed"],
            "Running": ["Prohibited", "Prohibited", "Limited", "Allowed"],
            "Swimming": ["Limited", "Allowed", "Allowed", "Allowed"],
            "Gym / lifting": ["Prohibited", "Limited", "Limited", "Allowed"],
            "Driving": ["Limited", "Limited", "Allowed", "Allowed"],
            "Contact sports": ["Prohibited", "Prohibited", "Prohibited", "Limited"],
            "Desk work": ["Allowed", "Allowed", "Allowed", "Allowed"],
        },
    },
    "fractures": {
        "name": "Fractures",
        "description": "Estimated timelines for uncomplicated fractures.",
        "activity_matrix": {
            "Walking": ["Limited", "Limited", "Limited", "Allowed"],
            "Running": ["Prohibited", "Prohibited", "Prohibited", "Limited"],
            "Swimming": ["Prohibited", "Limited", "Limited", "Allowed"],
            "Gym / lifting": ["Prohibited", "Prohibited", "Limited", "Limited"],
            "Driving": ["Prohibited", "Limited", "Limited", "Allowed"],
            "Contact sports": ["Prohibited", "Prohibited", "Prohibited", "Prohibited"],
            "Desk work": ["Allowed", "Allowed", "Allowed", "Allowed"],
        },
    },
    "cuts-wounds": {
        "name": "Cuts & wounds",
        "description": "Surface wounds and uncomplicated cuts.",
        "activity_matrix": {
            "Walking": ["Allowed", "Allowed", "Allowed", "Allowed"],
            "Running": ["Limited", "Limited", "Allowed", "Allowed"],
            "Swimming": ["Prohibited", "Prohibited", "Limited", "Allowed"],
            "Gym / lifting": ["Limited", "Limited", "Allowed", "Allowed"],
            "Driving": ["Limited", "Allowed", "Allowed", "Allowed"],
            "Contact sports": ["Prohibited", "Limited", "Limited", "Allowed"],
            "Desk work": ["Allowed", "Allowed", "Allowed", "Allowed"],
        },
    },
    "bruises-impact": {
        "name": "Bruises & impact",
        "description": "Bruises and minor impact injuries.",
        "activity_matrix": {
            "Walking": ["Limited", "Allowed", "Allowed", "Allowed"],
            "Running": ["Prohibited", "Limited", "Allowed", "Allowed"],
            "Swimming": ["Limited", "Allowed", "Allowed", "Allowed"],
            "Gym / lifting": ["Prohibited", "Limited", "Limited", "Allowed"],
            "Driving": ["Limited", "Allowed", "Allowed", "Allowed"],
            "Contact sports": ["Prohibited", "Prohibited", "Limited", "Allowed"],
            "Desk work": ["Allowed", "Allowed", "Allowed", "Allowed"],
        },
    },
    "burns": {
        "name": "Burns",
        "description": "Estimated ranges for minor, superficial burns.",
        "activity_matrix": {
            "Walking": ["Allowed", "Allowed", "Allowed", "Allowed"],
            "Running": ["Limited", "Limited", "Allowed", "Allowed"],
            "Swimming": ["Prohibited", "Prohibited", "Limited", "Allowed"],
            "Gym / lifting": ["Limited", "Limited", "Allowed", "Allowed"],
            "Driving": ["Allowed", "Allowed", "Allowed", "Allowed"],
            "Contact sports": ["Prohibited", "Prohibited", "Limited", "Allowed"],
            "Desk work": ["Allowed", "Allowed", "Allowed", "Allowed"],
        },
    },
}

# The per-injury activity_overrides field is optional. An override replaces
# the category's four-stage statuses for only the named activities.
INJURIES = {
    "ankle-sprain": {
        "name": "Ankle sprain",
        "category_id": "sprains-strains",
        "description": "A typical timeline for a mild to severe ankle ligament sprain.",
        "severities": {
            "mild": {"min_days": 7, "max_days": 14},
            "moderate": {"min_days": 14, "max_days": 42},
            "severe": {"min_days": 42, "max_days": 84},
        },
    },
    "wrist-sprain": {
        "name": "Wrist sprain",
        "category_id": "sprains-strains",
        "description": "A typical timeline for a wrist ligament sprain.",
        "severities": {
            "mild": {"min_days": 7, "max_days": 14},
            "moderate": {"min_days": 14, "max_days": 28},
            "severe": {"min_days": 28, "max_days": 56},
        },
        "activity_overrides": {
            "Driving": ["Allowed", "Allowed", "Allowed", "Allowed"],
        },
    },
    "hamstring-strain": {
        "name": "Hamstring strain",
        "category_id": "sprains-strains",
        "description": "A typical timeline for a hamstring muscle strain.",
        "severities": {
            "mild": {"min_days": 7, "max_days": 21},
            "moderate": {"min_days": 21, "max_days": 42},
            "severe": {"min_days": 42, "max_days": 84},
        },
    },

    "finger-fracture": {
        "name": "Finger fracture",
        "category_id": "fractures",
        "description": "A typical range for an uncomplicated finger fracture.",
        "severities": {
            "mild": {"min_days": 21, "max_days": 35},
            "moderate": {"min_days": 28, "max_days": 42},
            "severe": {"min_days": 42, "max_days": 70},
        },
    },
    "rib-fracture": {
        "name": "Rib fracture",
        "category_id": "fractures",
        "description": "A typical range for an uncomplicated rib fracture.",
        "severities": {
            "mild": {"min_days": 21, "max_days": 35},
            "moderate": {"min_days": 28, "max_days": 56},
            "severe": {"min_days": 42, "max_days": 70},
        },
    },

    "minor-cut": {
        "name": "Minor cut",
        "category_id": "cuts-wounds",
        "description": "A typical range for a small, superficial cut.",
        "severities": {
            "mild": {"min_days": 3, "max_days": 7},
            "moderate": {"min_days": 7, "max_days": 14},
            "severe": {"min_days": 14, "max_days": 28},
        },
    },
    "laceration": {
        "name": "Laceration",
        "category_id": "cuts-wounds",
        "description": "A typical range for a deeper cut after appropriate care.",
        "severities": {
            "mild": {"min_days": 7, "max_days": 14},
            "moderate": {"min_days": 14, "max_days": 28},
            "severe": {"min_days": 21, "max_days": 42},
        },
    },

    "thigh-contusion": {
        "name": "Thigh bruise",
        "category_id": "bruises-impact",
        "description": "A typical range for a soft-tissue bruise to the thigh.",
        "severities": {
            "mild": {"min_days": 3, "max_days": 7},
            "moderate": {"min_days": 7, "max_days": 21},
            "severe": {"min_days": 21, "max_days": 42},
        },
    },
    "knee-contusion": {
        "name": "Knee bruise",
        "category_id": "bruises-impact",
        "description": "A typical range for a soft-tissue bruise to the knee.",
        "severities": {
            "mild": {"min_days": 3, "max_days": 10},
            "moderate": {"min_days": 10, "max_days": 21},
            "severe": {"min_days": 21, "max_days": 42},
        },
    },
    "shoulder-contusion": {
        "name": "Shoulder bruise",
        "category_id": "bruises-impact",
        "description": "A typical range for a soft-tissue bruise to the shoulder.",
        "severities": {
            "mild": {"min_days": 3, "max_days": 10},
            "moderate": {"min_days": 10, "max_days": 21},
            "severe": {"min_days": 21, "max_days": 42},
        },
    },

    "superficial-burn": {
        "name": "Superficial burn",
        "category_id": "burns",
        "description": "A typical range for a small, superficial burn.",
        "severities": {
            "mild": {"min_days": 3, "max_days": 7},
            "moderate": {"min_days": 7, "max_days": 14},
            "severe": {"min_days": 14, "max_days": 28},
        },
    },
    "small-partial-thickness-burn": {
        "name": "Small partial-thickness burn",
        "category_id": "burns",
        "description": "A broad estimate for a small burn; medical assessment may be needed.",
        "severities": {
            "mild": {"min_days": 7, "max_days": 14},
            "moderate": {"min_days": 14, "max_days": 28},
            "severe": {"min_days": 21, "max_days": 42},
        },
    },
}
