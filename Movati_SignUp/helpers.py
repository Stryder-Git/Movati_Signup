import os
import shutil
import socket as sk
import PySimpleGUI as sg
from json import loads, dumps

class Dobby:
    SIZE = 22
    F = "utf-8"

    def __init__(self):
        self.socket = sk.socket(sk.AF_INET, sk.SOCK_STREAM)

    def connect(self):
        try:
            print("trying to connect")
            self.socket.connect((sk.gethostbyname("MPC"), 1289))
            self.send("movati", "")
        except OSError:
            sg.popup_ok("Could not connect to server, make sure laptop is running")
            exit()
        self.make_initial_exchange()

    def read(self, length = SIZE): return self.socket.recv(length).decode(self.F)


    def make_initial_exchange(self):
        """first flag dobby sends is either CANCEL or an integer
        if CANCEL, two guis are connected and need to be closed
        if int(flag) than that is the number of files that will be sent seperately
        and need to be installed"""

        length, flag = self.read().split("::")
        flag = flag.strip()
        if flag == "CANCEL":
            print("cancel flag")
            sg.popup_ok("There seem to be two GUIs trying to connect,"
                        " please use only the first one you opened. (Clicking OK will close the right one)")
            self.close()
            exit()

        num_updates = int(flag)
        for i in range(1, num_updates + 1):
            print(f"installing update number {i} of {num_updates}")
            length, filename = self.read().split("::")
            contents = self.read(int(length))
            install_update(filename.strip(), contents)

        if num_updates:
            sg.popup_ok("Updates were installed, press ok to close this GUI and then you can restart it")
            self.close()
            exit()

    def close(self):
        try:
            self.socket.shutdown(sk.SHUT_RDWR)
            self.socket.close()
        except OSError:
            pass

    def get_completed_failed(self):
        print("getting completed")
        length, flag = self.read().split("::")
        completed = loads(self.read(int(length)))
        print(completed)

        print("getting failed")
        length, flag = self.read().split("::")
        failed = loads(self.read(int(length)))
        print(failed)
        return completed, failed

    def make_msg(self, flag, msg):
        msg = msg.encode(self.F)
        header = f"{len(msg)}::{flag}"
        return f"{header:<{self.SIZE}}".encode(self.F) + msg

    def send(self, flag, msg):
        self.socket.send(self.make_msg(flag, msg))

    def send_update(self, data):
        data = dumps(data)
        self.send("update", data)
        print("sent: ", data)



class Update_Installer:
    """
    How?

    this file is passed to install_update(filename, file)

    if the file exists, replace it

    if it doesn't, create it

    """
    def __init__(self):
        self.code_folder = "Movati_Signup"
        self.project_folder = "."

    def __call__(self, filename, contents, backup= True):
        if not (isinstance(filename, str) and isinstance(contents, str)):
            raise ValueError(f"filename and contents must be string")
        if "." in filename or ".py" in filename:
            raise ValueError(f"something about the extension in filename: {filename} is wrong,"
                             f"don't use extensions")

        filepath = os.path.join(self.code_folder, filename + ".py")
        if os.path.exists(filepath):
            print("deleting ", filepath)

            if backup:
                print("backing up ", filepath)
                target = os.path.join(self.code_folder, "old", filename + ".py")
                if os.path.exists(target): os.remove(target)
                shutil.copy(filepath, target)

            os.remove(filepath)

        print("creating ", filepath)
        with open(filepath, "w") as file:
            file.write(contents)

        print("update installed")

install_update = Update_Installer()
