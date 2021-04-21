import requests as reqs
from bs4 import BeautifulSoup

r = reqs.get("https://movatiathletic.com/club-schedules/?club=guelph")
soup = BeautifulSoup(r.text, "lxml")
classes = soup.find(id= "classes")
days = classes.find_all(class_= "classDescription")[:8]

print(days[0]["id"])
print(days[0].find(class_= "classRow general mens-pool staff morning start-5").text)