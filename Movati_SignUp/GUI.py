from Presenter import Presenter
import PySimpleGUI as sg
import webbrowser as web
from subprocess import Popen

def GUI(p):
#### MAIN WINDOW
    ### Main Tab
    # Filter Column
    customfilters = [
        [sg.T("Name: "), sg.T(" "*18), sg.T("Day:  ")],
        [sg.LB(["All"]+p.get_class_names(), k= "NAME", s= (16, 10), select_mode= "extended"),
                        sg.LB(["All"]+p.get_days(), k= "DAYS", s= (16, 10), select_mode= "extended")],
        [sg.CB("Favourites", k= "FAV")], [sg.CB("Blacklist", k= "BL")], [sg.CB("AutoSignUp", k= "AUTO")],
        [sg.CB("Basic", k= "BASIC"), sg.CB("Full", k= "FULL")], [sg.B("Filter")],

        [sg.B("Save Filter as: ", k= "SAVE"), sg.I(s= (20, 1), k="SAVEAS")], [sg.T("_"*40)],
        [sg.B("Favourites"), sg.B("AutoSignUp")], [sg.T("Saved Filters: ")],
        [sg.DD(list(p.Filters.keys()), k= "FILTERS", s= (30,1)), sg.B("Filter", k= "SAVEDFILTER")]
    ]
    # Data Column
    data = [
        [sg.LB(p.results_txt, s=(60, 25), k="OPTIONS", select_mode="extended")],
        [sg.B("Open"), sg.B("Get Status"), sg.B("Add to AutoSignUp")]
    ]
    Main_Tab = sg.Tab("Main", [[sg.Column(customfilters),sg.VerticalSeparator(), sg.Column(data)]])

    ### Personalize Tab
    col_height = 8
    Personalize_Tab = sg.Tab("Personalize", [[
        sg.Column([[sg.T("Available Classes:")],
            [sg.LB(p.get_class_names(), s= (30, col_height), k= "pNAME", select_mode= "extended")],
            [sg.T("Add to: "), sg.B("Favourites", k= "addFAV"), sg.B("Blacklist", k= "addBL")]]),
        sg.Column([[sg.T("Favourites:")],
            [sg.LB(p.Lists["Favourites"], s= (20, col_height), k= "pFAV", select_mode= "extended")],
            [sg.B("Remove", k= "removeFAV")]]),
        sg.Column([[sg.T("Blacklist:")],
            [sg.LB(p.Lists["Blacklist"], s= (20, col_height), k= "pBL", select_mode= "extended")],
            [sg.B("Remove", k= "removeBL")]])
    ],
        [sg.Column([[sg.T("Saved Filters:")], [sg.LB(list(p.Filters.keys()), s= (30, col_height), k= "pFILTERS")],
                  [sg.B("Remove", k= "removeFILTER")]])
    ],
        [sg.B()]

    ])

#### STATUS WINDOW
    def create_status_window(lst):
        return [[sg.LB(lst, s= (60, 10), k= "STATUS", select_mode= "extended")],
                [sg.B("Open"), sg.B("Add to AutoSignUp"), sg.T(" "*20), sg.B("Close Popup")]]
#### STARTUP WINDOW
    def create_startup_window(): pass

    sg.theme("DarkBlue17")
    FullW = [[sg.TabGroup([[Main_Tab, Personalize_Tab]])]]
    window = sg.Window("Movati", FullW)

    def update_personalize_list():
        window["pBL"].update(p.Lists["Blacklist"])
        window["pFAV"].update(p.Lists["Favourites"])
    def update_main_options(filter_result):
        filter_result = p.set_results(filter_result)
        window["OPTIONS"].update(filter_result)
    def filters_todct(v):
        return dict(names=v["NAME"], days=v["DAYS"], favs=v["FAV"], bl=v["BL"],
                    auto=v["AUTO"], basic=v["BASIC"], full= v["FULL"])
    def update_filters():
        filters = list(p.Filters.keys())
        window["FILTERS"].update(values= filters)
        window["pFILTERS"].update(filters)


    while True:
        e, v = window.read()
        print(e, v)
        if e in (sg.WIN_CLOSED, "Quit"): p.save_all(); break

        elif e in ("Favourites", "AutoSignUp"):
            results = p.apply_filter(e)
            update_main_options(results)

        elif e == "Filter":
            filter = p.create_filter(**filters_todct(v))
            results = p.apply_filter(filter)
            update_main_options(results)

        elif e == "Get Status":
            full_info = p.update_full_info(p.hash_choices(v["OPTIONS"]))
            updated_options = p.apply_filter(p.lastfilter)
            update_main_options(updated_options)

            # create and run the pop up showing the requested status
            resp = p.make_status_response(full_info)
            status_window = sg.Window("Status Request", create_status_window(resp))
            while True:
                se, sv = status_window.read()
                print(se, sv)
                if se in (sg.WIN_CLOSED, "Close Popup"): status_window.close();break
                elif se == "Open":
                    for link in p.Info.loc[p.hash_choices(sv["STATUS"]), "Link"]:
                        web.open(link)
                elif se == "Add to AutoSignUp":
                    p.AutoSignUp.extend(p.hash_choices(sv["STATUS"]))
                    p.AutoSignUp = list(set(p.AutoSignUp))


        elif e == "Open":
            for link in p.Info.loc[p.hash_choices(v["OPTIONS"]), "Link"]: web.open(link)
        elif e == "Add to AutoSignUp":
            p.AutoSignUp.extend(p.hash_choices(sv["STATUS"]))
            p.AutoSignUp = list(set(p.AutoSignUp))

        elif e == "SAVE":
            n = v["SAVEAS"]
            if n in list(p.Filters.keys())+ ["Favourites", "Blacklist", "AutoSignUp"]:
                sg.popup_ok("Please choose a different name.\n "
                            "The chosen one is either taken or part of one of "
                            "'Favourites, 'Blacklist', and 'AutoSignUp', which are reserved.")
                continue
            p.Filters[n] = filters_todct(v)
            update_filters()

        elif e == "SAVEDFILTER":
            results = p.apply_filter(v["FILTERS"])
            update_main_options(results)


        elif e in ("addFAV", "addBL"):
            lst = "Favourites" if e == "addFAV" else "Blacklist"
            for choice in v["pNAME"]: p.Lists[lst].append(choice)
            update_personalize_list()

        elif e in ("removeFAV", "removeBL"):
            lst, choices = ("Favourites", v["pFAV"]) if e == "removeFAV" else ("Blacklist", v["pBL"])
            for choice in choices: p.Lists[lst].remove(choice)
            update_personalize_list()

        elif e == "removeFILTER":
            for f in v["pFILTERS"]: del p.Filters[f]
            update_filters()


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