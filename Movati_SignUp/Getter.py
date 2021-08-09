import requests as reqs
from bs4 import BeautifulSoup as BS
from datetime import datetime as dt, timedelta as td, time as t
from pandas import Series, read_csv
from numpy import ones
from json import load, dump
from logging import getLogger, Formatter, FileHandler, INFO

class twdct:
    def __init__(self, **kwargs):
        self.a = {}; self.b = {}
        for key, item in kwargs.items(): self[key] = item
        self.n = 0
        self.current= -1
        self.to_iter = []
    def __setitem__(self, a, b):
        if a in self.a or a in self.b or b in self.a or b in self.b:
            raise ValueError(f"element already exist")
        self.n+=1
        self.a[a] = b; self.b[b] = a
    def __getitem__(self, item):
        try: return self.a[item]
        except KeyError: return self.b[item]
    def __iter__(self): return iter(self.a.items())
    def __str__(self):
        res = ""
        for key, item in self.a.items(): res+= f"{key} <> {item}\n"
        if not res: res = "<Empty-TwDct>"
        return res


class Getter:
    """
    To set up the data:
        1. Get available days with .set_days()

    """


    TBO = "TBO" # when registration still needs to open
    FULL = "Full" # when its completely full
    AVAILABLE = "Available"  # when you can already sign up
    WAITLIST = "Waitlist"  # when you can wait for a place to open
    USERN = "tung.angela@hotmail.com"
    PASSW = "BooandBaby"
    FULLINFO = "ID uDay uTime uName Day Time Name Status SignTime dtStart dtEnd dtSignTime Link".split()
    URL = "https://movatiathletic.com/club-schedules/?club=guelph"
    INFOLOC = ".\\Data\\Info.csv"
    AUTOLOC = ".\\Data\\AutoSignUp.csv"
    SIGNEDLOC = ".\\Data\\signedup.txt"
    LISTSLOC = ".\\Data\\Lists.json"
    FILTERSLOC = ".\\Data\\Filters.json"
    LOGLOC = ".\\Data\\Logs"

    @classmethod
    def _get_class_name(cls): return cls.__name__

    def __init__(self, get_site= True):
        self.today = dt.combine(dt.now().date(), t(0))
        self.days = twdct()
        self.dates = twdct()
        self.Raw_Info = {}

        if get_site:
            self.Site = self.get()
            self.set_days()
        else: self.Site = None
        self.Info = self.getInfo()
        self.AutoSignUp = self.getAuto()
        self.Lists = self.getLists()
        self.Filters = self.getFilters()

        self.mylogger = self.create_logger(self._get_class_name())

    def create_logger(self, name):
        handler = FileHandler(f"{self.LOGLOC}\\{name}.log")
        handler.setFormatter(Formatter("%(asctime)s\t%(message)s"))
        logger = getLogger(name)
        logger.addHandler(handler)
        logger.setLevel(INFO)
        return logger

    def getInfo(self, index_col= "ID"):
        info = read_csv(self.INFOLOC, index_col= index_col, parse_dates= ["dtStart", "dtEnd", "dtSignTime"])
        return info[info.dtStart>= self.today]


    def saveInfo(self): self.Info.to_csv(self.INFOLOC, index= True)
    def getAuto(self):
        return read_csv(self.AUTOLOC, index_col= "ID", parse_dates= ["dtStart","dtEnd","dtSignTime"])
    def saveAuto(self):
        self.AutoSignUp.to_csv(self.AUTOLOC, index= True)
    def getLists(self):
        with open(self.LISTSLOC, "r") as lists: return load(lists)
    def saveLists(self):
        with open(self.LISTSLOC, "w") as lists: dump(self.Lists, lists)
    def getFilters(self):
        with open(self.FILTERSLOC, "r") as filters: return load(filters)
    def saveFilters(self):
        with open(self.FILTERSLOC, "w") as filters: dump(self.Filters, filters)
    def save_all(self):
        self.saveInfo()
        self.saveAuto()
        self.saveLists()
        self.saveFilters()

    def get(self, url= None): return BS(reqs.get(url or self.URL).text, features= "lxml")

    def _calc_date(self, d):
        month, date = d.split()
        if len(date) == 1: d.replace(date, f"0{date}")
        d = dt.strptime(f"{self.today.year} {month} {date}", "%Y %B %d")
        if d < self.today: d += td(365)
        return d

    def set_days(self):
        # class = "slick-list", or how I would normally do it doesn't work for some reason
        # so I am just iterating over all divs and getting the days from the carousel-items
        day_nav = self.Site.find(class_= "swiper-wrapper")
        for div in day_nav.find_all("div", recursive= False):
            try:
                if "nav" in div["id"]:
                    wkday, month, date = div.text.split()
                    wkdaydate = f"{wkday}{date}"
                    monthdate = f"{month} {date}"
                    self.days[wkdaydate] = monthdate
                    self.dates[wkdaydate] = self._calc_date(monthdate)
            except KeyError: pass

        return self.days

    def hash(self, uDay, uTime, uName):
        day = uDay[:uDay.index("y")+1]
        date = self.days[uDay]
        return (date+day+uTime+uName).replace(" ","").lower()

    def createInfoDict(self, **kwargs):
        if not all([k in self.FULLINFO for k in kwargs.keys()]):
            raise ValueError('kwargs must match the info fields')
        dct = {k: kwargs.get(k) for k in self.FULLINFO}
        return dct


    def set_basic_info(self):
        """going over the schedule of each day and saving the times and links"""
        for schedule in self.Site.find_all(class_= "scheduleDay"):
            day = schedule['id']
            for clss in schedule.find_all("div", recursive= False):
                if "classRow" in clss["class"]:
                    time_ = clss.find(class_= "schedTime").text
                    name = clss["class"][3]
                    link = clss.find(class_= "schedSignup")

                    # A unique id is created, if the same class is encountered,
                    # (for instances when refreshing) the id will be the same
                    id_ = self.hash(day, time_, name)
                    # sometimes a class won't have a link to it available
                    link = None if link.a is None else link.a["href"]
                    # save with classname, day and time as key to the link
                    self.Raw_Info[id_] = self.createInfoDict(
                        ID= id_, uDay= day, uTime= time_.strip(), uName= name, Link= link)
        return self.Raw_Info

    def _passForm(self, token):
        form = {i["name"]: i["value"] for i in token}
        form["login"] = self.USERN
        form["password"] = self.PASSW
        form["submit"] = 'Login'
        return form

    def _convertTime(self, time):
        if "pm" in time:
            mn = time.split("pm")[0].split(":")[1]
            hour = int(time.split(":")[0])
            return f"{hour + 12}:{mn}:00"
        elif "am" in time:
            return time.replace("am", ":00")

    def login_get(self, url, keep= False):
        s = reqs.Session()
        login_page = s.get(url)

        Soup = BS(login_page.text, "lxml")
        token = Soup.find_all(attrs={"type": "hidden"})
        form = self._passForm(token)

        response = s.post(login_page.url, data=form)
        response = s.get(response.url)
        soup = BS(response.text, "lxml")
        if not keep:
            s.close(); return soup
        else:
            return soup, s, response.url

    def set_full_info(self, ids):
        """should get a list of keys (tuples) for the class_links dct"""
        to_return = {}
        for id_ in ids:
            link = self.Raw_Info[id_]["Link"]
            site= self.login_get(link)
            self.Raw_Info[id_].update(dict(
                                   Name= " ".join(site.find("h2").text.split()[:-3]),
                                   Day= site.find("h3").text.split()[0],
                                   Time= site.find("h2").small.text))
            info = self.Raw_Info[id_]

            # alert alert-error should only be found if I cannot sign in
            alert = site.find(class_="alert alert-error")
            spots = int(site.find("h3").small.text.split()[0])
            if alert:
                # if there are spots available and the reservations haven't been closed yet,
                # it must be opened in the future (TBO)
                if spots and "Reservations for this class are now closed." not in alert.text:
                    info["Status"] = self.TBO
                    d, t = alert.text.split("starts on ")[1].split(".")[0].split(" at ") # extract the Sign Up Time
                    info["SignTime"] = f"{d} {self._convertTime(t)}"

                else: # there are no spots available or it has been closed already, it must be full
                    info["Status"] = self.FULL; info["SignTime"] = None

            else: # there is no alert alert-error. if there are spots, it must be availbale, otherwise waitlist
                if spots:
                    info["Status"] = self.AVAILABLE; info["SignTime"] = None
                else:
                    info["Status"] = self.WAITLIST; info["SignTime"] = None

            self.Raw_Info[id_] = info
            to_return[id_] = info
        return to_return

    def _alltrue(self): return Series(ones(self.Info.shape[0]), index= self.Info.index, dtype= "bool")

if __name__ == '__main__':

    g = Getter(get_site= False)
    g.Site = g.get()
    days = g.set_days()
    print(days)

    """
    Start with setting the available dates by parsing
    class="carousel-item slick-slide slick-active" id="navSaturday24"
    this should yield both date and id(Saturday24)


    Then for each day, by searching for the id in <div id="Wednesday21" class="scheduleDay" style="display: none;">
        for each class in that day (by iterating over all 'div's)
            select the name by parsing each["class"]
            select the time by getting the child element with class="schedTime"
            get the sign up link by getting the child element with class="schedSignup"


    Parse each class for the actual sign up info
    ->> check out MainMethods.getInfo


    """

