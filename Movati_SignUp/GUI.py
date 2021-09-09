import PySimpleGUI as sg
import webbrowser as web
from json import load, dump


class GUI:
    _gui_settings_loc = ".\\Data\\gui_settings.json"


    def __init__(self, p, s):
        self.p = p
        self.s = s

        self.settings = self.get_settings()
        self.THEME = self.settings["default_theme"]
        self.DEF_START= self.settings["default_start"]
        self.DEF_END = self.settings["default_end"]
        self.DEF_FAV = bool(self.settings["default_favourites"])

        sg.theme(self.THEME)

        self.create_main_window()
        # self.s.connect()   ####
        # self.update_completed_failed_autosignups() ######

    def get_settings(self):
        with open(self._gui_settings_loc, "r") as settings:
            return load(settings)
    def save_settings(self):
        with open(self._gui_settings_loc, "w") as settings:
            dump(self.settings, settings)

    def update_completed_failed_autosignups(self):
        completed, failed = self.s.get_completed_failed()
        if failed:
            have_failed = self.p.AutoSignUp.index.isin(failed)
            failed_text = self.p.make_results_text(self.p.AutoSignUp[have_failed])
            self.show_failed_window(failed_text)

        if completed:
            self.p.add_to_registered(completed)
            self.update_registered_tab()


        self.p.remove_from_autosignup(completed + failed)
        self.update_auto_tab()

    def create_main_window(self):
        #### MAIN WINDOW
            ### Main Tab
            # Filter Row
            self.customfilters = [sg.Column(
                [[sg.T("Time between: ")],
                [sg.DD(self.p._times, k= "START", default_value= self.DEF_START), sg.T("and"),
                 sg.DD(self.p._times, k= "END", default_value= self.DEF_END)]
                ]),
                sg.Column([
                [sg.T("Day:  ")],
                [sg.LB(["All"]+self.p.get_days(), k= "DAYS", s= (25, 7), select_mode= "extended")],
                ]),
                sg.Column([
                [sg.CB("Only Favourites", k= "FAV", default= self.DEF_FAV)], [sg.B("Filter")]
                ])
            ]

            df = self.p.apply_filter(self.p.create_filter(
                favs=self.DEF_FAV, start=self.DEF_START, end=self.DEF_END))
            # Data Row
            self.data = [
                [sg.LB(self.p.make_results_text(df), s=(80, 15), k="OPTIONS", select_mode="extended")],
                [sg.B("Open"), sg.B("Add to AutoSignUp")]]

            self.Main_Tab = sg.Tab("Main", [self.customfilters, *self.data])

            ### AutoSignup Tab
            self.Auto_Tab = sg.Tab("AutoSignUp", [
                [sg.LB(self.p.make_results_text(self.p.AutoSignUp), s= (80, 15), k= "AUTO", select_mode= "extended")],
                [sg.B("Remove from AutoSignUp")]])

            # ### Registered Tab
            # self.Registered_Tab = sg.Tab("Registered", [
            #     [sg.LB(self.p.make_results_text(self.p.Registered), s= (80, 15), k= "REGIST", select_mode= "extended")],
            #     [sg.B("Cancel Reservation")]])

            ### Personalize Tab
            col_height = 8
            self.Personalize_Tab = sg.Tab("Personalize", [[
                sg.Column([[sg.T("Available Classes:")],
                    [sg.LB(self.p.get_class_names(), s= (30, col_height), k= "pNAME", select_mode= "extended")],
                    [sg.T("Add to: "), sg.B("Favourites", k= "addFAV"), sg.B("Blacklist", k= "addBL")]]),
                sg.Column([[sg.T("Favourites:")],
                    [sg.LB(self.p.Lists["Favourites"], s= (20, col_height), k= "pFAV", select_mode= "extended")],
                    [sg.B("Remove", k= "removeFAV")]]),
                sg.Column([[sg.T("Blacklist:")],
                    [sg.LB(self.p.Lists["Blacklist"], s= (20, col_height), k= "pBL", select_mode= "extended")],
                    [sg.B("Remove", k= "removeBL")]])
                ],
                [sg.Column([[sg.T("Default time between:")],
                             [sg.DD(self.p._times, k="pSTART", default_value= self.DEF_START), sg.T("and"),
                              sg.DD(self.p._times, k="pEND", default_value= self.DEF_END)],
                            [sg.B("Save default", k= "pSAVETIME")]]),
                 sg.Column([[sg.T("Change the theme:\n")],
                           [sg.Button("Launch Theme Changer")],
                            [sg.T(f"Your current theme: \n{self.THEME}")]])
                ]
            ])

            self.window = sg.Window("Movati", [[sg.TabGroup([
                [self.Main_Tab, self.Auto_Tab, self.Personalize_Tab]
            ])]])
            return self.window

    def save_default_time(self, start, end):
        self.DEF_START = self.settings["default_start"] = start
        self.DEF_END = self.settings["default_end"] = end
        self.save_settings()
        self.window.close()
        self.create_main_window()

    def change_theme(self, theme= None):
        if theme is None: return
        self.window.close()
        self.THEME = theme
        self.settings["default_theme"] = self.THEME
        sg.theme(self.THEME)
        self.create_main_window()

    def launch_theme_changer(self):
        def create_tabs(current_theme):
            choose_tab = sg.Tab("Choose", [
                [sg.T("Choose a theme:")],
                [sg.LB(sg.theme_list(), s= (20, 12), default_values= [current_theme],
                       k= "THEME", select_mode= "single")],
                [sg.T(f"Current theme:\n\n{current_theme}")],
                [sg.B("Try it"), sg.B("Choose it")], [sg.B("Close Popup")]
            ])
            nothing_tab = sg.Tab("Nothing", [
                [sg.T("Just to see the color of tabs...")]
            ])
            return [[choose_tab, nothing_tab]]

        theme_changer = sg.Window("Theme Chooser", [[sg.TabGroup(create_tabs(self.THEME))]])
        theme = self.THEME
        while True:
            se, sv = theme_changer.read()
            print(se, sv)
            if se in (sg.WIN_CLOSED, "Close Popup"):
                sg.theme(self.THEME)
                break

            elif se == "Try it":
                theme = sv['THEME'][0]
                print(f"\nTYRYING IT:  {theme}")
                theme_changer.close()
                sg.theme(theme)
                theme_changer = sg.Window("Theme Chooser", [[sg.TabGroup(create_tabs(theme))]])

            elif se == "Choose it":
                print(f"\nCHOOSING IT:  {theme}")
                self.change_theme(theme)
                break

        theme_changer.close()

    def show_failed_window(self, failed):
        layout = [
            [sg.T("These Sign Ups have failed for some reason ... ")],
            [sg.LB(failed, s= (60, 10), k= "STATUS", select_mode= "extended")],
            [sg.B("Open"), sg.T(" "*20), sg.B("Close Popup")]
        ]

        failed_window = sg.Window("Failed Sign Ups", layout)
        while True:
            se, sv = failed_window.read()
            print(se, sv)
            if se in (sg.WIN_CLOSED, "Close Popup"):
                failed_window.close();break
            elif se == "Open":
                for link in self.p.Info.loc[self.p.hash_choices(sv["STATUS"]), "Link"]:
                    web.open(link)

    def show_warning_window(self, df):
        layout = [[sg.T("These classes are already full: ")],
            [sg.LB(self.p.make_results_text(df), s= (60, 10), k= "WARNINGS", select_mode= "extended")],
            [sg.B("Open"), sg.T(" "*20), sg.B("Close Popup")]]
        warning_window = sg.Window("Warning", layout)
        while True:
            se, sv = warning_window.read()
            print(se, sv)
            if se in (sg.WIN_CLOSED, "Close Popup"):
                warning_window.close();break
            elif se == "Open":
                for link in self.p.Info.loc[self.p.hash_choices(sv["WARNINGS"]), "Link"]:
                    web.open(link)

    def update_personalize_list(self):
        self.window["pBL"].update(self.p.Lists["Blacklist"])
        self.window["pFAV"].update(self.p.Lists["Favourites"])

    def update_main_options(self, filter_result):
        filter_result = self.p.make_results_text(filter_result)
        self.window["OPTIONS"].update(filter_result)

    def update_auto_tab(self):
        autos = self.p.make_results_text(self.p.AutoSignUp)
        self.window["AUTO"].update(autos)

    def update_registered_tab(self):
        regist = self.p.maket_results_text(self.p.Registered)
        self.window["REGIST"].update(regist)

    def filters_todct(self, v):
        return dict(days=v["DAYS"], favs=v["FAV"], start=v["START"], end=v["END"])

    def launch_main(self):
        while True:
            e, v = self.window.read()
            print(e, v)
            if e in (sg.WIN_CLOSED, "Quit"):
                self.p.save_all()
                self.save_settings()
                # signups = self.p.AutoSignUp[["dtSignTime", "Status", "Link"]].sort_values("dtSignTime") ##########
                # signups["dtSignTime"] = signups["dtSignTime"].astype("string")  ##########
                #
                # self.s.send_update(signups.to_dict())   ##########
                # self.update_completed_failed_autosignups()  ##########
                # self.p.save_all()   ##########
                # self.s.close()  ##########
                break

            ### Main Tab
            elif e == "Filter":
                filter = self.p.create_filter(**self.filters_todct(v))
                results = self.p.apply_filter(filter)
                self.update_main_options(results)

            elif e == "Open":
                for link in self.p.Info.loc[self.p.hash_choices(v["OPTIONS"]), "Link"]: web.open(link)

            elif e == "Add to AutoSignUp":
                failed = self.p.add_to_autosignup(v["OPTIONS"])
                self.update_auto_tab()
                if not failed.empty:
                    self.show_warning_window(failed)

            ### Auto Tab
            elif e == "Remove from AutoSignUp":
                self.p.remove_from_autosignup(v["AUTO"])
                self.update_auto_tab()


            # ### Registered Tab
            # elif e == "Cancel Reservation":
            #     choices = self.p.hash_choices(v["REGIST"])
            #     self.p.cancel_reservations(choices)
            #     self.p.remove_from_registered(choices)
            #     self.update_registered_tab()


            ### Personalize Tab
            elif e in ("addFAV", "addBL"):
                lst = "Favourites" if e == "addFAV" else "Blacklist"
                other = "Blacklist" if e =="addFav" else "Favourites"

                for choice in v["pNAME"]:
                    self.p.Lists[lst].append(choice)
                    try: self.p.Lists[other].remove(choice)
                    except ValueError: pass

                self.update_personalize_list()

            elif e in ("removeFAV", "removeBL"):
                lst, choices = ("Favourites", v["pFAV"]) if e == "removeFAV" else ("Blacklist", v["pBL"])
                for choice in choices: self.p.Lists[lst].remove(choice)
                self.update_personalize_list()

            elif e == "pSAVETIME":
                self.save_default_time(v["pSTART"], v["pEND"])

            elif e == "Launch Theme Changer":
                self.launch_theme_changer()

        self.window.close()



if __name__ == '__main__':
    pass
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