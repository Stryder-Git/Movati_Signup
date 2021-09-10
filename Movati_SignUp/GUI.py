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

        # self.s.connect()   ####
        # self.update_completed_failed_autosignups() ######
        self.create_main_window()

    def get_settings(self):
        with open(self._gui_settings_loc, "r") as settings:
            return load(settings)
    def save_settings(self):
        with open(self._gui_settings_loc, "w") as settings:
            dump(self.settings, settings)


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

    def update_completed_failed_autosignups(self):
        completed, failed = self.s.get_completed_failed()
        if failed:
            print("received failed")
            have_failed = self.p.AutoSignUp[self.p.AutoSignUp.index.isin(failed)]
            self.show_warning_window(have_failed)

        self.p.remove_from_autosignup(completed + failed)

    def resolve(self, choices, options, df):
        """this should get a list with the choices, a list with the options that were chosen from
            and the dataframe that the options list was created from
        """
        # first get the index of the choices in the options list [these are the integer locations in df.index]
        ix = [options.index(choice)-1 for choice in choices] # -1 because the first row in options are the columns
        # then return the indexes at the integer locations
        return df.index[ix]

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
            self._main_options, self._main_df = self.p.make_results_text(df)

            # Data Row
            self.data = [
                [sg.LB(self._main_options, s=(80, 15), k="OPTIONS", select_mode="extended")],
                [sg.B("Open"), sg.B("Add to AutoSignUp")]]

            self.Main_Tab = sg.Tab("Main", [self.customfilters, *self.data])


            self._auto_options, self._auto_df = self.p.make_results_text(self.p.AutoSignUp)
            ### AutoSignup Tab
            self.Auto_Tab = sg.Tab("AutoSignUp", [
                [sg.LB(self._auto_options, s= (80, 15), k= "AUTO", select_mode= "extended")],
                [sg.B("Remove from AutoSignUp")]])

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

            self.window = sg.Window("Movati", [[sg.TabGroup([[self.Main_Tab,
                                                              self.Auto_Tab,
                                                              self.Personalize_Tab]])]])
            return self.window



    def show_warning_window(self, df, msg=""):
        options, df = self.p.make_results_text(df)

        layout = [
            [sg.T(msg)],
            [sg.LB(options, s= (60, 10), k= "OPTIONS", select_mode= "extended")],
            [sg.B("Open"), sg.T(" "*20), sg.B("Close Popup")]
        ]

        failed_window = sg.Window("Warning", layout)
        while True:
            se, sv = failed_window.read()
            print(se, sv)
            if se in (sg.WIN_CLOSED, "Close Popup"):
                failed_window.close();break
            elif se == "Open":
                for link in self.p.Info.loc[self.resolve(sv["OPTIONS"], options, df), "Link"]:
                    web.open(link)

    def update_main_options(self, filter_result):
        self._main_options, self._main_df = self.p.make_results_text(filter_result)
        self.window["OPTIONS"].update(self._main_options)

    def update_auto_tab(self):
        self._auto_options, self._auto_df = self.p.make_results_text(self.p.AutoSignUp)
        self.window["AUTO"].update(self._auto_options)

    def update_personalize_list(self):
        self.window["pBL"].update(self.p.Lists["Blacklist"])
        self.window["pFAV"].update(self.p.Lists["Favourites"])

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
                choices = self.resolve(v["OPTIONS"], self._main_options, self._main_df)
                for link in self.p.Info.loc[choices, "Link"]: web.open(link)

            elif e == "Add to AutoSignUp":
                choices = self.resolve(v["OPTIONS"], self._main_options, self._main_df)
                failed = self.p.add_to_autosignup(choices)
                self.update_auto_tab()
                if not failed.empty:
                    self.show_warning_window(failed, "These classes seem to be unavailable")


            ### Auto Tab
            elif e == "Remove from AutoSignUp":
                choices = self.resolve(v["AUTO"], self._auto_options, self._auto_df)
                self.p.remove_from_autosignup(choices)
                self.update_auto_tab()


            ### Personalize Tab
            elif e in ("addFAV", "addBL"):
                print('handling adding')
                lst = "Favourites" if e == "addFAV" else "Blacklist"
                other = "Blacklist" if e =="addFAV" else "Favourites"
                print(lst, other)
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

            elif e == "pSAVETIME":
                self.save_default_time(v["pSTART"], v["pEND"])

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
