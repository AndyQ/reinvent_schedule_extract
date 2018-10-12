############################################################################################
#### AWS re:Invent 2018 - Session Information Downloader
# Provides a quick dirty way to export AWS re:Invent session content from the event website.
# Requirements:
#   1. Update your event website credentials in the USERNAME and PASSWORD vars.
#   2. Download the Chrome web driver (https://sites.google.com/a/chromium.org/chromedriver/downloads).
#   3. Change the CHROME_DRIVER var to point to the driver location.
#
# @author written by Matt Adorjan 
# @email matt.adorjan@gmail.com
############################################################################################

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import os
import shutil
from time import sleep
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json


from config import USERNAME, PASSWORD

# Set to True to download the data from the web OR False to use a pre-downloaded set of data
# useful if you want to change the parsed datasets
downloadDataFromWeb = True

# Chrome web driver path
CHROME_DRIVER = './chromedriver'

# Venetian, Encore, Aria, MGM, Mirage, Bellagio, Vdara
VENUE_NAMES = ["Venetian", "Encore", "Aria", "MGM", "Mirage", "Bellagio", "Vdara"]
VENUE_CODES = [22188,728,22191,22190,22583,22584,24372]
DAY_IDS = [170,31,110,111,112]
DAY_NAMES = ["Mon","Tue","Wed","Thur","Fri"]

# Initialize headless chrome
chrome_options = Options()

# Uncomment this out to run the chromedriver in headless mode (hides the display)
#chrome_options.add_argument("--headless")

content_to_parse = ''
events = []

def login(chrome_driver, username, password):
    '''
    Handle user login to the reinvent session catalog.
    Utilizes headless chrome, passing in username and password
    '''
    chrome_driver.get("https://www.portal.reinvent.awsevents.com/connect/login.ww")
    username_field = chrome_driver.find_element_by_id("loginUsername")
    username_field.send_keys(username)
    password_field = chrome_driver.find_element_by_id("loginPassword")
    password_field.send_keys(password)
    cookieAccept = chrome_driver.find_element_by_id( "cookieAgreementAcceptButton" )
    cookieAccept.click()
    login_button = chrome_driver.find_element_by_id("loginButton")
    login_button.click()

def loadSessonContentsFromURL( driver, venue, day ):
    global content_to_parse

    # Getting content by day, instead of the entire set, because sometimes the
    # Get More Results link stops working on the full list. Haven't had issues
    # looking at the lists day by day.
    driver.get("https://www.portal.reinvent.awsevents.com/connect/search.ww#loadSearch-searchPhrase=&searchType=session&tc=0&sortBy=abbreviationSort&dayID={}&p=&i(728)={}".format( DAY_IDS[day], VENUE_CODES[venue]))
    #d sdriver.get("https://www.portal.reinvent.awsevents.com/connect/search.ww#loadSearch-searchPhrase=&searchType=session&tc=0&sortBy=daytime&dayID=170&p=")

    sleep(3)
    print ("Getting Content for Venue Code: {} on {}".format(VENUE_NAMES[venue], DAY_NAMES[day]))
    more_results = True
    # Click through all of the session results pages for a specific day.
    # The goal is to get the full list for a day loaded.
    while(more_results):
        try:
            # Find the Get More Results link and click it to load next sessions
            get_results_btn = driver.find_element_by_link_text("Get More Results")
            get_results_btn.click()
            sleep(1)
        except NoSuchElementException as e:
            more_results = False

    # Go through all the links and expand the scheduling options
    progress = driver.execute_script('''
    links = document.querySelectorAll(".expandSessionImg:not(.expanded)");
    links.forEach(link => link.click());
    ''')
    sleep(2)

    # write to <venueid>.txt
    with open( "./output/webdata/{}_{}.txt".format(VENUE_NAMES[venue], DAY_NAMES[day]), "w") as out:
        out.write( driver.page_source )


