import json
import csv
import os
from pathlib import Path

# Define input and output paths
data_dir = Path("data")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

clan_file = data_dir / "clan_ranks_for_bot.json"
discord_file = data_dir / "discord_members.csv"
matched_output = output_dir / "matched_members.json"
unmatched_output = output_dir / "unmatched_members.json"

# Load OSRS clan members
with open(clan_file, "r", encoding="utf-8") as f:
    clan_data = json.load(f)

# Load Discord members
discord_members = []
with open(discord_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        discord_members.append({
            "user": row.get("User", "").strip(),
            "id": row.get("ID", "").strip(),
            "nickname": row.get("Nickname", "").strip()
        })

matched = {}
unmatched = []
rsns = list(clan_data.keys())

for member in discord_members:
    user = member["user"].lower()
    nick = member["nickname"].lower() if member["nickname"] else ""
    discord_id = member["id"]

    match = None
    match_type = None
    ambiguous = False

    # Priority 1: exact match with nickname
    for rsn in rsns:
        if nick and rsn.lower() == nick:
            match = rsn
            match_type = "exact_nickname"
            break

    # Priority 2: exact match with username
    if not match:
        for rsn in rsns:
            if rsn.lower() == user:
                match = rsn
                match_type = "exact_username"
                break

    # Priority 3: RSN contains nickname
    if not match and nick:
        candidates = [rsn for rsn in rsns if nick in rsn.lower()]
        if len(candidates) == 1:
            match = candidates[0]
            match_type = "rsn_contains_nick"
        elif len(candidates) > 1:
            match = candidates
            match_type = "rsn_contains_nick"
            ambiguous = True

    # Priority 4: Nickname contains RSN
    if not match and nick:
        candidates = [rsn for rsn in rsns if rsn.lower() in nick]
        if len(candidates) == 1:
            match = candidates[0]
            match_type = "nick_contains_rsn"
        elif len(candidates) > 1:
            match = candidates
            match_type = "nick_contains_rsn"
            ambiguous = True

    if match:
        if isinstance(match, list):
            for m in match:
                matched[m] = {
                    "discord_id": discord_id,
                    "discord_user": member["user"],
                    "nickname": member["nickname"],
                    "match_type": match_type,
                    "ambiguous": True
                }
        else:
            matched[match] = {
                "discord_id": discord_id,
                "discord_user": member["user"],
                "nickname": member["nickname"],
                "match_type": match_type,
                "ambiguous": ambiguous
            }
    else:
        unmatched.append({
            "discord_id": discord_id,
            "discord_user": member["user"],
            "nickname": member["nickname"],
            "reason": "no match"
        })

# Write results
with open(matched_output, "w", encoding="utf-8") as f:
    json.dump(matched, f, indent=2)

with open(unmatched_output, "w", encoding="utf-8") as f:
    json.dump(unmatched, f, indent=2)

print(f"Matched: {len(matched)}")
print(f"Unmatched: {len(unmatched)}")

