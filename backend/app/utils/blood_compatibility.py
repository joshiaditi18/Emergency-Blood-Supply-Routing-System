"""Single source of truth for red blood cell donor compatibility."""

BLOOD_GROUPS = ("O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+")

# Keys are recipient groups; values are compatible donor groups.
DONOR_GROUPS = {
    "O-": frozenset({"O-"}),
    "O+": frozenset({"O-", "O+"}),
    "A-": frozenset({"O-", "A-"}),
    "A+": frozenset({"O-", "O+", "A-", "A+"}),
    "B-": frozenset({"O-", "B-"}),
    "B+": frozenset({"O-", "O+", "B-", "B+"}),
    "AB-": frozenset({"O-", "A-", "B-", "AB-"}),
    "AB+": frozenset(BLOOD_GROUPS),
}


def compatible_donor_groups(recipient_group: str) -> frozenset[str]:
    normalized = recipient_group.upper()
    try:
        return DONOR_GROUPS[normalized]
    except KeyError as exc:
        raise ValueError("invalid blood group") from exc


def is_compatible_donor(recipient_group: str, donor_group: str) -> bool:
    return donor_group.upper() in compatible_donor_groups(recipient_group)