def loadSessonContentsFromFile( ):
    global content_to_parse
    # Getting content by day, instead of the entire set, because sometimes the
    # Get More Results link stops working on the full list. Haven't had issues
    # looking at the lists day by day.
    for venue in range(0, len(VENUE_CODES)):
        for day in range(0, len(DAY_IDS)):
            with open( "./output/webdata/{}_{}.txt".format(VENUE_NAMES[venue], DAY_NAMES[day]), "r") as input:
                data = input.read()
                extractSessionsFromHTML( VENUE_NAMES[venue], DAY_NAMES[day], data, "./output/csv/sessions_{}_{}.csv".format(VENUE_NAMES[venue], DAY_NAMES[day]) )
                #content_to_parse = content_to_parse + data


def extractSessionsFromHTML( venueName, dayName, html, outputFile ):
    global events
    # Start the process of grabbing out relevant session information and writing to a file
    #soup = BeautifulSoup(content_to_parse, "html5lib")
    soup = BeautifulSoup(html, "html.parser")

    # In some event titles, there are audio options available inside of an 'i' tag
    # Strip out all 'i' tags to make this easier on BS
    # Hopefully there is no other italicized text that I'm removing
    for i in soup.find_all('i'):
        i.extract()

    # Grab all of the sessionRows from the final set of HTML and work only with that
    sessions = soup.find_all("div", class_="sessionRow")

    print( "Found {} sessions for {} on {}".format(len(sessions), venueName, dayName))

    # Open a blank text file to write sessions to
    file = open(outputFile,"w")

    # Create a header row for the file. Note the PIPE (|) DELIMITER.
    file.write("Session Number,Session Title,Session Desc,Session Level,Session Type,Session Speakers,Session Interest,Day,Start Time,End Time,Building,Room\n")

    # For each session, pull out the relevant fields and write them to the sessions.txt file.
    unableToGet = []
    for session in sessions:
        session_soup = BeautifulSoup(str(session), "html.parser")
        session_id = session_soup.find("div", class_="sessionRow")
        session_id = session_id['id']
        session_id = session_id[session_id.find("_")+1:]

        # Grab the schedule timings
        text = ""
        item = session_soup.find( "ul", class_="availableSessions")
        if item != None:
            text = item.text

        reserved = False
        if text.startswith("Unreserve seat"):
            reserved = True
        text = text.replace("You have a conflict with this session time in your schedule.", "" )
        text = text.replace("Add to Waitlist", "" )
        text = text.replace("Remove from Waitlist", "" )
        text = text.replace("Reserve seat", "" )
        text = text.replace("Unreserve seat", "" )
        #print( "{} - [{}]".format( session_id, text ) )
        #text = text[37:]
        #print( "{} - [{}]".format( session_id, text ) )

        match = re.search("([^,]*), ([^,]*), ([^-]*)- ([^-–]*). ([^,]*), ([^,]*)[, ]*(.*)", text, re.DOTALL | re.MULTILINE)
        if match == None:
            unableToGet.append( session_id )
            session_timing = {
                "start_time": "Unknown",
                "end_time": "Unknown",
                "building": "Unknown",
                "room": "Unknown",
                "day": "Unknown",
            }
        else:
            groups = match.groups()

            session_timing = {
                "start_time": groups[2].strip(),
                "end_time": groups[3].strip(),
                "building": groups[4].strip(),
                "room": "{} - {}".format(groups[5].strip(), groups[6].strip().replace( ",", " - ")),
                "day": "{}".format(groups[1].strip())
            }

        if session_timing["start_time"] == "Unknown":
            continue

        session_number = session_soup.find("span", class_="abbreviation")
        session_number = session_number.string.replace(" - ", "")

        session_level = session_number[3:6]

        session_title = session_soup.find("span", class_="title")
        session_title = session_title.string.rstrip().replace( "\"", "'" )

        session_desc = session_soup.find( "span", class_="abstract")
        session_desc = session_desc.text.rstrip().replace( "\"", "'" ).replace( "\n", " " ).replace( " View More", "" )

        session_type = session_soup.find( "small", class_="type").string

        session_speakers = ""
        for child in session_soup.find( "small", class_="speakers").children:
            session_speakers += str(child)
        if session_speakers == None:
            session_speakers = ""
        else:
            session_speakers = session_speakers.strip().replace( "<br/>", ", ")
            if session_speakers.endswith(", "):
                session_speakers = session_speakers[:-2]

        session_abstract = session_soup.find("span", class_="abstract")

        session_interest = session_soup.find("a", class_="interested")
        
        if (session_interest == None):
            session_interest = False
        else:
            session_interest = True

        try:
            startDateStr = '{} 2018 {}'.format(session_timing['day'], session_timing['start_time']).strip()
            endDateStr = '{} 2018 {}'.format(session_timing['day'], session_timing['end_time']).strip()
            startDate = datetime.strptime(startDateStr, '%b %d %Y %I:%M %p')
            endDate = datetime.strptime(endDateStr, '%b %d %Y %I:%M %p')
            startTimeEpoch = startDate.timestamp()
            duration = (endDate - startDate).total_seconds() / 60.0
        except:
            print("[{}] - [{}]".format(startDateStr, endDateStr))
            raise

        if session_interest == True:
            interested = "Interested"
            eventKind = 0
        else:
            interested = "NotInterested"
            eventKind = 1

        item = {
            "title" : session_number,
            "desc" : session_title,
            "detail" : session_desc,
            "level" : session_level,
            "type" : session_type,
            "speakers" : session_speakers,
            "eventKind" : eventKind,
            "interested" : interested,
            "scheduledDate" : int(startTimeEpoch),
            "duration" : int(duration),
            "building" : session_timing['building'],
            "room" : session_timing['room'],
        }
        events.append( item )

        write_contents = "{},\"{}\",\"{}\",{},{},\"{}\",{},{},{},{},{},{}".format(session_number, session_title, session_desc, session_level, session_type, session_speakers, session_interest, session_timing['day'], session_timing['start_time'], session_timing['end_time'], session_timing['building'], session_timing['room'])
        file.write(write_contents.strip() + "\n")

        # Print the session title for each session written to the file
        #print (session_title.strip())

    file.close()


    if len(unableToGet) > 0:
        print( "------------")
        print( "Unable to get details for the following sessions:")
        for session in unableToGet:
            print( "     {}".format( session ) )


