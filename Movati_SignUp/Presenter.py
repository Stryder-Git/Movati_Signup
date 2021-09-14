from .Getter import Getter
from pandas import DataFrame as DF, concat, Series, to_timedelta, to_datetime
import datetime as dt
from pprint import pprint

class Presenter(Getter):
    """This is where all the storing and converting to
     presentable data is done"""

    _RESCOLS = ["uDay", "uTime", "uName", "uTeacher"]
    RESCOLS = ["Day", "Time", "Name", "Teacher"]
    _RESCOLSA = ["uDay", "uTime", "uName", "uTeacher", "Auto"]
    RESCOLSA = ["Day", "Time", "Name", "Teacher", "Auto"]
    EMPTY = "empty_dataframe"

    def __init__(self, set_info= True):
        Getter.__init__(self)
        if set_info: self.update_basic_info()
        self.lastfilter = Series()
        self._times = self.create_time_list()


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
        if info.empty: return self.Info

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
        print(full_info.keys())

        if not full_info:
            full_info = DF(columns= self.FULLINFO)
        else:
            full_info = DF(full_info.values())

        full_info.set_index("ID", inplace=True)
        self.Info.loc[full_info.index] = full_info
        self.update_dt()
        return full_info

    def add_to_autosignup(self, choices):
        # make sure that you have full info
        not_full = self.Info.loc[choices, "Status"].isna()
        if not_full.any():
            self.update_full_info(not_full[not_full].index)

        self.AutoSignUp = concat([self.AutoSignUp, self.Info.loc[choices]], ignore_index= False)
        self.AutoSignUp = self.AutoSignUp.drop_duplicates(subset= self._RESCOLS)

        arefull = self.AutoSignUp.Status.isin([self.FULL])
        are_full = self.AutoSignUp[arefull]
        self.AutoSignUp = self.AutoSignUp[~arefull]

        self.AutoSignUp.loc[self.AutoSignUp.Status.isin([self.WAITLIST, self.AVAILABLE]), "dtSignTime"] = self.today
        self.AutoSignUp = self.AutoSignUp.sort_values("dtStart")

        return are_full

    def remove_from_autosignup(self, choices):
        self.AutoSignUp = self.AutoSignUp[~self.AutoSignUp.index.isin(choices)]

    def prepare_data(self, df, auto_col= True):

        if df.empty:
            df = df.append(Series({col: " "*15 for col in df.columns}, name= self.EMPTY))
            df.iloc[:, 0] = "Nothing here..."
        else: df = df.sort_values("dtStart")

        if auto_col:
            cols = self._RESCOLSA
            df[cols[-1]] = " "
            df.loc[df.index.isin(self.AutoSignUp.index), cols[-1]] = "x"
        else:
            cols = self._RESCOLS

        values = df[cols].values.tolist()
        return values, df

    def get_class_names(self): return self.Info['uName'].unique().tolist()

    def get_days(self):
        days = []
        for wkday, date in self.days:
            wkday = wkday[:wkday.index("y")+1]
            days.append(f"{wkday} {date}")
        return days

    def create_time_list(self):
        times = [f"{'0' if i < 10 else ''}{i}:00" for i in range(1, 13)]
        return times


    def _amtotd(self, t, am):
        add = to_timedelta(0) if am or t.startswith("12:") else to_timedelta(12, unit= "H")
        return to_timedelta(int(t.split(":")[0]), unit= "H") + add


    def create_filter(self, days= None, favs= None, start= None, start_am= None, end= None, end_am= None):
        """parses the requested filter options.
        If any options werent selected a mask with only true values is generated"""
        # remove All, if that makes the list empty, there is no restriction placed
        # on names or days anyway, and other selection takes precedence
        try: days.remove("All")
        except (AttributeError, ValueError): pass

        # if days are empty, select all, else make condition
        if days:
            days = [f"{d.split()[0]}{d.split()[-1]}" for d in days]
            days = self.Info["uDay"].isin(days)
        else: days = self._alltrue()

        # the between time filter
        start = to_timedelta(0) if start is None else self._amtotd(start, start_am)
        end = to_timedelta(24, unit= "H") if end is None else self._amtotd(end, end_am)
        timed = self.Info.dtStart - self.Info.dtStart.dt.normalize()
        when = timed.ge(start) & timed.lt(end)

        # use lists, or autosignup to filter the index if they were selected
        bl = ~self.Info["uName"].isin(self.Lists["Blacklist"])
        if favs: favs = self.Info["uName"].isin(self.Lists["Favourites"])
        else: favs = self._alltrue()

        return days & when & bl & favs

    def apply_filter(self, filter):
        if filter.empty: filter = self._alltrue()

        self.lastfilter = filter
        return self.Info[filter]





if __name__ == '__main__':
    pass
    # p = Presenter()
    # p.reset_info()
    # print()

