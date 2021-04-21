import requests
import pandas as pd
from bs4 import BeautifulSoup
from conf import CODE, INF, NINF, USERN, PASSW

def showDays(DFs, num= 0, NewDF= pd.DataFrame(columns= NINF), MAIN= True):
    for n, date in enumerate(DFs):
        if DFs[date].shape[0]:
            if MAIN:
                tbo = DFs[date][DFs[date][INF[2]]== CODE[0]].copy()
                avail = DFs[date][DFs[date][INF[2]]== CODE[2]].copy()
                wait = DFs[date][DFs[date][INF[2]]== CODE[3]].copy()
                t, a, w = tbo.shape[0], avail.shape[0], wait.shape[0]
                if any([t,a,w]):
                    print(f"------------------------ \n"
                          f"For {date}:\n")
                else:
                    continue

                if w:
                    num += w
                    wait.insert(0, NINF[0], [date for i in range(w)])
                    wait[NINF[-2]] = [0 for i in range(w)]
                    wait[NINF[-1]] = [i+1 for i in range(num-w, num)]
                    NewDF = NewDF.append(wait, ignore_index=True)
                    print(f"You can go on the waitlist for the following class(es)\n"
                          f"{wait[[INF[0], INF[1], NINF[-1]]].to_string(index=False)}\n")
                if a:
                    num += a
                    avail.insert(0, NINF[0], [date for i in range(a)])
                    avail[NINF[-2]] = [0 for i in range(a)]
                    avail[NINF[-1]] = [i+1 for i in range(num-a, num)]
                    NewDF = NewDF.append(avail, ignore_index=True)
                    print(f"You can already sign up for the following class(es)\n"
                          f"{avail[[INF[0], INF[1], NINF[-1]]].to_string(index=False)}\n")
                if t:
                    num += t
                    tbo.insert(0, NINF[0], [date for i in range(t)])
                    tbo[NINF[-2]] = [0 for i in range(t)]
                    tbo[NINF[-1]] = [i + 1 for i in range(num- t, num)]
                    NewDF = NewDF.append(tbo, ignore_index=True)
                    print(f"You can start auto-signup for the following class(es)\n"
                          f"{tbo[[INF[0], INF[1],INF[3], NINF[-1]]].to_string(index=False)}\n")
            else:
                print(f"---------------------\n"
                      f"For {date}:\tCODE:{n}\n\n"
                      f"(The availability may have changed, remove the day to check again.)\n"
                      f"{DFs[date][[INF[0], INF[1], INF[2]]].to_string(index= False)}\n")

    return (NewDF, num)

def convertTime(time):
    if "pm" in time:
        mn = time.split("pm")[0].split(":")[1]
        time = int(time.split(":")[0])
        return f"{time+12}:{mn}:00"

    elif "am" in time:
        return time.replace("am", ":00")

def passForm(token):
    form = {i["name"]: i["value"] for i in token}
    form["login"] = USERN
    form["password"] = PASSW
    form["submit"] = 'Login'
    return form

def getInfo(link):
    with requests.Session() as s:
        print(link)
        R = s.get(link)
        Soup = BeautifulSoup(R.text, "lxml")
        token = Soup.find_all(attrs= {"type": "hidden"})
        form = passForm(token)
        # print(form)

        response = s.post(R.url, data= form)
        response = s.get(response.url)
        sop = BeautifulSoup(response.text, "lxml")

        inf = [*INF]
        alerts = sop.find_all(class_= "alert alert-error")
        if alerts:
            spts = int(sop.find(class_= "title").small.text.split()[0])
            if spts and "Reservations for this class are now closed." not in alerts[0].text:
                inf[2] = CODE[0]
                inf[3] = alerts[0].text.split("starts on ")[-1].replace(" at "," ").split(".")[0]
                inf[3] = f"{inf[3].split()[0]} {convertTime(inf[3].split()[1])}"
            else:
                inf[2] = CODE[1]
                inf[3] = 0
        else:
            spts = int(sop.find(class_= "title").small.text.split()[0])
            if spts:
                inf[2] = CODE[2]
                inf[3] = 0
            else:
                inf[2] = CODE[3]
                inf[3] = 0


        inf[0] = " ".join(sop.find("h2").text.split()[:2])
        inf[1] = sop.find("h2").small.text
        inf[4] = link
    return inf


def reqForm(token):
    form = {i["name"]:i["value"] for i in token}
    if "action" in form:
        if form["action"] == "waitlist":
            form["submit"] = "Join the Waitlist"
        elif form["action"]== "reserve":
            form["submit"] = "Reserve a Spot"
    else:
        print("'action' wasn't in form, this relates to the error I once had,\n"
              "check if everything is well.")
    return form

def makeReq(link):
    with requests.Session() as s:

    # On the login page:
        R = s.get(link)
        Soup = BeautifulSoup(R.text, "lxml")
        token = Soup.find_all(attrs= {"type": "hidden"})
        form = passForm(token)
        response = s.post(R.url, data= form)

    # On the class page
        sop = BeautifulSoup(response.text, "lxml")
        eralrts = sop.find_all(class_= "alert alert-error")
        if not eralrts:
            token = sop.find_all(attrs= {"type": "hidden"})
            form = reqForm(token)
            response = s.post(response.url, data= form)

        # On confirmation page
            sop = BeautifulSoup(response.text, "lxml")
            sucalrts = sop.find_all(class_= "alert alert-success")
            if sucalrts:
                for sals in sucalrts:
                    print(sals.text)
                return True
            else:
                print("Confirmation page different than expected")
                alrts = sop.find_all(class_= "alert alert-error")
                if alrts:
                    for als in alrts:
                        print(als.text)
                return False

        else:
            print("Signup page different than expected")
            for als in eralrts:
                print(als.text)
            return False