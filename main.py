from Movati_SignUp import GUI, Dobby, Presenter, Getter

# g = Getter(get_site=True)
#
# links = ["https://api.groupexpro.com/gxp/reservations/start/index/12414350/09/11/2021"]
#
# g.cancel_reservations(links)

gui = GUI(Presenter(), Dobby())
gui.launch_main()

# from Tests import test_presenter
#
# for att in dir(test_presenter):
#     if att.startswith("test_"):
#         print("running: ", att)
#         getattr(test_presenter, att)()

