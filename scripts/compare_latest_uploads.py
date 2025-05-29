import os
import glob
import json
from datetime import datetime

UPLOADS_DIR = "uploads"

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

    # Detect RSN changes by matching joinedDate
    join_dates_to_rsn_new = {jd: rsn for rsn, jd in joined}
    join_dates_to_rsn_old = {jd: rsn for rsn, jd in left}

    renamed = []
    for jd in set(join_dates_to_rsn_new.keys()).intersection(join_dates_to_rsn_old.keys()):
        renamed.append({
            "old_rsn": join_dates_to_rsn_old[jd],
            "new_rsn": join_dates_to_rsn_new[jd],
            "joinedDate": jd
        })

    # Filter out renamed from joined/left
    renamed_dates = {r["joinedDate"] for r in renamed}
    joined_clean = [(rsn, jd) for rsn, jd in joined if jd not in renamed_dates]
    left_clean = [(rsn, jd) for rsn, jd in left if jd not in renamed_dates]

    return joined_clean, left_clean, renamed

def main():
    files = get_sorted_clanrank_files()
    if len(files) < 2:
        print("Need at least two clanrank JSON files to compare.")
        return

    newest_file = files[0]
    second_newest_file = files[1]

    joined, left, renamed = compare_clan_files(newest_file, second_newest_file)

    print(f"Comparing:\n  Newest: {newest_file}\n  Older: {second_newest_file}\n")

    print("\n🟢 Joined:")
    for rsn, date in sorted(joined):
        print(f"  {rsn} (joined {date})")

    print("\n🔴 Left:")
    for rsn, date in sorted(left):
        print(f"  {rsn} (joined {date})")

    print("\n🔁 Renamed:")
    for entry in renamed:
        print(f"  {entry['old_rsn']} → {entry['new_rsn']} (joined {entry['joinedDate']})")

if __name__ == "__main__":
    main()
