import urllib.request
import json
import matplotlib.pyplot as plt
import time

STATLINK = "https://kronos.elusive-dev.com/api/Stats/Player/"
MODES = ["pointsTotal", "pointsSolo", "pointsContestSolo", "pointsTeam", "pointsContestTeam", "pointsFirstInTeam", "pointsContestFirstInTeam"]

def get_all_ids(point_threshold=None):
    with urllib.request.urlopen("https://kronos.elusive-dev.com/api/Leaderboard/10000/0") as url:
        data = json.load(url)
    allids = []
    allentries = data["entries"]
    for entry in allentries:
        if point_threshold and entry["points"] >= point_threshold:
            allids.append(entry["id"])
    return allids

def get_points_data_mode(mode, allids, show=False):
    point_list = []
    x_coords = []
    count = 1
    st = time.time()
    for dsc_id in allids:
        print("Requesting data for", dsc_id, count, "out of", len(allids), "Time", str(time.time()-st))
        with urllib.request.urlopen(STATLINK + str(dsc_id)) as url:
            data = json.load(url)
        points = 0
        for mod in mode:
            if data[mod] is not None:
                print("For", mod, str(dsc_id), "has", data[mod], "points")
                points += data[mod]
        point_list.append(points)
        x_coords.append(count)
        count += 1
    if show:
        fig = plt.bar(x_coords, point_list)
        plt.savefig("figures/" + str(mode[0]) + ".svg")
        plt.close()
    return point_list

if __name__ == "__main__":
    allids = get_all_ids(point_threshold=5000)
    allpointlist = []
    for mode in ["pointsSolo"]:
        point_list = get_points_data_mode([mode], allids, show=True)
        print(point_list)
        point_list = [mode] + point_list
        allpointlist.append(point_list)
    with open("data.txt", "w") as file:
        file.write(str(allpointlist))
