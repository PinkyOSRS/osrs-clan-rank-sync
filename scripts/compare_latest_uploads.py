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
        return {(m["rsn"], m["joinedDate"]) for m in data.get("clanMemberMaps", [])}

def compare_clan_files(newest_file, older_file):
    newest_members = load_clan_members(newest_file)
    older_members = load_clan_members(older_file)

    joined = newest_members - older_members
    left = older_members - newest_members

    return joined, left

def main():
    files = get_sorted_clanrank_files()
    if len(files) < 2:
        print("Need at least two clanrank JSON files to compare.")
        return

    newest_file = files[0]
    second_newest_file = files[1]

    joined, left = compare_clan_files(newest_file, second_newest_file)

    print(f"Comparing:\n  Newest: {newest_file}\n  Older: {second_newest_file}\n")

    print("\n🟢 Joined:")
    for rsn, date in sorted(joined):
        print(f"  {rsn} (joined {date})")

    print("\n🔴 Left:")
    for rsn, date in sorted(left):
        print(f"  {rsn} (joined {date})")

if __name__ == "__main__":
    main()
