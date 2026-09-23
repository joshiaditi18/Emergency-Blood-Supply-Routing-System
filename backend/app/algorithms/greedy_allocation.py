"""Manual greedy blood allocation.

Each selection scans the remaining candidates and takes from the hospital
with the greatest currently available compatible inventory. This is O(H^2)
in the number of candidates and uses O(H) space.
"""


from backend.app.utils.blood_compatibility import compatible_donor_groups


def _value(candidate, name):
    if isinstance(candidate, dict):
        return candidate.get(name)
    return getattr(candidate, name, None)


def allocate_blood(required_units, inventory_candidates, blood_group=None):
    """Allocate units greedily from compatible hospital inventory records."""
    if isinstance(required_units, bool) or not isinstance(required_units, int) or required_units <= 0:
        raise ValueError("required_units must be a positive integer")
    if blood_group is not None:
        blood_group = blood_group.upper()
        donor_groups = compatible_donor_groups(blood_group)

    remaining_candidates = []
    for candidate in inventory_candidates:
        units = _value(candidate, "units_available")
        candidate_group = _value(candidate, "blood_group")
        if isinstance(units, bool) or not isinstance(units, int) or units < 0:
            raise ValueError("inventory units must be a non-negative integer")
        if blood_group and candidate_group and candidate_group.upper() not in donor_groups:
            continue
        remaining_candidates.append({"candidate": candidate, "available": units})

    remaining = required_units
    allocations = []
    allocation_steps = []
    while remaining and remaining_candidates:
        best_index = 0
        for index in range(1, len(remaining_candidates)):
            if remaining_candidates[index]["available"] > remaining_candidates[best_index]["available"]:
                best_index = index
        selected = remaining_candidates[best_index]
        taken = min(remaining, selected["available"])
        if taken == 0:
            remaining_candidates.pop(best_index)
            continue
        hospital_id = _value(selected["candidate"], "hospital_id")
        allocation = {"hospital_id": hospital_id, "units_taken": taken}
        inventory_id = _value(selected["candidate"], "id")
        if inventory_id is not None:
            allocation["inventory_id"] = inventory_id
        allocations.append(allocation)
        step = {
            "hospital_id": hospital_id,
            "available_before": selected["available"],
            "units_taken": taken,
            "remaining_required": remaining - taken,
        }
        if inventory_id is not None:
            step["inventory_id"] = inventory_id
        allocation_steps.append(step)
        selected["available"] -= taken
        remaining -= taken
        if selected["available"] == 0:
            remaining_candidates.pop(best_index)

    return {
        "required_units": required_units,
        "allocated_units": required_units - remaining,
        "remaining_units": remaining,
        "selected_hospitals": [allocation["hospital_id"] for allocation in allocations],
        "allocations": allocations,
        "allocation_steps": allocation_steps,
        "status": "COMPLETED" if remaining == 0 else "FAILED",
    }
