from .Presenter import Presenter
import PySimpleGUI as sg
import webbrowser as web
import socket as sk
from json import loads, dumps, load


class Dobby:
    SIZE = 22
    F = "utf-8"

    def __init__(self, connect=True):
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)

    def connect(self):
        try:
            print("trying to connect")
            self.socket.connect((sk.gethostbyname("MPC"), 1289))
            self.send("movati", "")
        except OSError:
            sg.popup_ok("Could not connect to server, make sure laptop is running")
            exit()

    def close(self):
        try:
            self.socket.shutdown(sk.SHUT_RDWR)
            self.socket.close()
        except OSError:
            pass

    def get_completed(self):
        print("getting completed")
        length, flag = self.socket.recv(self.SIZE).decode(self.F).split("::")
        if flag.strip() == "CANCEL":
            print("cancel flag")
            sg.popup_ok("There seem to be two GUIs trying to connect,"
                        " please use only the first one you opened. (Clicking OK will close the right one)")
            self.close()
            exit()
        return loads(self.socket.recv(int(length)).decode(self.F))

    def get_failed(self):
        print("getting failed")
        length, flag = self.socket.recv(self.SIZE).decode(self.F).split("::")
        return loads(self.socket.recv(int(length)).decode(self.F))

    def send(self, flag, msg):
        msg = msg.encode(self.F)
        header = f"{len(msg)}::{flag}"
        msg = f"{header:<{self.SIZE}}".encode(self.F) + msg
        self.socket.send(msg)

    def send_update(self, data):
        data = dumps(data)
        self.send("update", data)
        print("sent: ", data)


class GUI:

    def __init__(self, p, s):
        self.p = p
        self.s = s

        with open(".\\Data\\gui_settings.json", "r") as settings:
            settings = load(settings)
        self.THEME = settings["default_theme"]
        sg.theme(self.THEME)

        self.s.connect()

        completed = self.s.get_completed()
        failed = self.s.get_failed()
        if failed:
            have_failed = self.p.AutoSignUp.index.isin(failed)
            failed_text = self.p.make_status_text(self.p.AutoSignUp[have_failed])
            self.show_failed_window(failed_text)

        self.p.update_autosignup(completed, failed)
        self.create_main_window()

    def create_main_window(self):
        #### MAIN WINDOW
            ### Main Tab
            # Filter Column
            self.customfilters = [
                [sg.T("Name: "), sg.T(" "*18), sg.T("Day:  ")],
                [sg.LB(["All"]+self.p.get_class_names(), k= "NAME", s= (16, 10), select_mode= "extended"),
                                sg.LB(["All"]+self.p.get_days(), k= "DAYS", s= (16, 10), select_mode= "extended")],
                [sg.CB("Favourites", k= "FAV")], [sg.CB("Blacklist", k= "BL")], [sg.CB("AutoSignUp", k= "AUTO")],
                [sg.CB("Basic", k= "BASIC"), sg.CB("Full", k= "FULL")], [sg.B("Filter")],

                [sg.B("Save Filter as: ", k= "SAVE"), sg.I(s= (20, 1), k="SAVEAS")], [sg.T("_"*40)],
                [sg.B("Favourites"), sg.B("AutoSignUp")], [sg.T("Saved Filters: ")],
                [sg.DD(list(self.p.Filters.keys()), k= "FILTERS", s= (30,1)), sg.B("Filter", k= "SAVEDFILTER")]
            ]
            # Data Column
            self.data = [
                [sg.LB(self.p.make_results_text(), s=(60, 25), k="OPTIONS", select_mode="extended")],
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
                [sg.Column([[sg.T("Saved Filters:")], [sg.LB(list(self.p.Filters.keys()), s= (30, col_height), k= "pFILTERS")],
                          [sg.B("Remove", k= "removeFILTER")]])
                ]
            ])

            self.window = sg.Window("Movati", [[sg.TabGroup([[self.Main_Tab, self.Personalize_Tab]])]])
            return self.window

    def change_theme(self, theme= None):
        self.window.close()
        sg.theme(theme or self.THEME)
        self.create_main_window()


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
            elif se == "Add to AutoSignUp":
                self.p.add_to_autosignup(sv["STATUS"])


    #### STATUS WINDOW
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
        return dict(names=v["NAME"], days=v["DAYS"], favs=v["FAV"], bl=v["BL"],
                    auto=v["AUTO"], basic=v["BASIC"], full= v["FULL"])

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
                signups = self.p.AutoSignUp[["dtSignTime", "Status", "Link"]].sort_values("dtSignTime")
                signups["dtSignTime"] = signups["dtSignTime"].astype("string")

                self.s.send_update(signups.to_dict())
                self.s.close()
                break

            elif e in ("Favourites", "AutoSignUp"):
                results = self.p.apply_filter(e)
                self.update_main_options(results)

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

            elif e == "SAVEDFILTER":
                results = self.p.apply_filter(v["FILTERS"])
                self.update_main_options(results)

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