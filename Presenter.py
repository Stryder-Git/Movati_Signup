from Getter import Getter
from pandas import DataFrame as DF, concat, read_csv, Series, to_timedelta
from numpy import ones
from json import load, dump

class Presenter(Getter):
    """This is where all the storing and converting to
     presentable data is done"""
    # RESCOLS = ["uDay", "uTime", "dtStart", "dtEnd", "uName", "SignTime", "Status"]
    # RESCOLS = Getter.FULLINFO[1:-1]
    RESCOLS = ["uDay", "uTime", "uName"]
    STATUSCOLS = ["uDay", "uTime", "uName", "Status", "SignTime"]
    INFOLOC = "Data\\Info.csv"
    AUTOLOC = "Data\\AutoSignUp.json"
    LISTSLOC = "Data\\Lists.json"
    FILTERSLOC = "Data\\Filters.json"

    def __init__(self, set_info= True, set_current_options= True):
        Getter.__init__(self)
        self.Info = DF(columns= self.FULLINFO)
        self.Info.set_index("ID", inplace= True)
        if set_info: self.update_basic_info()

        self.results_df = DF(columns= self.FULLINFO)
        self.results_txt = ""
        if set_current_options: self.set_results()

        self.AutoSignUp = self.getAuto()
        self.Lists = self.getLists()
        self.Filters = self.getFilters()

        self.lastfilter = Series()

    def getInfo(self): return read_csv(self.INFOLOC)
    def saveInfo(self): self.Info.to_csv(self.INFOLOC, index= True)
    def getAuto(self):
        with open(self.AUTOLOC, "r") as auto: return load(auto)
    def saveAuto(self):
        with open(self.AUTOLOC, "w") as auto: dump(self.AutoSignUp, auto)
    def getLists(self):
        with open(self.LISTSLOC, "r") as lists: return load(lists)
    def saveLists(self):
        with open(self.LISTSLOC, "w") as lists: dump(self.Lists, lists)
    def getFilters(self):
        with open(self.FILTERSLOC, "r") as filters: return load(filters)
    def saveFilters(self):
        with open(self.FILTERSLOC, "w") as filters: dump(self.Filters, filters)

    def _make_timedelta_col(self, startend):
        startend = startend.str.split("-", expand= True)
        to_return = []
        for c in startend.columns:
            pm = startend[c].str.contains("pm", regex= False) & ~startend[c].str.contains("12:", regex= False)
            pm = pm.map({True: 12, False: 0}).astype("int32")
            times = startend[c].str.split(":", expand= True)
            times[1] = times[1].str.replace("am", "", regex= False).str.replace("pm", "", regex= False)

            times = times.astype("int32")
            td = (times[0] + pm) * 60 + times[1]
            to_return.append(to_timedelta(td, unit= "m"))
        return to_return

    def hash_choices(self, lst): return [self.hash(*choice.split(maxsplit= 3)[:3]) for choice in lst]

    def update_dt(self):
        start, end = self._make_timedelta_col(self.Info["uTime"])
        date = self.Info["uDay"].map(self.dates.a)
        self.Info["dtStart"] = date + start
        self.Info["dtEnd"] = date + end

    def update_basic_info(self):
        info = DF(self.set_basic_info().values())
        info.set_index("ID", inplace= True)

        # remove the ones that are already in the Info DF,
        # and have full info and the same link.
        notfullfromdf = self.Info["Status"].isna()
        arefullindf = info.index.isin(self.Info[~notfullfromdf].index)
        samelink = info["Link"].eq(self.Info["Link"]).loc[info.index]
        info = info[~(arefullindf & samelink)]

        # replace the ones in the Info DF that are not full yet
        idisininfo = self.Info.index.isin(info.index)
        self.Info.loc[notfullfromdf & idisininfo] = info

        # find the ones that are in both and have full info
        # but also have different links
        fullsameid = ~notfullfromdf & idisininfo
        difflink = ~self.Info["Link"].eq(info["Link"]).loc[self.Info.index]
        fullsameiddifflink = self.Info[fullsameid & difflink].index.to_list()

        # get the full info of the last subset
        if fullsameiddifflink: self.update_full_info(fullsameiddifflink)

        # add all those that are not in the Info df
        self.Info = concat([self.Info, info[~info.index.isin(self.Info.index)]])
        self.update_dt()
        return self.Info

    def update_full_info(self, ids):
        full_info = self.set_full_info(ids)
        full_info = DF(full_info.values())
        full_info.set_index("ID", inplace=True)
        self.Info.loc[full_info.index] = full_info
        return full_info

    def set_results(self, df= None):
        if df is None: df = self.Info
        self.results_df = df.reset_index(drop= True).sort_values("dtStart")
        if not self.results_df.empty:
            self.results_txt = self.results_df[self.RESCOLS].to_string(index= False).split("\n")
            self.results_txt[0] = self.results_txt[0].replace("u", " ")
        else: self.results_txt = ["nothing found..."]
        return self.results_txt

    def get_class_names(self, refs= None):
        if refs is None:
            return self.Info['uName'].unique().tolist()
    def get_days(self):
        days = []
        for wkday, date in self.days:
            wkday = wkday[:wkday.index("y")+1]
            days.append(f"{wkday} {date}")
        return days

    def _alltrue(self): return Series(ones(self.Info.shape[0]), index= self.Info.index, dtype= "bool")
    def apply_filter(self, names= None, days= None, favs= None, bl= None, auto= None, basic= None, full= None):
        """parses the requested filter options.
        If any options werent selected a mask with only true values is generated"""
        # remove All, if that makes the list empty, there is no restriction placed
        # on names or days anyway, and other selection takes precedence
        if names is self.lastfilter:
            if self.lastfilter.empty: return self.Info.loc[self._alltrue()]
            return self.Info.loc[self.lastfilter]

        try: names.remove("All")
        except (AttributeError, ValueError): pass
        try: days.remove("All")
        except (AttributeError, ValueError): pass

        # if names or days are empty, select all, else make condition
        if names: names = self.Info["uName"].isin(names)
        else: names = self._alltrue()
        if days:
            days = [f"{d.split()[0]}{d.split()[-1]}" for d in days]
            days = self.Info["uDay"].isin(days)
        else: days = self._alltrue()

        # use lists, or autosignup to filter the index if they were selected
        if favs: favs = self.Info["uName"].isin(self.Lists["Favourites"])
        else: favs = self._alltrue()
        if bl: bl = self.Info["uName"].isin(self.Lists["Blacklist"])
        else: bl = self._alltrue()
        if auto: auto = self.Info.index.isin(self.AutoSignUp)
        else: auto = self._alltrue()

        basic_cond = self.Info["Status"].isna()
        if basic and not full: which = basic_cond
        elif full and not basic: which = ~basic_cond
        else: which = self._alltrue()

        self.lastfilter = names & days & favs & bl & auto & which
        return self.Info.loc[self.lastfilter]

    def make_status_response(self, df):
        resp = df[self.STATUSCOLS].to_string(index= False).split("\n")
        resp[0] = resp[0].replace("u", " ")
        return resp





if __name__ == '__main__':
    pass
    # p = Presenter()
    # p.reset_info()
    # print()

