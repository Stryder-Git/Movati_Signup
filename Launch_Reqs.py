import threading as th
import pandas as pd
import datetime as dt
from os import listdir, remove
from time import sleep

from MainMethods import makeReq
from conf import NINF, LOC2, chosenF, errorsF, doneF

oldflags = [f for f in listdir(LOC2) if f[0]== "T"]
if oldflags:
    for f in oldflags:
        remove(f"{LOC2}\{f}")

def flagIt():
    now = dt.datetime.timestamp(dt.datetime.now())
    name = fr"{LOC2}\T{str(int(now))}.txt"
    with open(name, "w") as T:
        pass
    sleep(2)
    return name

def unflagIt(name):
    remove(name)


def checkWait():
    flag = [f for f in listdir(LOC2) if f[0]== "F" or f[0]== "T"]
    print("checking for flags")
    timeout = False
    while flag:
        print(f"encountered {flag[0]}")
        if flag[0][0] == "F":
            while flag[0] in listdir(LOC2):
                sleep(5)
                if dt.datetime.timestamp(dt.datetime.now())- int(flag[0].split(".")[0][1:]) > 10*60:
                    timeout = True
                    break
        elif flag[0][0] == "T":
            while flag[0] in listdir(LOC2):
                sleep(5)
                if dt.datetime.timestamp(dt.datetime.now())- int(flag[0].split(".")[0][1:]) > 5*60:
                    timeout = True
                    break
        if not timeout:
            flag = [f for f in listdir(LOC2) if f[0]== "F" or f[0]== "T"]
        else:
            print("timed out")
            break

    print("path clear")


def autoSign(ID, wait, ex):
    print("thread sleeping")
    sleep(wait+5+ex)
    checkWait()
    flag = flagIt()
    print(f"blocked with {flag}")

    chosen = pd.read_csv(chosenF)
    errors = pd.read_csv(errorsF)
    success = pd.read_csv(doneF)
    print("got the files")
    if chosen[NINF[-2]].isin([ID]).any():
        link = chosen[chosen[NINF[-2]]== ID][NINF[5]].iloc[0]
        print(f"trying {ID}: {link}")
        try:
            signup= makeReq(link)
            if signup:
                Done.append(ID)
                success = success.append(chosen[chosen[NINF[-2]]== ID])
                success.to_csv(doneF, index= False)
                Waiting.remove(ID)
                print("success")
            else:
                Failed.append(ID)
                errors = errors.append(chosen[chosen[NINF[-2]]== ID])
                errors.to_csv(errorsF, index= False)
                Waiting.remove(ID)
                print("error")

        except KeyError:
            print(f"{ID}, {link}")
            raise KeyError
    print(f"unflagging {flag}")
    unflagIt(flag)


def checkRun():
    print("checking")
    for i,d in enumerate(Chosen[NINF[4]]):
        id = Chosen.iloc[i,-2]
        if id in Done or id in Failed:
            continue
        if id in Waiting:
            print(f"This is already waiting:\n"
                  f"{Chosen.iloc[i, :3].to_string(index=False)}")
            continue

        ex= len(Waiting)+1

        if d not in ["0",0]:
            if pd.to_datetime(d.split()[0]) == dt.date.today():
                req = (id, pd.to_datetime(d))

                if dt.datetime.now() < req[1]:
                    wait = (req[1] - dt.datetime.now()).seconds
                else:
                    wait = 0
                th.Thread(target=autoSign, args=(req[0], wait, ex)).start()
                Waiting.append(id)
                print(f"started {id},\n"
                      f"{Chosen.iloc[i,:3].to_string(index= False)}\n"
                      f"will launch at {req[1]}")

        else:
            th.Thread(target= autoSign, args= (id, 0, 0)).start()
            Waiting.append(id)
            print(f"started {id},\n"
                  f"{Chosen.iloc[i, :3].to_string(index=False)}\n")
            sleep(1.5)
    print("done")


sig = [f for f in listdir(LOC2) if f[:3] == "Sig"][0]

checkWait()

Chosen = pd.read_csv(chosenF)
Errors = pd.read_csv(errorsF)
Success = pd.read_csv(doneF)

Failed = Errors[NINF[-2]].to_list()
Done = Success[NINF[-2]].to_list()
Waiting = []

checkRun()

while True:
    if not sig in listdir(LOC2):
        Chosen = pd.read_csv(chosenF)
        Errors = pd.read_csv(errorsF)
        Success = pd.read_csv(doneF)

        Failed = Errors[NINF[-2]].to_list()
        Done = Success[NINF[-2]].to_list()
        checkRun()
        sig = [f for f in listdir(LOC2) if f[:3]== "Sig"][0]

    sleep(300)
