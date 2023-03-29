from PIL import Image
from dotenv import load_dotenv
import os
import urllib.request
import json
import requests
from io import BytesIO
import numpy as np

print("imports successful")

load_dotenv()
STATLINK = os.getenv("STATLINK")

LIGHTWORDS = [40,60,80,90,100,110]
DARKWORDS = [50,70]

def getstats(dsc_id):
    with urllib.request.urlopen(STATLINK + str(dsc_id)) as url:
        data = json.load(url)
    for key in list(data.keys()):
        if data[key] is None:
            data[key] = 0
    print(data)
    cfit_ovr = ((1000/3)*(data["pointsContestFirstInTeam"]))**(1/3.5)
    csolo_ovr = ((16/5)*data["pointsContestSolo"])**(1/2)
    cteam_ovr = ((20/3)*data["pointsContestTeam"])**(1/3)
    fit_ovr = ((5/3)*data["pointsFirstInTeam"])**(1/2.5)
    solo_ovr = ((10/3)*data["pointsSolo"])**(1/2.5)
    team_ovr = ((250/3)*data["pointsTeam"])**(1/3.5)
    ovr = ((200/7)*data["pointsTotal"])**(1/3.5)

    statlist = [ovr, solo_ovr, team_ovr, fit_ovr, csolo_ovr, cteam_ovr, cfit_ovr]
    statlist = [round(_) for _ in statlist]
    return statlist

def pfp_analysis(photo_link): 
    response = requests.get(photo_link)
    img = Image.open(BytesIO(response.content))
    pix = np.array(img.getdata())
    dcount, lcount = 0,0
    for pixel in pix:
        if sum(pixel)/3 < 127.5:
            dcount += 1
        else:
            lcount += 1
    return (dcount < lcount)

    #img.show()
    

def newcard(name, stats, pfp, pfpcolor, output):
    ovr = stats[0]
    other_stats = stats[1:]

if __name__ == "__main__":
    #print(getstats("547906814663196682"))
    print(pfp_analysis("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTZfvyX_tSP6oVTSzVd5RSbk3gE_8mS8ygkFso85sBDgBRhRA&s"))
    