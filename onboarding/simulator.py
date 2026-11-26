"""Simulator roster. Actor ids use the same spelling as the intake page."""

ROSTER = (
    {"actor_id": "actor-alex-rivera", "actor_role": "hr_coordinator", "name": "Alex Rivera"},
    {"actor_id": "actor-taylor-brooks", "actor_role": "it_fulfiller", "name": "Taylor Brooks"},
    {"actor_id": "actor-sam-ortiz", "actor_role": "hiring_manager", "name": "Sam Ortiz"},
    {"actor_id": "actor-morgan-hale", "actor_role": "hiring_manager", "name": "Morgan Hale"},
    {"actor_id": "actor-jordan-lee", "actor_role": "new_hire", "name": "Jordan Lee"},
    {"actor_id": "actor-riley-chen", "actor_role": "new_hire", "name": "Riley Chen"},
)

EQUIPMENT_OWNER_ID = "actor-taylor-brooks"


def find_identity(actor_id: str, actor_role: str) -> dict | None:
    """Both fields must match one configured person. A role alone matches nobody."""
    for person in ROSTER:
        if person["actor_id"] == actor_id and person["actor_role"] == actor_role:
            return person
    return None


def is_equipment_owner(person: dict) -> bool:
    return person["actor_id"] == EQUIPMENT_OWNER_ID and person["actor_role"] == "it_fulfiller"
