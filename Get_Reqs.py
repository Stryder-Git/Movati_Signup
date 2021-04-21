import requests
from bs4 import BeautifulSoup
import pandas as pd
from os import listdir, remove
import datetime as dt
from time import sleep

from MainMethods import getInfo, showDays
from conf import INT, INF, URL, LOC, NINF, LOC2,\
    chosenF, errorsF, doneF

"""
The information for saved days is checked 
and old files deleted.
"""
oldflags = [f for f in listdir(LOC2) if f[0]== "F"]
if oldflags:
    for f in oldflags:
        remove(f"{LOC2}\{f}")

saved= listdir(LOC)
if saved:
    saved = [f.split(".csv")[0] for f in saved]
    ints = [int(f.split("y")[-1]) for f in saved]
    to_remove =[]
    for i, f in enumerate(saved):
        date = dt.datetime.today().day
        if date < 7:
            if ints[i] > date+7 or ints[i] < date:
                remove(f"{LOC}\{f}.csv")
                to_remove.append(f)

        elif date > 23:
            diff = 7- (31 - date)
            if diff < ints[i] < date:
                remove(f"{LOC}\{f}.csv")
                to_remove.append(f)

        elif ints[i] < date:
            remove(f"{LOC}\{f}.csv")
            to_remove.append(f)
    for f in to_remove:
        saved.remove(f)


def flagIt():
    now = dt.datetime.timestamp(dt.datetime.now())
    name = fr"{LOC2}\F{str(int(now))}.txt"
    with open(name, "w") as F:
        pass
    sleep(2)
    return name

def unflagIt(name):
    remove(name)

def checkWait():
    flag = [f for f in listdir(LOC2) if f[0] == "T"]
    if flag:
        while flag[0] in listdir(LOC2):
            print("Wait, Sign Up in process....")
            sleep(5)

checkWait()

flag = flagIt()
Chosen = pd.read_csv(chosenF)
Done = pd.read_csv(doneF)[NINF[-2]].to_list()
if Done:
    print(f"These SignUps are done and should be confirmed by email:\n"
          f"{Chosen[Chosen[NINF[-2]].isin(Done)][[NINF[0], NINF[1], NINF[2]]].to_string(index=False)}\n\n"
          f"-------------------------------------------")
    Chosen.drop(Chosen[Chosen[NINF[-2]].isin(Done)].index, inplace=True)
    pd.DataFrame(columns= NINF).to_csv(doneF, index= False)


Errors = pd.read_csv(errorsF)
errrs = Errors[NINF[-2]].to_list()
if errrs:
    print(f"The sign up for these classes failed:\n"
          f"{Errors.iloc[:,:3]}\n"
          f"Please check manually if you are still interested and "
          f"allow them to be deleted from the program.")
    conf = "n"
    while conf.lower() != "y":
        conf = input("Allow? (y/n):")
        if conf.lower() == "y":
            Errors = pd.DataFrame(columns= NINF)
            Errors.to_csv(errorsF, index = False)
            Chosen.drop(Chosen[Chosen[NINF[-2]].isin(errrs)].index, inplace=True)
        else:
            conf = input("There is no benefit in keeping them !\n"
                         "Are you sure "
                         "you don't want to let them go?\n"
                         "(y/n):")

Chosen.to_csv(chosenF, index= False)

""" 
This uses requests and beautiful soup to setup
the iterators.
"""
r = requests.get(URL)
soup = BeautifulSoup(r.text, "lxml")
classes = soup.find(id= "classes")
days = classes.find_all(class_= "scheduleDay")[:8]

""" 
The following loop gets the basic info from the websites
and keeps it in the dictionary DFs as DataFrames
"""
DFs = {}
for day in days:
    date= day["id"]
    if date in saved:
        continue
    DFs[date] = pd.DataFrame(columns= INF)

    # iterate over each class in the day
    dayclss = day.find_all("div")
    for clss in dayclss:
        #then within each class I select the link in "schedSignup"
        if any(x in clss["class"] for x in INT):
            link = clss.find(class_= "schedSignup").a["href"]
            inf = getInfo(link)
            DFs[date] = DFs[date].append(pd.Series(inf, index= INF), ignore_index=True)

