import unittest as ut
from unittest.mock import Mock, patch
from Presenter import Presenter
from pandas import read_csv, DataFrame as DF, Series
from pprint import pprint

class Presenter_Tests(ut.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """this prepares the testdata to be return in p.set_basic_info,
        returns the df and the dct version of it"""
        newdf = read_csv("TestData\\new.csv")
        newdct = [row.to_dict() for _, row in newdf.iterrows()]
        newdct = {d["ID"]: d for d in newdct}
        # here the types tend to be converted to float but in the presenter
        # they are converted to object, which will not be considered equal
        newdf = DF(newdct.values()).astype("object")
        newdf.set_index("ID", inplace= True)
        cls.newdf = newdf; cls.newdct = newdct


    def setUp(self) -> None:
        # initiate the presenter with set_info= False (should automatically be an empty self.Info)
        self.p = Presenter(set_info= False)
        # mock self.set_basic_info method to return new.csv as a dct of dcts
        # mock self.set_full_info method
        self.p.set_basic_info = Mock(return_value= self.newdct)
        self.p.set_full_info = Mock()

    def test_reset_empty_Info(self):
        """checks that it is correctly handled when the self.Info is empty, which means that
         all the basic_info should be added, no changes made and no full info was requested"""
        self.p.reset_info() # call to test
        print(self.newdf)
        print(self.p.Info)

        # check that the full new.csv has been added, without any changes
        self.assertTrue(self.newdf.equals(self.p.Info), "testdata not fully added to the empty Info df")
        # check that self.set_full_info has not been called
        self.p.set_full_info.assert_not_called()


    def test_reset_not_empty_Info(self):
        """check that the updating of self.Info has been handled correctly (when its not empty)
        """
        # replace with testdata
        self.p.Info = read_csv("TestData\\old.csv").set_index("ID")
        self.p.set_full_info.return_value = \
            {"idd-new":
                 {"ID": "idd-new", "uDay": "Sat", "uTime":"11:00", "uName": "aa", "Day": None,
                  "Time": None, "Name": None, "Status": None, "SignTime": 1, "Link": "www.diff"},
             "idc-new":
                 {"ID": "idc-new", "uDay": "Sat", "uTime": "11:00", "uName": "aa", "Day": None,
                  "Time": None, "Name": None, "Status": None, "SignTime": 3, "Link": "www.diff"}
             }
        self.p.reset_info()  # call to test
        print(self.newdf); print(self.p.Info)

        ### checks for ids that are not in both
        # check that the new rows are added to p.Info
        self.assertTrue(Series(["id7-new", "id8-new"]).isin(self.p.Info.index).all())
        # check that the old rows in p.Info are not removed
        self.assertTrue(Series(["id5-new", "id6-new"]).isin(self.p.Info.index).all())

        ### checks for ids that are in both
        # test that not full in Info gets replaced with new row
        link1, link2 = self.p.Info.loc[["id2-new", "ida-new"], "Link"]
        self.assertListEqual([link1, link2], ["www.change"]*2, "rows weren't updated")
        # full in Info but same Link, so don't change anything
        signtime1, signtime2 = self.p.Info.loc[["id3-new", "idb-new"], "SignTime"]
        self.assertListEqual([signtime1, signtime2], [10, 2], "rows weren't left a they are")

        # ids in both, full in Info and have a diff link
        ids = ["idd-new", "idc-new"]
        # check that full_info has been requested
        self.p.set_full_info.assert_called_once_with(ids)
        # check that SignTime has been updated
        signtime1, signtime2 = self.p.Info.loc[ids, "SignTime"]
        self.assertListEqual([signtime1, signtime2], [1,3], "full_info update didn't work")

"""
second case:
    there is data in Info
    in the infoupdate returned there should be:
        rows with new ids
            -> should be added to Info, without changing anything
        
        rows with equal ids in Info which have
                are NOT full in Info
                    -> these should replace the ones in Info
                    
                full in Info and the same link as in Info
                    -> should be ignored/dropped from infoupdate

                full info BUT different link then in Info
                    -> should be requested full info for (using the new link)
                    -> then new full_info should replace the rows in Info
        
        
        
Permutations:
    id      same or diff
    info    full or nfull
    links   equal or changed
    
# diff nfull changed  all diffs will simply be added or left alone
# diff nfull equal
# diff full changed
# diff full equal

# same nfull changed  nfull will simply be replaced
# same nfull equal

# same full equal   left alone  

# same full changed  update the full info
    


"""


if __name__ == '__main__':
    ut.main()
