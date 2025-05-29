import os
import glob
import json

UPLOADS_DIR = "uploads"
OUTPUT_FILE = "latest_rsn_changes.json"

def get_sorted_clanrank_files():
    files = glob.glob(os.path.join(UPLOADS_DIR, "clanrank_*.json"))
    return sorted(files, key=lambda f: os.path.getmtime(f), reverse=True)

def load_clan_members(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("clanMemberMaps", [])

def compare_clan_files(newest_file, older_file):
    new_data = load_clan_members(newest_file)
    old_data = load_clan_members(older_file)

    new_set = {(m["rsn"], m["joinedDate"]) for m in new_data}
    old_set = {(m["rsn"], m["joinedDate"]) for m in old_data}

    joined = new_set - old_set
    left = old_set - new_set

    # Index by joinedDate
    joined_by_date = {}
    for rsn, jd in joined:
        joined_by_date.setdefault(jd, []).append(rsn)

    left_by_date = {}
    for rsn, jd in left:
        left_by_date.setdefault(jd, []).append(rsn)

    renamed = []
    for jd in joined_by_date.keys() & left_by_date.keys():
        if len(joined_by_date[jd]) == 1 and len(left_by_date[jd]) == 1:
            renamed.append({
                "joinedDate": jd,
                "old_rsn": left_by_date[jd][0],
                "new_rsn": joined_by_date[jd][0]
            })

    return renamed

def main():
    files = get_sorted_clanrank_files()
    if len(files) < 2:
        print("Need at least two clanrank JSON files to compare.")
        return

    newest_file = files[0]
    second_newest_file = files[1]

    renamed = compare_clan_files(newest_file, second_newest_file)

    # Write JSON output
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(renamed, f, indent=2)
    
    print(f"Comparing:\n  Newest: {newest_file}\n  Older: {second_newest_file}")
    print(f"\n🔁 Detected {len(renamed)} likely RSN changes (saved to {OUTPUT_FILE}):")

    for entry in renamed:
        print(f"  {entry['old_rsn']} → {entry['new_rsn']} (joined {entry['joinedDate']})")

if __name__ == "__main__":
    main()
