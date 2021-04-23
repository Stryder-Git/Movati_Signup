import requests as reqs
from bs4 import BeautifulSoup as BS
from itertools import count
class twdct:
    def __init__(self, **kwargs):
        self.a = {}; self.b = {}
        for key, item in kwargs.items(): self[key] = item
    def __setitem__(self, a, b):
        if a in self.a or a in self.b or b in self.a or b in self.b:
            raise ValueError(f"element already exist")
        self.a[a] = b; self.b[b] = a
    def __getitem__(self, item):
        try: return self.a[item]
        except KeyError: return self.b[item]
    def __str__(self):
        res = ""
        for key, item in self.a.items(): res+= f"{key} <> {item}\n"
        return res



class Getter:
    TBO = "TBO"
    FULL = "Full"
    AVAILABLE = "Available"
    WAITLIST = "Waitlist"
    USERN = "tung.angela@hotmail.com"
    PASSW = "BooandBaby"
    FULLINFO = "ID uDay uTime uName Day Time Name Status SignTime Link".split()
    URL = "https://movatiathletic.com/club-schedules/?club=guelph"

    def __init__(self):
        self.days = twdct()
        self.Raw_Info = {}
        self.Site = self.get()
        self.set_days()

    def get(self, url= None): return BS(reqs.get(url or self.URL).text, features= "lxml")

    def set_days(self):
        # class = "slick-list", or how I would normally do it doesn't work for some reason
        # so I am just iterating over all divs and getting the days from the carousel-items
        for div in self.Site.find_all("div"):
            try:
                if "carousel-item" in div["class"]:
                    wkday, month, date = div.text.split()
                    self.days[f"{wkday}{date}"] = f"{month} {date}"

                elif "scheduleDay" in div["class"]: break
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
                    name = clss["class"][2]
                    link = clss.find(class_= "schedSignup")

                    # A unique id is created, if the same class is encountered
                    # (for instances when refreshing, the id will be the same)
                    id_ = self.hash(day, time_, name)
                    # sometimes a class won't have a link to it available
                    if not link.a is None: link = link.a["href"]
                    else: link = None
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

    def login_get(self, url):
        with reqs.Session() as s:
            login_page = s.get(url)

            Soup = BS(login_page.text, "lxml")
            token = Soup.find_all(attrs={"type": "hidden"})
            form = self._passForm(token)

            response = s.post(login_page.url, data=form)
            response = s.get(response.url)
            return BS(response.text, "lxml")

    def set_full_info(self, ids):
        """should get a list of keys (tuples) for the class_links dct"""
        to_return = {}
        for id_ in ids:
            link = self.Raw_Info[id_]["Link"]
            site = self.login_get(link)

            info = self.Raw_Info[id_].update(dict(
                                       Name= " ".join(site.find("h2").text.split()[:-3]),
                                       Day= site.find("h3").text.split()[0],
                                       Time= site.find("h2").small.text))

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





if __name__ == '__main__':
    from pprint import pprint
    g = Getter()
    g.set_days()
    print(g.days)
    g.set_basic_info()
    # pprint(g.basic_info)
    g.basic_info["TBO"] = {"Link": "https://api.groupexpro.com/gxp/reservations/start/index/12142353/04/27/2021"}
    g.basic_info["Full"] = {"Link": "https://api.groupexpro.com/gxp/reservations/start/index/12142637/04/21/2021"}
    g.basic_info["Available"] = {"Link": "https://api.groupexpro.com/gxp/reservations/start/index/11932830/04/22/2021"}

    pprint(g.set_full_info("TBO Full Available".split()))



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

