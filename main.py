from Movati_SignUp import GUI, Dobby, Presenter

gui = GUI(Presenter(), Dobby())
gui.launch_main()


# from threading import Thread, active_count
# from time import sleep
#
# A = "no"
#
# def to_stop():
#     for i in range(1, 102, 2):
#         sleep(2)
#         print(" *** ** * still running")
#         if A.lower() == "yes":
#             break
#     print("-- stopped to_stop")
#
# print(active_count())
# Thread(target= to_stop, daemon= True).start()
# print(active_count())
#
# while A.lower() not in ("both", "this"):
#     A = input("stop?:  ")
#
# print("------- broke input loop ---> :")
# sleep(3)
# print(active_count())
#
# # exit()



