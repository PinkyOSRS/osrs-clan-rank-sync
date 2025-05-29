import json
import csv
import os
import subprocess
import sys
import re
from pathlib import Path
from difflib import SequenceMatcher

print("[DEBUG] Script started...")

# Define input and output paths
data_dir = Path("data")
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Adjusted path: clan file is in root directory
clan_file = Path("clan_ranks_for_bot.json")
discord_file = data_dir / "discord_members.csv"
manually_matched_file = data_dir / "manual_matches.json"
matched_output = output_dir / "matched_members.json"
unmatched_output = output_dir / "unmatched_members.json"
unmatched_rsn_output = output_dir / "unmatched_rsn.json"
excluded_output = output_dir / "excluded_members.json"

# Load OSRS clan members
with open(clan_file, "r", encoding="utf-8") as f:
    clan_data = json.load(f)

# Load Discord members
discord_members = []
with open(discord_file, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        discord_members.append(row)

# Load manual matches
manual_matches = {}
if manually_matched_file.exists():
    with open(manually_matched_file, "r", encoding="utf-8") as f:
        manual_matches = json.load(f)

# Define excluded roles
excluded_roles = {"EasyPoll", "MemberList", "Clan Guest", "Memberlist2.0"}

def is_excluded(row):
    roles_raw = row.get("Roles", "")
    roles = {r.strip() for r in roles_raw.split(",") if r.strip()}
    return bool(excluded_roles & roles)

def normalize(name):
    return re.sub(r'[^a-z0-9]', '', name.lower()) if name else ""

def strip_suffix_digits(name):
    return re.sub(r'\d{2,4}$', '', name)

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
excluded = []
rsns = list(clan_data.keys())
normalized_rsns = {normalize(rsn): rsn for rsn in rsns}
matched_rsn_set = set()

# Add manual matches first
for rsn, match_info in manual_matches.items():
    matched[rsn] = {
        "discord_id": match_info.get("discord_id"),
        "discord_user": match_info.get("discord_user"),
        "nickname": match_info.get("nickname"),
        "match_type": "manual",
        "ambiguous": False,
        "rank": clan_data.get(rsn, {}).get("rank"),
        "joinedDate": clan_data.get(rsn, {}).get("joinedDate")
    }
    matched_rsn_set.add(rsn)

# === Skip already manually matched Discord IDs ===
manually_matched_ids = {m["discord_id"] for m in matched.values()}

for member in discord_members:
    if member.get("ID") in manually_matched_ids:
        continue

    if is_excluded(member):
        excluded.append({
            "discord_id": member.get("ID"),
            "discord_user": member.get("User"),
            "nickname": member.get("Nickname"),
            "status": "excluded",
            "reason": "has excluded role"
        })
        continue

    user = member.get("User", "")
    global_name = member.get("Global Display Name", "")
    nick = member.get("Nickname", "")
    if not nick:
        nick = global_name or user
    discord_id = member.get("ID")

    match = None
    match_type = None
    ambiguous = False

    # Normalize all inputs
    stripped_user = strip_suffix_digits(user)
    norm_user = normalize(stripped_user)
    norm_nick = normalize(nick)
    norm_global = normalize(global_name)

    # Priority 1: normalized match with nickname
    if norm_nick in normalized_rsns:
        match = normalized_rsns[norm_nick]
        match_type = "normalized_nickname"

    # Priority 2: normalized match with global name
    if not match and norm_global in normalized_rsns:
        match = normalized_rsns[norm_global]
        match_type = "normalized_globalname"

    # Priority 3: normalized match with username
    if not match and norm_user in normalized_rsns:
        match = normalized_rsns[norm_user]
        match_type = "normalized_username"

    # Priority 4: RSN contains nickname/global/user
    for norm_val, label in [(norm_nick, "nick"), (norm_global, "global"), (norm_user, "user")]:
        if not match and norm_val:
            candidates = [rsn for rsn in rsns if norm_val in normalize(rsn)]
            if len(candidates) == 1:
                match = candidates[0]
                match_type = f"rsn_contains_{label}"
                break
            elif len(candidates) > 1:
                match = candidates
                match_type = f"rsn_contains_{label}"
                ambiguous = True
                break

    # Priority 5: Nickname/global/user contains RSN
    for norm_val, label in [(norm_nick, "nick"), (norm_global, "global"), (norm_user, "user")]:
        if not match and norm_val:
            candidates = [rsn for rsn in rsns if normalize(rsn) in norm_val]
            if len(candidates) == 1:
                match = candidates[0]
                match_type = f"{label}_contains_rsn"
                break
            elif len(candidates) > 1:
                match = candidates
                match_type = f"{label}_contains_rsn"
                ambiguous = True
                break

    # Priority 6: Fuzzy match nickname/global/user
    for norm_val, label in [(norm_nick, "fuzzy_nickname"), (norm_global, "fuzzy_globalname"), (norm_user, "fuzzy_username")]:
        if not match and norm_val:
            fuzzy = fuzzy_match(norm_val, [normalize(rsn) for rsn in rsns])
            if fuzzy:
                for norm_key, original_rsn in normalized_rsns.items():
                    if normalize(norm_key) == fuzzy:
                        match = original_rsn
                        match_type = label
                        break

    if match:
        if isinstance(match, list):
            for m in match:
                if m not in matched:
                    matched[m] = {
                        "discord_id": discord_id,
                        "discord_user": user,
                        "nickname": nick,
                        "match_type": match_type,
                        "ambiguous": True,
                        "rank": clan_data.get(m, {}).get("rank"),
                        "joinedDate": clan_data.get(m, {}).get("joinedDate")
                    }
                    matched_rsn_set.add(m)
        else:
            if match not in matched:
                matched[match] = {
                    "discord_id": discord_id,
                    "discord_user": user,
                    "nickname": nick,
                    "match_type": match_type,
                    "ambiguous": ambiguous,
                    "rank": clan_data.get(match, {}).get("rank"),
                    "joinedDate": clan_data.get(match, {}).get("joinedDate")
                }
                matched_rsn_set.add(match)
    else:
        unmatched.append({
            "discord_id": discord_id,
            "discord_user": user,
            "nickname": nick,
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

with open(excluded_output, "w", encoding="utf-8") as f:
    json.dump(excluded, f, indent=2)

# Commit changes to the repo safely
try:
    subprocess.run(["git", "add", str(matched_output), str(unmatched_output), str(unmatched_rsn_output), str(excluded_output)], check=False)
    subprocess.run(["git", "commit", "-m", "Update RSN to Discord match results"], check=False)
    subprocess.run(["git", "push"], check=False)
except Exception as e:
    print("Git subprocess failed:", e)

print(f"Matched: {len(matched)}")
print(f"Unmatched Discord users: {len(unmatched)}")
print(f"Unmatched RSNs: {len(unmatched_rsn)}")
print(f"Excluded Discord users: {len(excluded)}")
print("[DEBUG] Script finished. Exiting.")
sys.exit(0)
