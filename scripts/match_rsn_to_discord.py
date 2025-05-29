import json
import csv
import os
import subprocess
import sys
from pathlib import Path
from difflib import SequenceMatcher

# Define input and output paths
data_dir = Path("data")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

clan_file = data_dir / "clan_ranks_for_bot.json"
discord_file = data_dir / "discord_members.csv"
matched_output = output_dir / "matched_members.json"
unmatched_output = output_dir / "unmatched_members.json"
unmatched_rsn_output = output_dir / "unmatched_rsn.json"

# Load OSRS clan members
with open(clan_file, "r", encoding="utf-8") as f:
    clan_data = json.load(f)

# Load Discord members
discord_members = []
with open(discord_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        discord_members.append(row)

# Define excluded roles
excluded_roles = {"EasyPoll", "MemberList", "Clan Guest"}

def is_excluded(row):
    return any(row.get(role, "").strip() for role in excluded_roles)

def fuzzy_match(name, candidates, threshold=0.85):
    best_score = 0
    best_match = None
    for candidate in candidates:
        score = SequenceMatcher(None, name.lower(), candidate.lower()).ratio()
        if score > best_score:
            best_score = score
            best_match = candidate
    return best_match if best_score >= threshold else None

matched = {}
unmatched = []
rsns = list(clan_data.keys())
matched_rsn_set = set()

for member in discord_members:
    if is_excluded(member):
        unmatched.append({
            "discord_id": member.get("ID"),
            "discord_user": member.get("User"),
            "nickname": member.get("Nickname"),
            "status": "excluded",
            "reason": "has excluded role"
        })
        continue

    user = member.get("User", "").lower()
    nick = member.get("Nickname", "").lower() if member.get("Nickname") else ""
    discord_id = member.get("ID")

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

    # Priority 5: Fuzzy match with nickname or username
    if not match and nick:
        fuzzy = fuzzy_match(nick, rsns)
        if fuzzy:
            match = fuzzy
            match_type = "fuzzy_nickname"
    if not match and user:
        fuzzy = fuzzy_match(user, rsns)
        if fuzzy:
            match = fuzzy
            match_type = "fuzzy_username"

    if match:
        if isinstance(match, list):
            for m in match:
                matched[m] = {
                    "discord_id": discord_id,
                    "discord_user": member.get("User"),
                    "nickname": member.get("Nickname"),
                    "match_type": match_type,
                    "ambiguous": True
                }
                matched_rsn_set.add(m)
        else:
            matched[match] = {
                "discord_id": discord_id,
                "discord_user": member.get("User"),
                "nickname": member.get("Nickname"),
                "match_type": match_type,
                "ambiguous": ambiguous
            }
            matched_rsn_set.add(match)
    else:
        unmatched.append({
            "discord_id": discord_id,
            "discord_user": member.get("User"),
            "nickname": member.get("Nickname"),
            "status": "unmatched",
            "reason": "no match"
        })

# Determine RSNs with no matching Discord
unmatched_rsn = [
    {"rsn": rsn, "status": "unmatched", "reason": "no matching Discord account"}
    for rsn in rsns if rsn not in matched_rsn_set
]

# Write results
with open(matched_output, "w", encoding="utf-8") as f:
    json.dump(matched, f, indent=2)

with open(unmatched_output, "w", encoding="utf-8") as f:
    json.dump(unmatched, f, indent=2)

with open(unmatched_rsn_output, "w", encoding="utf-8") as f:
    json.dump(unmatched_rsn, f, indent=2)

# Commit changes to the repo safely
try:
    subprocess.run(["git", "add", str(matched_output), str(unmatched_output), str(unmatched_rsn_output)], check=True)
    subprocess.run(["git", "commit", "-m", "Update RSN to Discord match results"], check=True)
    subprocess.run(["git", "push"], check=True)
except subprocess.CalledProcessError as e:
    print("Git subprocess failed:", e)

print(f"Matched: {len(matched)}")
print(f"Unmatched Discord users: {len(unmatched)}")
print(f"Unmatched RSNs: {len(unmatched_rsn)}")

sys.exit(0)
