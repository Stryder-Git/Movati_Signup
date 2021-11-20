import PySimpleGUI as sg
import webbrowser as web
from json import load, dump


class GUI:
    _gui_settings_loc = ".\\Data\\gui_settings.json"


    def __init__(self, p, s, create_main_window= True):
        self.p = p
        self.s = s

        self.settings = self.get_settings()
        self.THEME = self.settings["default_theme"]
        self.DEF_START= self.settings["default_start"]
        self.DEF_START_AM = bool(self.settings["default_start_am"])

        self.DEF_END = self.settings["default_end"]
        self.DEF_END_AM = bool(self.settings["default_end_am"])

        self.DEF_FAV = bool(self.settings["default_favourites"])

        sg.theme(self.THEME)

        if self.s.connect():
            self.update_completed_failed_autosignups()
        else:
            print("not connected")

        if create_main_window:
            self.create_main_window()

    def get_settings(self):
        with open(self._gui_settings_loc, "r") as settings:
            return load(settings)
    def save_settings(self):
        with open(self._gui_settings_loc, "w") as settings:
            dump(self.settings, settings)

    def save_default_favourites(self, new_def):
        print("saving favourites: ", new_def)
        self.DEF_FAV = self.settings["default_favourites"] = new_def
        self.save_settings()

    def save_default_time(self, start, start_am, end, end_am):
        print("saving time: ", start, end)
        self.DEF_START = self.settings["default_start"] = start
        self.DEF_START_AM = self.settings["default_start_am"] = start_am
        self.DEF_END = self.settings["default_end"] = end
        self.DEF_END_AM = self.settings["default_end_am"] = end_am
        self.save_settings()

    def change_theme(self, theme= None):
        print("saving theme: ", theme)
        if theme is None: return
        self.window.close()
        self.THEME = theme
        self.settings["default_theme"] = self.THEME
        self.save_settings()
        sg.theme(self.THEME)
        self.create_main_window()

    def update_completed_failed_autosignups(self):
        completed, failed = self.s.get_completed_failed()
        if failed:
            print("received failed")
            have_failed = self.p.AutoSignUp[self.p.AutoSignUp.index.isin(failed)]
            self.show_warning_window(have_failed, "These signups have failed for some reason ...")

        self.p.remove_from_autosignup(completed + failed)

    def resolve(self, choices, df):
        """this should get a list with the choices, a list with the options that were chosen from
            and the dataframe that the options list was created from
        """
        return df.index[choices]

    def create_main_window(self):
        #### MAIN WINDOW
            ### Main Tab
            # Filter Row
            self.customfilters = [sg.Column(
                [[sg.T("Time between: ")],
                [sg.DD(self.p._times, k= "START", default_value= self.DEF_START), sg.T("and"),
                 sg.DD(self.p._times, k= "END", default_value= self.DEF_END)],
                [sg.CB("am", key= "START_AM", default= self.DEF_START_AM), sg.T(" "*10),
                 sg.CB("am", key= "END_AM", default= self.DEF_END_AM)]
                ]),
                sg.Column([[sg.LB(["All"]+self.p.get_days(), k= "DAYS", s= (25, 7), select_mode= "extended")]
                ]),
                sg.Column([
                [sg.CB("Only Favourites", k= "FAV", default= self.DEF_FAV)], [sg.B("Filter")]
                ])
            ]
            df = self.p.apply_filter(self.p.create_filter(favs=self.DEF_FAV, start= self.DEF_START,
                                                          start_am= self.DEF_START_AM, end=self.DEF_END,
                                                          end_am= self.DEF_END_AM))
            self._main_values, self._main_df = self.p.prepare_data(df)
            # Data Row
            self.data = [
                [sg.Table(values= self._main_values, headings= self.p.RESCOLSA, size=(80, 15),
                          select_mode= sg.TABLE_SELECT_MODE_EXTENDED, k="OPTIONS")],
                [sg.B("Open"), sg.B("Add to AutoSignUp"), sg.B("Remove from AutoSignUp", k="OPTIONSREMOVE")]]

            self.Main_Tab = sg.Tab("Main", [self.customfilters, *self.data])


            self._auto_values, self._auto_df = self.p.prepare_data(self.p.AutoSignUp, auto_col= False)
            ### AutoSignup Tab
            self.Auto_Tab = sg.Tab("AutoSignUp", [
                [sg.Table(values= self._auto_values, headings= self.p.RESCOLS, size= (80, 15),
                          select_mode= sg.TABLE_SELECT_MODE_EXTENDED, k= "AUTO", max_col_width= 100)],
                [sg.B("Remove from AutoSignUp", k= "AUTOREMOVE")]])

            ### Personalize Tab
            col_height = 8
            self.Personalize_Tab = sg.Tab("Personalize", [[
                sg.Column([[sg.T("Available Classes:")],
                    [sg.LB(sorted(self.p.get_class_names()), s= (24, col_height), k= "pNAME", select_mode= "extended")],
                    [sg.T("Add to: "), sg.B("Favourites", k= "addFAV"), sg.B("Blacklist", k= "addBL")]]),
                sg.Column([[sg.T("Favourites:")],
                    [sg.LB(sorted(self.p.Lists["Favourites"]), s= (23, col_height), k= "pFAV", select_mode= "extended")],
                    [sg.B("Remove", k= "removeFAV")]]),
                sg.Column([[sg.T("Blacklist:")],
                    [sg.LB(sorted(self.p.Lists["Blacklist"]), s= (23, col_height), k= "pBL", select_mode= "extended")],
                    [sg.B("Remove", k= "removeBL")]])
                ],
                [sg.Column([[sg.T("Default time between:")],
                             [sg.DD(self.p._times, k="pSTART", default_value= self.DEF_START,
                                    enable_events= True), sg.T("and"),
                              sg.DD(self.p._times, k="pEND", default_value= self.DEF_END,
                                    enable_events= True)],
                            [sg.CB("am", key="pSTART_AM", default=self.DEF_START_AM,
                                   enable_events= True), sg.T(" " * 10),
                             sg.CB("am", key="pEND_AM", default=self.DEF_END_AM,
                                   enable_events= True)]
                            ]),
                 sg.Column([[sg.T("Change the theme:\n")],
                           [sg.Button("Launch Theme Changer")],
                            [sg.T(f"Your current theme: \n{self.THEME}")]]),
                 sg.Column([[sg.T("Default favourites at start?")],
                            [sg.CB("Yes.", k= "DEF_FAV", default= self.DEF_FAV, enable_events= True)]])
                ]
            ])
            self.window = sg.Window("Movati", [[sg.TabGroup([[self.Main_Tab,
                                                              self.Auto_Tab,
                                                              self.Personalize_Tab]])]])
            return self.window

    def show_warning_window(self, df, msg="", info= None, buttons= None):
        values, df = self.p.prepare_data(df)
        if info is None:
            info = [sg.Table(values= values, headings= self.p.RESCOLSA,
                             s= (70, 10), k= "OPTIONS")]
        if buttons is None:
            buttons = [sg.B("Open"), sg.T(" "*90), sg.B("Close Popup")]

        layout = [[sg.T(msg)], info, buttons]
        failed_window = sg.Window("Warning", layout)
        while True:
            se, sv = failed_window.read()
            print(se, sv)
            if se in (sg.WIN_CLOSED, "Close Popup"):
                failed_window.close();break
            elif se == "Open":
                for link in self.p.Info.loc[self.resolve(sv["OPTIONS"], df), "Link"]:
                    web.open(link)

    def update_main_options(self, filter_result):
        self._main_values, self._main_df = self.p.prepare_data(filter_result)
        self.window["OPTIONS"].update(values= self._main_values)

    def update_auto_tab(self):
        self._auto_values, self._auto_df = self.p.prepare_data(self.p.AutoSignUp, auto_col= False)
        self.window["AUTO"].update(values= self._auto_values)

    def update_personalize_list(self):
        self.window["pBL"].update(sorted(self.p.Lists["Blacklist"]))
        self.window["pFAV"].update(sorted(self.p.Lists["Favourites"]))

    def filters_todct(self, v):
        return dict(days=v["DAYS"], favs=v["FAV"], start=v["START"],
                    start_am= v["START_AM"], end=v["END"], end_am= v["END_AM"])

    def launch_main(self):
        while True:
            e, v = self.window.read()
            print(e, v)
            if e in (sg.WIN_CLOSED, "Quit"):
                self.p.save_all()
                self.save_settings()
                signups = self.p.AutoSignUp[["dtSignTime", "Status", "Link"]].sort_values("dtSignTime") ##########
                signups["dtSignTime"] = signups["dtSignTime"].astype("string")  ##########

                if self.s.connected:
                    self.s.send_update(signups.to_dict())   ##########
                    self.update_completed_failed_autosignups()  ##########
                    self.p.save_all()
                    self.s.close()  ##########
                else:
                    print("not connected")

                break

            ### Main Tab
            elif e == "Filter":
                filter = self.p.create_filter(**self.filters_todct(v))
                results = self.p.apply_filter(filter)
                self.update_main_options(results)

            elif e == "Open":
                choices = self.resolve(v["OPTIONS"], self._main_df)
                for link in self.p.Info.loc[choices, "Link"]: web.open(link)

            elif e == "Add to AutoSignUp":
                choices = self.resolve(v["OPTIONS"], self._main_df)
                failed = self.p.add_to_autosignup(choices)
                self.update_auto_tab()

                results = self.p.apply_filter(self.p.lastfilter)
                self.update_main_options(results)

                if not failed.empty:
                    self.show_warning_window(failed, "These classes seem to be unavailable")


            ### Remove from AutoSignUp -- Main_Tab & Auto_Tab
            elif e in ("OPTIONSREMOVE", "AUTOREMOVE"):
                _e = e.replace("REMOVE", "")
                choices = self.resolve(v[_e], self._auto_df if _e == "AUTO" else self._main_df)

                self.p.remove_from_autosignup(choices)
                self.update_auto_tab()

                results = self.p.apply_filter(self.p.lastfilter)
                self.update_main_options(results)

            ### Personalize Tab
            elif e in ("addFAV", "addBL"):
                lst = "Favourites" if e == "addFAV" else "Blacklist"
                other = "Blacklist" if e =="addFAV" else "Favourites"
                for choice in v["pNAME"]:
                    try: self.p.Lists[other].remove(choice)
                    except ValueError: pass
                    try: self.p.Lists[lst].remove(choice)
                    except ValueError: pass
                    self.p.Lists[lst].append(choice)

                self.update_personalize_list()

            elif e in ("removeFAV", "removeBL"):
                lst, choices = ("Favourites", v["pFAV"]) if e == "removeFAV" else ("Blacklist", v["pBL"])
                for choice in choices: self.p.Lists[lst].remove(choice)
                self.update_personalize_list()

            elif e in ("pSTART", "pEND", "pSTART_AM", "pEND_AM"):
                self.save_default_time(v["pSTART"], v["pSTART_AM"], v["pEND"], v["pEND_AM"])

            elif e == "DEF_FAV":
                self.save_default_favourites(v["DEF_FAV"])

            elif e == "Launch Theme Changer":
                self.launch_theme_changer()

        self.window.close()

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
                self.window.close()
                sg.theme(self.THEME)
                self.create_main_window()
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
