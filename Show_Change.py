import pandas as pd
from os import listdir, remove

from conf import LOC
from MainMethods import showDays

files = [f for f in listdir(LOC)]
DFs = [pd.read_csv(fr"{LOC}\{f}") for f in files]
days = [f.split(".")[0] for f in files]

DFs = {day: DFs[i] for i, day in enumerate(days)}

showDays(DFs, MAIN= False)

to_remove= []
conf= "n"
while conf.lower() !="y":
    to_remove= []
    print("Please type in the CODE for the day(s) that you would like to remove")
    inp = input("remove:")
    try:
        inp = list(map(int, inp.split(",")))

        if max(inp)<= len(DFs)-1:
            print("You chose to remove these days:\n")
            for i, d in enumerate(days):
                if i in inp:
                    print(d)
                    to_remove.append(i)

            conf= input("confirm? (y/n):")
        else:
            print(f"You may have forgotten a comma or got the wrong number,\n"
                  f"please try again")
    except:
        print(f"There seems to be a mistake in your input,\n"
              f"please don't type any unnecessary commas, spaces or words.")

for i, f in enumerate(files):
    if i in to_remove:
        remove(fr"{LOC}\{f}")

print("Done.")