
USERN = "tung.angela@hotmail.com"
PASSW = "BooandBaby"

URL = "https://movatiathletic.com/club-schedules/?club=guelph"

LOC = "DailyInfo"
LOC2 = "Reqs"

chosenF = fr"{LOC2}\chosen.csv"
errorsF = fr"{LOC2}\Errors.csv"
doneF = fr"{LOC2}\Done.csv"


INT = ["20-20-20-e",
       "body-sculpt-e",
       "movati-barre-physique-e",
       "pilates-e",
       "power-flow-ia",
       "zumbaÂ-e",
       "general-workout"]

# This is only used in the daily lists
INF = ["Name",
       "Time",
       "Open",
       "SignTime",
       "Link"]

CODE = ["TBO",
        "Full",
        "Available",
        "Waitlist"]

# This is used in the Chosen list
NINF = ["Day",
        *INF,
        "UniqueID",
        "CODE"]
