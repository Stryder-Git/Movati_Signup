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

        sg.theme(self.THEME)

        # self.s.connect()   ####
        # self.update_completed_failed_autosignups() ######
        self.create_main_window()



    def get_settings(self):
        with open(self._gui_settings_loc, "r") as settings:
            return load(settings)

    def save_settings(self):
        with open(self._gui_settings_loc, "w") as settings:
            dump(self.settings, settings)

    def update_completed_failed_autosignups(self):
        completed, failed = self.s.get_completed_failed()
        if failed:
            print("received failed")
            have_failed = self.p.AutoSignUp.index.isin(failed)
            failed_text = self.p.make_status_text(self.p.AutoSignUp[have_failed])
            self.show_failed_window(failed_text)

        self.p.update_autosignup(completed, failed)

    def create_main_window(self):
        #### MAIN WINDOW
            ### Main Tab
            # Filter Column
            self.customfilters = [
                [sg.T("Time between: ")],
                [sg.DD(self.p._times, k= "START", default_value= self.DEF_START), sg.T("and"),
                 sg.DD(self.p._times, k= "END", default_value= self.DEF_END)],
                [sg.T("Day:  ")],
                [sg.LB(["All"]+self.p.get_days(), k= "DAYS", s= (25, 10), select_mode= "extended")],
                [sg.CB("Favourites", k= "FAV", default= True)], [sg.CB("AutoSignUp", k= "AUTO")],
                [sg.B("Filter")]
            ]

            df = self.p.apply_filter(self.p.create_filter(
                favs=True, start=self.DEF_START, end=self.DEF_END))
            # Data Column
            self.data = [
                [sg.LB(self.p.make_results_text(df), s=(60, 25), k="OPTIONS", select_mode="extended")],
                [sg.B("Open"), sg.B("Get Status"), sg.B("Add to AutoSignUp"), sg.B("Remove from AutoSignUp")]
            ]
            self.Main_Tab = sg.Tab("Main", [[sg.Column(self.customfilters),
                                             sg.VerticalSeparator(),
                                             sg.Column(self.data)]])

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

            self.window = sg.Window("Movati", [[sg.TabGroup([[self.Main_Tab, self.Personalize_Tab]])]])
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

    def show_status_window(self,lst):
        layout = [[sg.LB(lst, s= (60, 10), k= "STATUS", select_mode= "extended")],
                [sg.B("Open"), sg.B("Add to AutoSignUp"), sg.T(" "*20), sg.B("Close Popup")]]
        status_window = sg.Window("Status Request", layout)
        while True:
            se, sv = status_window.read()
            print(se, sv)
            if se in (sg.WIN_CLOSED, "Close Popup"):
                status_window.close();break
            elif se == "Open":
                for link in self.p.Info.loc[self.p.hash_choices(sv["STATUS"]), "Link"]:
                    web.open(link)
            elif se == "Add to AutoSignUp":
                self.p.add_to_autosignup(sv["STATUS"])

    def update_personalize_list(self):
        self.window["pBL"].update(self.p.Lists["Blacklist"])
        self.window["pFAV"].update(self.p.Lists["Favourites"])

    def update_main_options(self, filter_result):
        filter_result = self.p.make_results_text(filter_result)
        self.window["OPTIONS"].update(filter_result)

    def filters_todct(self, v):
        return dict(days=v["DAYS"], favs=v["FAV"], auto=v["AUTO"],
                    start=v["START"], end=v["END"])

    def update_filters(self):
        filters = list(self.p.Filters.keys())
        self.window["FILTERS"].update(values= filters)
        self.window["pFILTERS"].update(filters)

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

            elif e == "Filter":
                filter = self.p.create_filter(**self.filters_todct(v))
                results = self.p.apply_filter(filter)
                self.update_main_options(results)

            elif e == "Get Status":
                full_info = self.p.update_full_info(self.p.hash_choices(v["OPTIONS"]))
                updated_options = self.p.apply_filter(self.p.lastfilter)
                self.update_main_options(updated_options)

                # create and run the pop up showing the requested status
                resp = self.p.make_status_text(full_info)
                self.show_status_window(resp)


            elif e == "Open":
                for link in self.p.Info.loc[self.p.hash_choices(v["OPTIONS"]), "Link"]: web.open(link)

            elif e == "Add to AutoSignUp":
                self.p.add_to_autosignup(v["OPTIONS"])

            elif e == "Remove from AutoSignUp":
                self.p.remove_from_autosignup(v["OPTIONS"])

            elif e == "SAVE":
                n = v["SAVEAS"]
                if n in list(self.p.Filters.keys())+ ["Favourites", "Blacklist", "AutoSignUp"]:
                    sg.popup_ok("Please choose a different name.\n "
                                "The chosen one is either taken or part of one of "
                                "'Favourites, 'Blacklist', and 'AutoSignUp', which are reserved.")
                    continue
                self.p.Filters[n] = self.filters_todct(v)
                self.update_filters()

            elif e in ("addFAV", "addBL"):
                lst = "Favourites" if e == "addFAV" else "Blacklist"
                for choice in v["pNAME"]: self.p.Lists[lst].append(choice)
                self.update_personalize_list()

            elif e in ("removeFAV", "removeBL"):
                lst, choices = ("Favourites", v["pFAV"]) if e == "removeFAV" else ("Blacklist", v["pBL"])
                for choice in choices: self.p.Lists[lst].remove(choice)
                self.update_personalize_list()

            elif e == "removeFILTER":
                for f in v["pFILTERS"]: del self.p.Filters[f]
                self.update_filters()

            elif e == "pSAVETIME":
                self.save_default_time(v["pSTART"], v["pEND"])

            elif e == "Launch Theme Changer":
                self.launch_theme_changer()

        self.window.close()
