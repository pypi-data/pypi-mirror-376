def acct_to_fediverse(acct_uri: str) -> str:
    return acct_uri.replace("acct:", "@")


def gather_property_values(attachments: list[dict]) -> list[dict]:
    return [
        {"name": a.get("name"), "value": a.get("value")}
        for a in attachments
        if a.get("type") == "PropertyValue"
    ]


def format_actor_profile(profile: dict) -> dict:
    acct_uris = [x for x in profile.get("identifiers", []) if x.startswith("acct:")]
    return {
        "fediverse_handles": [acct_to_fediverse(x) for x in acct_uris],
        "property_values": gather_property_values(profile.get("attachment", [])),
    }
