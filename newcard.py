from PIL import Image, ImageDraw, ImageFont
from dotenv import load_dotenv
import os
import urllib.request
import json
import requests
import random
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
    if data["pointsTotal"] < 5000:
        return False
    cfit_ovr = ((1000/3)*(data["pointsContestFirstInTeam"]))**(1/3.5)
    csolo_ovr = ((16/5)*data["pointsContestSolo"])**(1/2)
    cteam_ovr = ((20/3)*data["pointsContestTeam"])**(1/3)
    fit_ovr = ((5/3)*data["pointsFirstInTeam"])**(1/2.5)
    solo_ovr = ((10/3)*data["pointsSolo"])**(1/2.5)
    team_ovr = ((250/3)*data["pointsTeam"])**(1/3.5)
    ovr = ((200/7)*data["pointsTotal"])**(1/3.5)

    totalsolo = data["pointsSolo"] + data["pointsContestSolo"]
    totalteam = data["pointsTeam"] + data["pointsContestTeam"]
    totalfit = data["pointsFirstInTeam"] + data["pointsContestFirstInTeam"]

    print(totalsolo, totalteam, totalfit)

    if (totalsolo / totalteam) > 0.6:
        pos = "ST"
    elif (totalsolo / totalteam) > 0.2:
        pos = "CF"
    elif (totalfit / totalteam) > 0.6:
        pos = "AM"
    elif (totalfit / totalteam) > 0.3:
        pos = "LM" if ovr % 2 == 0 else "RM"
    elif (totalsolo + totalfit) / totalteam > 0.8:
        pos = "LW" if ovr % 2 == 0 else "RW"
    elif (totalteam / (totalsolo + totalfit)) > 3.5:
        pos = "GK"
    elif (totalteam / (totalsolo + totalfit)) > 2.2:
        pos = "CB"
    elif (totalteam / (totalsolo + totalfit)) > 1.5:
        pos = "LB" if ovr % 2 == 0 else "RB"
    else:
        pos = "CM"

    statlist = [ovr, solo_ovr, team_ovr, fit_ovr, csolo_ovr, cteam_ovr, cfit_ovr]
    statlist = [round(_) for _ in statlist]
    return statlist, pos

def genfont(type, size):
    return ImageFont.truetype('card_designs/' + type + '.ttf', size, layout_engine=ImageFont.LAYOUT_BASIC)

def newcard(name, stats, pos, pfp, output, nat=None, quote=None):
    ovr = stats[0]
    card_background = Image.open("card_designs/" + str(int(ovr/10)*10) + ".png")
    card_background = card_background.resize((1288,1800))
    card_background = card_background.convert("RGBA")
    response = requests.get(pfp)
    pfp = Image.open(BytesIO(response.content)).convert("RGBA")
    pfp = pfp.resize((450,450))
    card_background.paste(pfp, (600,250), pfp)
    print(card_background.size)
    carddraw = ImageDraw.Draw(card_background)
    print(str(ovr))
    carddraw.text((290,350), str(ovr), (255,215,0), font=genfont("EA", 150), stroke_width=1)
    carddraw.text((290,525), str(pos), (255,255,255), font=genfont("EA", 100), stroke_width=1)
    w, h = carddraw.textsize(name, font=genfont("arial", int(175/(len(name)**(1/2)))))
    carddraw.text((825-(w/2),700), name, (255,215,0), font=genfont("arial", int(175/(len(name)**(1/2)))), stroke_width=2)
    if quote:
        quote = str(quote)
        w, h = carddraw.textsize(quote, font=genfont("arial", int(275/(len(quote)**(1/2)))), stroke_width=2)
        carddraw.text((644-(w/2),800), quote, font=genfont("arial", int(275/(len(quote)**(1/2)))))
    carddraw.text((250,1150), "SOLO  " + str(stats[1]), font=genfont("EA", 65))
    carddraw.text((250,1250), "TEAM  " + str(stats[2]), font=genfont("EA", 65))
    carddraw.text((250,1350), "FIT   " + str(stats[3]), font=genfont("EA", 65))
    carddraw.text((800,1150), "CSOLO " + str(stats[4]), font=genfont("EA", 65))
    carddraw.text((800,1250), "CTEAM " + str(stats[5]), font=genfont("EA", 65))
    carddraw.text((800,1350), "CFIT  " + str(stats[6]), font=genfont("EA", 65))
    status = True
    if nat:
        try:
            flag = Image.open("flags/" + nat + ".png").convert("RGBA")
            flag = flag.resize((120,72))
            card_background.paste(flag, (300,650))
        except:
            status = False
    return card_background, status

if __name__ == "__main__":
    #print(pfp_analysis("https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTZfvyX_tSP6oVTSzVd5RSbk3gE_8mS8ygkFso85sBDgBRhRA&s"))
    #937082904616513577
    #547906814663196682
    #1035502624893566977
    #400296877230260224
    #361385665998618634
    pass