"""
This condition runs the showDays loop to check
each new day's classes for availability and presents the options
"""
num = 0
NewDF = pd.DataFrame(columns= NINF)
if DFs:
    result = showDays(DFs, num, NewDF)
    NewDF, num  = result[0], result[1]

#############

"""
Here, the requests waiting in the 'chosen' csv file
are presented and offered for cancellation
"""

# this just sets up the sig and UId variables for
sigs= [f for f in listdir(LOC2) if f[:3]== "Sig"]
if sigs:
    with open(f"{LOC2}\{sigs[0]}", "r") as s:
        UId = int(s.read())


                        ##### Cancel
if Chosen.shape[0]:
    print(f"\n============== OPTIONS TO CANCEL ======================\n"
          f"These are signups that are waiting to be executed:\n\n"
          f"{Chosen.iloc[:,:3]}\n\n"
          f"Type in the row number on the left if you want to cancel it, seperate with commas\n"
          f"Otherwise, just hit enter and confirm\n")

    confirm = "n"
    while confirm.lower() != "y":
        inp = input("CANCEL:")
        if inp:
            try:
                inp = list(map(int, inp.split(",")))
                print(f"cancel these:\n"
                      f"{Chosen.loc[inp, [NINF[0], NINF[1], NINF[2]]]}")
                confirm = input("Confirm (y/n):")
                if confirm.lower() == "y":
                    Chosen.drop(inp, inplace=True)
            except:
                print(f"There seems to be a mistake in your input,\n"
                      f"please don't type any unnecessary commas, spaces or words.")
        else:
            confirm = input("Keep all (y/n):")

"""
If there are newly available classes:
the following while loop will get requests and 
add the newly chosen ones to the 'chosen' csv file

It will also give Unique IDs to each class based on 
the UId variable retrieved from the Signal File (SigA or SigB)  
"""

                        ##### Choose
if num:
    print(f"=====================================\n"
          f"The column on the RIGHT of each list contains the code to choose the class\n"
          f"please type in your choice(s)"
          f"(seperate codes with commas if you want multiple, hit enter if you want none.)\n")
    confirm = "n"
    while confirm.lower() != "y":
        choice = input("Choice:")
        if choice:
            try:
                choice = list(map(int,choice.split(",")))
                chosen = NewDF[NewDF[NINF[-1]].isin(choice)].copy()
                if max(choice) <= NewDF[NINF[-1]].max():
                    print(f"These are your new choices:\n"
                          f"{chosen.iloc[:,:3].to_string(index= False)}\n")

                    if Chosen.shape[0]:
                        print(f"These are still waiting to be executed:\n"
                              f"{Chosen.iloc[:, :3].to_string(index=False)}\n")
                    else:
                        print(f"There are no signups waiting.")
                    confirm = input("Confirm (y/n):")

                else:
                    print(f"You may have forgotten a comma or got the wrong number,\n"
                          f"please try again")

            except:
                print(f"There seems to be a mistake in your input,\n"
                      f"please don't type any unnecessary commas, spaces or words.")

        else:
            print(f"You chose none.")
            chosen = pd.DataFrame()
            if Chosen.shape[0]:
                print(f"These are still waiting to be executed:\n"
                      f"{Chosen.iloc[:, :3].to_string(index= False)}\n")
            else:
                print(f"There are no signups waiting.")
            confirm = input("Confirm (y/n):")


    if chosen.shape[0]:
        chosen[NINF[-2]] = [UId +i for i in range(1, chosen.shape[0]+1)]
        UId = chosen[NINF[-2]].max()
        Chosen = Chosen.append(chosen, ignore_index=True)

# The days and requestes are saved
Chosen.to_csv(chosenF, index= False)
unflagIt(flag)

for d in DFs:
    DFs[d].to_csv(fr"{LOC}\{d}.csv", index = False)

# The SigFile is updated
if sigs:
    nxtSig = int(sigs[0].split(".")[0][3:])+1
    remove(fr"{LOC2}\{sigs[0]}")

    with open(fr"{LOC2}\Sig{nxtSig}.txt", "w") as s:
        s.write(str(UId))






