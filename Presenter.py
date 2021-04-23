from Getter import Getter
from pandas import DataFrame as DF, concat

class Presenter(Getter):
    """This is where all the storing and converting to
     presentable data is done"""

    def __init__(self, set_info= True):
        Getter.__init__(self)
        self.Info = DF(columns= self.FULLINFO)
        self.Info.set_index("ID", inplace= True)
        if set_info: self.update_basic_info()

    def update_basic_info(self):
        info = DF(self.set_basic_info().values())
        info.set_index("ID", inplace= True)

        # remove the ones that are already in the Info DF,
        # and have full info and the same link.
        notfullfromdf = self.Info["SignTime"].isna()
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
        return self.Info

    def update_full_info(self, ids):
        full_info = self.set_full_info(ids)
        full_info = DF(full_info.values())
        full_info.set_index("ID", inplace=True)
        self.Info.loc[full_info.index] = full_info








if __name__ == '__main__':
    p = Presenter()
    p.reset_info()
    print()

