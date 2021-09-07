from Movati_SignUp import GUI, Dobby, Presenter
#
# gui = GUI(Presenter(), Dobby())
# gui.launch_main()
#
from Tests import test_presenter

for att in dir(test_presenter):
    if att.startswith("test_"):
        print("running: ", att)
        getattr(test_presenter, att)()

