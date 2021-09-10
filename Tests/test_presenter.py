import pandas as pd

from Movati_SignUp import Presenter


def test_make_timedelta_col():
    p = Presenter()

    testcol = pd.Series(["6:15am-7:15am", "9:00am-10:00am", "10:45am-01:15pm", "5:30pm-6:30pm"])

    start_goal = pd.Series([pd.Timedelta(hours= 6, minutes= 15),
                            pd.Timedelta(hours= 9),
                            pd.Timedelta(hours= 10, minutes= 45),
                            pd.Timedelta(hours= 17, minutes= 30)])

    end_goal = pd.Series([pd.Timedelta(hours= 7, minutes= 15),
                            pd.Timedelta(hours= 10),
                            pd.Timedelta(hours= 13, minutes= 15),
                            pd.Timedelta(hours= 18, minutes= 30)])

    start, end = p._make_timedelta_col(testcol)

    assert start.eq(start_goal).all(), f"\n{pd.concat([start, start_goal], axis= 1)}"
    assert end.eq(end_goal).all()



if __name__ == '__main__':
    pass
    # for ref, obj in locals().copy().items():
    #     if ref.startswith("test_"):
    #         print("running: ", ref)
    #         obj()

