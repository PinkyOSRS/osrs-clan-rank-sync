import os
import glob
import json

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

    # Index joined and left by join date
    joined_by_date = {}
    for rsn, jd in joined:
        joined_by_date.setdefault(jd, []).append(rsn)

    left_by_date = {}
    for rsn, jd in left:
        left_by_date.setdefault(jd, []).append(rsn)

    renamed = []
    for jd in joined_by_date.keys() & left_by_date.keys():
        for old_rsn in left_by_date[jd]:
            for new_rsn in joined_by_date[jd]:
                renamed.append({
                    "joinedDate": jd,
                    "old_rsn": old_rsn,
                    "new_rsn": new_rsn
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

    print(f"Comparing:\n  Newest: {newest_file}\n  Older: {second_newest_file}\n")

    print("\n🔁 Likely RSN Changes:")
    if not renamed:
        print("  None detected.")
    else:
        for entry in renamed:
            print(f"  {entry['old_rsn']} → {entry['new_rsn']} (joined {entry['joinedDate']})")

if __name__ == "__main__":
    main()
