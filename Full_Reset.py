from os import listdir, remove
from conf import NINF, chosenF, errorsF, doneF, LOC
import pandas as pd

conf = "n"
while conf.lower() !="y":
    conf= input("Are you sure you want to go over the whole week again?\n"
                "(y/n):")

if conf.lower() == "y":
    days = listdir(LOC)
    for f in days:
        remove(rf"{LOC}\{f}")

    csvF = [chosenF, errorsF, doneF]
    for f in csvF:
        pd.DataFrame(columns= NINF).to_csv(f, index= False)

print("Done")