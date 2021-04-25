from Presenter import Presenter
import PySimpleGUI as sg
import webbrowser as web

def GUI(p):
#### MAIN WINDOW
    # Filter Column
    customfilters = [
        [sg.T("Name: "), sg.T(" "*18), sg.T("Day:  ")],
        [sg.LB(["All"]+p.get_class_names(), k= "NAME", s= (16, 10), select_mode= "extended"),
                        sg.LB(["All"]+p.get_days(), k= "DAYS", s= (16, 10), select_mode= "extended")],

        [sg.CB("Favourites", k= "FAV")], [sg.CB("Blacklist", k= "BL")], [sg.CB("AutoSignUp", k= "AUTO")],
        [sg.CB("Basic", k= "BASIC"), sg.CB("Full", k= "FULL")],
        [sg.B("Filter")],
        [sg.B("Save Filter as: "), sg.I(s= (20, 1))],
        [sg.T("_"*40)],
        [sg.B("Favourites"), sg.B("AutoSignUp")],
        [sg.T("Saved Filters: ", k= "SAVE")],
        [sg.Combo(p.Filters, k= "FILTERS", enable_events= True)]
    ]
    # Data Column
    data = [
        [sg.LB(p.results_txt, s=(120, 25), k="OPTIONS", select_mode="extended")],
        [sg.B("Open"), sg.B("Get Status")]
    ]

#### STATUS WINDOW
    def create_status_window(lst):
        return [[sg.LB(lst, s= (60, 10), k= "STATUS", select_mode= "extended")],
                [sg.B("Open"), sg.B("Add to AutoSignUp"), sg.T(" "*20), sg.B("Close Popup")]]


    sg.theme("DarkBlue17")
    FullW = [[sg.Column(customfilters),sg.VerticalSeparator(), sg.Column(data)]]
    window = sg.Window("Movati", FullW)

    while True:
        e, v = window.read()
        if e in (sg.WIN_CLOSED, "Quit"): break
        print(e, v)

        if e == "Filter":
            names = v["NAME"]; days = v["DAYS"]
            favs = v["FAV"]; bl = v["BL"]; auto = v["AUTO"]
            basic = v["BASIC"]; full = v["FULL"]

            results = p.apply_filter(names, days, favs, bl, auto, basic, full)
            results = p.set_results(results)
            window["OPTIONS"].update(results)

        elif e == "Get Status":
            full_info = p.update_full_info(p.hash_choices(v["OPTIONS"]))

            updated_options = p.apply_filter(p.lastfilter)
            updated_options = p.set_results(updated_options)
            window["OPTIONS"].update(updated_options)

            resp = p.make_status_response(full_info)
            status_window = sg.Window("Status Request", create_status_window(resp))
            while True:
                se, sv = status_window.read()
                print(se, sv)
                if se in (sg.WIN_CLOSED, "Close Popup"): status_window.close();break
                elif se == "Open":
                    for link in p.Info.loc[p.hash_choices(sv["STATUS"]), "Link"]:
                        web.open(link)

        elif e == "Open":
            for link in p.Info.loc[p.hash_choices(v["OPTIONS"]), "Link"]:
                web.open(link)



        # if e == "Open":
        #     for l in


    window.close()



if __name__ == '__main__':
    GUI(Presenter())
    """Layout:
    FULL Window:
    Filter
    -> type of class/day/onautosignup/favourites
    -> only basic/also full
    -> saved filters
    Full info
    -> Select classes to put on AutoSignUp
    
    
    Basic Info
    -> Select classes to get FullInfo from
    
    WAITING Window:
    Filter 
    -> type of class/day
    Classes on AutoSignUp
    -> Select to cancel/update status
    
    
    
    Settings Window:
    change start up filter
    
    
    
    
    
    
    
    
    """