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
excluded_roles = {"EasyPoll", "MemberList", "Clan Guest"}

def is_excluded(row):
    return any(row.get(role, "").strip() for role in excluded_roles)

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
        "ambiguous": False
    }
    matched_rsn_set.add(rsn)

manually_matched_ids = {info.get("discord_id") for info in manual_matches.values()}

for member in discord_members:
    if is_excluded(member):
        excluded.append({
            "discord_id": member.get("ID"),
            "discord_user": member.get("User"),
            "nickname": member.get("Nickname"),
            "status": "excluded",
            "reason": "has excluded role"
        })
        continue

    discord_id = member.get("ID")
    if discord_id in manually_matched_ids:
        continue

    user = member.get("User", "")
    nick = member.get("Nickname", "")
    if not nick:
        print(f"[WARN] No nickname for user {user} ({discord_id})")
        nick = user

    match = None
    match_type = None
    ambiguous = False

    # Normalize all inputs
    stripped_user = strip_suffix_digits(user)
    norm_user = normalize(stripped_user)
    norm_nick = normalize(nick)

    # Priority 1: normalized match with nickname
    if norm_nick in normalized_rsns:
        match = normalized_rsns[norm_nick]
        match_type = "normalized_nickname"

    # Priority 2: normalized match with username
    if not match and norm_user in normalized_rsns:
        match = normalized_rsns[norm_user]
        match_type = "normalized_username"

    # Priority 3: RSN contains nickname (normalized)
    if not match and norm_nick:
        candidates = [rsn for rsn in rsns if norm_nick in normalize(rsn)]
        if len(candidates) == 1:
            match = candidates[0]
            match_type = "rsn_contains_nick"
        elif len(candidates) > 1:
            match = candidates
            match_type = "rsn_contains_nick"
            ambiguous = True

    # Priority 4: Nickname contains RSN (normalized)
    if not match and norm_nick:
        candidates = [rsn for rsn in rsns if normalize(rsn) in norm_nick]
        if len(candidates) == 1:
            match = candidates[0]
            match_type = "nick_contains_rsn"
        elif len(candidates) > 1:
            match = candidates
            match_type = "nick_contains_rsn"
            ambiguous = True

    # Priority 4.5: Discord user contains RSN (normalized)
    if not match and norm_user:
        candidates = [rsn for rsn in rsns if normalize(rsn) in norm_user]
        if len(candidates) == 1:
            match = candidates[0]
            match_type = "user_contains_rsn"
        elif len(candidates) > 1:
            match = candidates
            match_type = "user_contains_rsn"
            ambiguous = True

    # Priority 5: Fuzzy match with normalized nickname or username
    if not match and norm_nick:
        fuzzy = fuzzy_match(norm_nick, [normalize(rsn) for rsn in rsns])
        if fuzzy:
            for norm_key, original_rsn in normalized_rsns.items():
                if normalize(norm_key) == fuzzy:
                    match = original_rsn
                    match_type = "fuzzy_nickname"
                    break

    if not match and norm_user:
        fuzzy = fuzzy_match(norm_user, [normalize(rsn) for rsn in rsns])
        if fuzzy:
            for norm_key, original_rsn in normalized_rsns.items():
                if normalize(norm_key) == fuzzy:
                    match = original_rsn
                    match_type = "fuzzy_username"
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
                        "ambiguous": True
                    }
                    matched_rsn_set.add(m)
        else:
            if match not in matched:
                matched[match] = {
                    "discord_id": discord_id,
                    "discord_user": user,
                    "nickname": nick,
                    "match_type": match_type,
                    "ambiguous": ambiguous
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