# If we are downloading from web, due to interesting session issues that affect the venue selection
# but not the day, kill the driver when changing venues and write all the data to disk


def main():
    # Create output folders if necessary
    if not os.path.isdir("./output"):
        os.makedirs( "./output" )

    # Remove and recreate the webdata folder if we are downloading data
    if downloadDataFromWeb == True:
        shutil.rmtree("./output/webdata")
        os.makedirs( "./output/webdata" )

    # Always remove csv output folder as we will always write data here
    if os.path.isdir("./output/csv/"):
        shutil.rmtree("./output/csv")
    os.makedirs( "./output/csv" )

    if os.path.exists("./output/sessions.csv"):
        os.remove("./output/sessions.csv")
    if os.path.exists("./output/sessions.json"):
        os.remove("./output/sessions.json")

    if downloadDataFromWeb == True:

        # Login to the reinvent website
        for venue in range(0, len(VENUE_CODES)):
            driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=CHROME_DRIVER)
            login(driver, USERNAME, PASSWORD)
            for day in range(0, len(DAY_IDS)):
                loadSessonContentsFromURL(driver, venue, day )
            driver.close() 

    loadSessonContentsFromFile()

    # create single sessions.csv file
    os.system("cat ./output/csv/*.csv >> ./output/sessions.csv")     

    # write out to sessions.json
    with open("./output/sessions.json", 'w') as outf:
        json.dump(events, outf)

if __name__ == "__main__":
    main()
