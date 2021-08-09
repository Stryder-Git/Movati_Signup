from .Getter import Getter
from pandas import DataFrame as DF, concat, Series, to_timedelta, to_datetime

class Presenter(Getter):
    """This is where all the storing and converting to
     presentable data is done"""
    # RESCOLS = ["uDay", "uTime", "dtStart", "dtEnd", "uName", "SignTime", "Status"]
    # RESCOLS = Getter.FULLINFO[1:-1]
    RESCOLS = ["uDay", "uTime", "uName"]
    STATUSCOLS = ["uDay", "uTime", "uName", "Status", "SignTime"]


    def __init__(self, set_info= True, set_current_options= True):
        Getter.__init__(self)
        if set_info: self.update_basic_info()
        self.results_df = DF(columns= self.FULLINFO)
        self.results_txt = ""
        if set_current_options: self.set_results()
        self.lastfilter = Series()

    def hash_choices(self, lst): return [self.hash(*choice.split(maxsplit= 3)[:3]) for choice in lst]

    def add_to_autosignup(self, choices):
        choices = self.hash_choices(choices)
        print(choices)
        # make sure that you have full info
        not_full = self.Info.loc[choices, "Status"].isna()
        if not_full.any():
            self.update_full_info(not_full[not_full].index)

        self.AutoSignUp = concat([self.AutoSignUp, self.Info.loc[choices]], ignore_index= False)
        self.AutoSignUp = self.AutoSignUp.drop_duplicates()
        self.AutoSignUp = self.AutoSignUp[~self.AutoSignUp.Status.isin([self.FULL])]
        self.AutoSignUp.loc[self.AutoSignUp.Status.isin([self.WAITLIST, self.AVAILABLE]), "dtSignTime"] = self.today

    def remove_from_autosignup(self, choices):
        choices = self.hash_choices(choices)
        self.AutoSignUp = self.AutoSignUp[~self.AutoSignUp.index.isin(choices)]

    def _make_timedelta_col(self, startend):
        """ convert am/pm column to timedelta columns (timedelta since midnight)"""
        startend = startend.str.split("-", expand= True)
        to_return = []
        for c in startend.columns:
            # gets the ones after 1pm, which need to be adjusted
            pm = startend[c].str.contains("pm", regex= False) & ~startend[c].str.contains("12:", regex= False)
            pm = pm.map({True: 12, False: 0}).astype("int32") # change True to 12 to add it later
            # extract hours and minutes and remove am/pm
            times = startend[c].str.split(":", expand= True)
            times[1] = times[1].str.replace("am", "", regex= False).str.replace("pm", "", regex= False)
            # convert to int
            times = times.astype("int32")
            # calculate the amount of minutes since midnight
            td = (times[0] + pm) * 60 + times[1]
            to_return.append(to_timedelta(td, unit= "m"))
        return to_return


    def update_dt(self):
        """make dtStart and dtEnd columns for the classes"""
        start, end = self._make_timedelta_col(self.Info["uTime"])
        date = self.Info["uDay"].map(self.dates.a) # convert days to dates
        self.Info["dtStart"] = date + start # add the timedeltas
        self.Info["dtEnd"] = date + end
        self.Info["dtSignTime"] = to_datetime(self.Info["SignTime"], infer_datetime_format= True)

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
        self.update_dt()
        return full_info

    def update_completed_signup(self, completed):
        self.AutoSignUp = self.AutoSignUp[~self.AutoSignUp.index.isin(completed)]

    def _make_results(self, df):
        txt = df.to_string(index= False).split("\n")
        txt[0] = txt[0].replace("u", " ", 3)
        return txt

    def set_results(self, df= None):
        if df is None: df = self.Info
        self.results_df = df.reset_index(drop= True).sort_values("dtStart")
        if not self.results_df.empty:
            self.results_txt = self._make_results(self.results_df[self.RESCOLS])
        else: self.results_txt = ["nothing found..."]
        return self.results_txt

    def make_status_text(self, df):
        return self._make_results(df[self.STATUSCOLS])

    def get_class_names(self): return self.Info['uName'].unique().tolist()

    def get_days(self):
        days = []
        for wkday, date in self.days:
            wkday = wkday[:wkday.index("y")+1]
            days.append(f"{wkday} {date}")
        return days

    def create_filter(self, names= None, days= None, favs= None, bl= None, auto= None, basic= None, full= None):
        """parses the requested filter options.
        If any options werent selected a mask with only true values is generated"""
        # remove All, if that makes the list empty, there is no restriction placed
        # on names or days anyway, and other selection takes precedence
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
        else: bl = ~self.Info["uName"].isin(self.Lists["Blacklist"])
        if auto: auto = self.Info.index.isin(self.AutoSignUp.index)
        else: auto = self._alltrue()

        # basic/full refer to the amount of information available (status/SignTime gotten or not)
        basic_cond = self.Info["Status"].isna()
        if basic and not full: which = basic_cond
        elif full and not basic: which = ~basic_cond
        else: which = self._alltrue()

        return names & days & favs & bl & auto & which

    def apply_filter(self, filter):
        if not isinstance(filter, str):
            if filter.empty: filter = self._alltrue()
        else:
            if filter == "Favourites": filter = self.Info["uName"].isin(filter)
            elif filter == "AutoSignUp": filter = self.Info.index.isin(filter)
            else: filter = self.create_filter(self.Filters[filter])

        self.lastfilter = filter
        return self.Info.loc[filter]





if __name__ == '__main__':
    pass
    # p = Presenter()
    # p.reset_info()
    # print()

