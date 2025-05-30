import os
import json

INPUT_MATCHED_FILE = "output/matched_members.json"
INPUT_RENAMES_FILE = "output/latest_rsn_changes.json"
OUTPUT_UPDATED_FILE = "output/updated_matched_members.json"

# Exit early if latest_rsn_changes.json is missing or empty
if not os.path.isfile(INPUT_RENAMES_FILE) or os.path.getsize(INPUT_RENAMES_FILE) == 0:
    print("ℹ️ No RSN changes to process. File is missing or empty.")
    exit(0)

# Load matched_members.json
with open(INPUT_MATCHED_FILE, "r", encoding="utf-8") as f:
    matched_members = json.load(f)

# Load latest_rsn_changes.json
with open(INPUT_RENAMES_FILE, "r", encoding="utf-8") as f:
    rsn_changes = json.load(f)

# Build index: joinedDate -> old RSN
joined_date_lookup = {}
for rsn, info in matched_members.items():
    joined = info.get("joinedDate")
    if joined:
        joined_date_lookup.setdefault(joined, {})[rsn] = info

# Create new mapping for renamed RSNs
updated_matches = {}
unmatched_renames = []

for entry in rsn_changes:
    old_rsn = entry["old_rsn"]
    new_rsn = entry["new_rsn"]
    joined_date = entry["joinedDate"]

    match_info = joined_date_lookup.get(joined_date, {}).get(old_rsn)
    if match_info:
        updated_matches[new_rsn] = match_info
    else:
        unmatched_renames.append(entry)

# Save result
os.makedirs("output", exist_ok=True)
with open(OUTPUT_UPDATED_FILE, "w", encoding="utf-8") as f:
    json.dump(updated_matches, f, indent=2)

# Print summary
print(f"✅ New RSNs matched: {len(updated_matches)}")
print(f"❌ Renames unmatched: {len(unmatched_renames)}")
if unmatched_renames:
    print("\nUnmatched renames:")
    for entry in unmatched_renames:
        print(f"  {entry['old_rsn']} → {entry['new_rsn']} (joined {entry['joinedDate']})")
