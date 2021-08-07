from Getter import Getter
from time import sleep
from datetime import datetime as dt
import requests
from bs4 import BeautifulSoup

class SignUp(Getter):

    def __int__(self, set_signups= True):
        Getter.__init__(self, get_site= False)

    def get_signups(self):
        istoday = self.Info["dtSignTime"].dt.date.eq(self.today, fill_value= self.today)
        if self.AutoSignUp: isonsignup = self.Info.index.isin(self.AutoSignUp)
        else: isonsignup = ~self._alltrue()
        signups = self.Info.loc[isonsignup & istoday]
        signups = signups[["dtSignTime", "Status", "Link"]].sort_values("dtSignTime")
        self.mylogger.info(f"{'='*50}\nToday's sign ups:\n{signups.to_string()}")
        return signups

    def schedule_sign(self, signups):
        for index, signup in signups.iterrows():
            self.mylogger.info(f"setting up {signup}")

            if signup["Status"] in (self.AVAILABLE, self.WAITLIST):
                wait = (signup["dtSignTime"] - dt.now()).total_seconds()
                sleep(max(0, wait))
                self.mylogger.info(f"signing up..")
                signedup = self.signup(signup["Link"])
                self.mylogger.info(f"sign up was{' ' if signedup else ' NOT '}successful")
            else:
                self.mylogger.info("not available for sign up or full status not available")

            self.AutoSignUp.remove(index)
            with open(self.SIGNEDLOC, "a") as signed: signed.write(index+"\n")


    def signup_form(self, token):
        form = {i["name"]: i["value"] for i in token}
        if "action" in form:
            if form["action"] == "waitlist": form["submit"] = "Join the Waitlist"
            elif form["action"] == "reserve": form["submit"] = "Reserve a Spot"
        else:
            self.mylogger.info("'action' wasn't in form, this relates to the error I once had,\n"
                  "check if everything is well.")
        return form

    def signup(self, link):
        # On the class page
        sop, session, signup_page_link = self.login_get(link, keep= True)
        eralrts = sop.find_all(class_="alert alert-error")
        success= False
        if not eralrts:
            token = sop.find_all(attrs={"type": "hidden"})
            form = self.signup_form(token)
            response = session.post(signup_page_link, data=form)
            # On confirmation page
            sop = BeautifulSoup(response.text, "lxml")
            sucalrts = sop.find_all(class_="alert alert-success")
            if sucalrts:
                for sals in sucalrts: self.mylogger.info(sals.text)
                success = True
            else:
                self.mylogger.info("Confirmation page different than expected")
                alrts = sop.find_all(class_="alert alert-error")
                if alrts:
                    for als in alrts: self.mylogger.info(als.text)
        else:
            self.mylogger.info("Signup page different than expected")
            for als in eralrts: self.mylogger.info(als.text)
        session.close()
        return success


if __name__ == '__main__':
    print("HEllo World")
    su = SignUp()
    if su.AutoSignUp:
        signups = su.get_signups()
        su.schedule_sign(signups)

