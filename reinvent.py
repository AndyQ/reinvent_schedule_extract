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
from time import sleep
from bs4 import BeautifulSoup
import re

from config import USERNAME, PASSWORD

# Set to True to download the data from the web OR False to use a pre-downloaded set of data
# useful if you want to change the parsed datasets
downloadDataFromWeb = False

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
            sleep(3)
        except NoSuchElementException as e:
            more_results = False

    # Go through all the links and expand the scheduling options
    # this loads the schedule times (and means we don't need to mess with the AJAX call which
    # requires sessions and stuff)
    sessions = driver.find_element_by_id('searchResult')
    sessionTimes = sessions.find_elements_by_xpath( "//*[contains(@onclick,'showAvailSessions')]")
    print( "Expanding {} sessions".format(len(sessionTimes)))
    for link in sessionTimes:
        link.click()
        sleep(0.250)

    # write to <venueid>.txt
    with open( "{}_{}.txt".format(VENUE_NAMES[venue], DAY_NAMES[day]), "w") as out:
        out.write( driver.page_source )


def loadSessonContentsFromFile( ):
    global content_to_parse
    # Getting content by day, instead of the entire set, because sometimes the
    # Get More Results link stops working on the full list. Haven't had issues
    # looking at the lists day by day.
    for venue in range(0, len(VENUE_CODES)):
        for day in range(0, len(DAY_IDS)):
            with open( "{}_{}.txt".format(VENUE_NAMES[venue], DAY_NAMES[day]), "r") as input:
                data = input.read()
                extractSessionsFromHTML( data, "sessions_{}_{}.txt".format(VENUE_NAMES[venue], DAY_NAMES[day]) )
                #content_to_parse = content_to_parse + data


def extractSessionsFromHTML( html, outputFile ):
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

    print( "Found {} sessions".format(len(sessions)))

    # Open a blank text file to write sessions to
    file = open(outputFile,"w")

    # Create a header row for the file. Note the PIPE (|) DELIMITER.
    file.write("Session Number,Session Title,Session Level,Session Type,Session Speakers,Session Interest,Day,Start Time,End Time,Building,Room\n")

    # For each session, pull out the relevant fields and write them to the sessions.txt file.
    unableToGet = []
    for session in sessions:
        session_soup = BeautifulSoup(str(session), "html.parser")
        session_id = session_soup.find("div", class_="sessionRow")
        session_id = session_id['id']
        session_id = session_id[session_id.find("_")+1:]

        # Grab the schedule timings
        text = session_soup.find( "ul", class_="availableSessions").text
        text = text[37:]
        #print( "{} - [{}]".format( session_id, text ) )

        match = re.search("([^,]*), ([^,]*), ([^-]*)- ([^-–]*). ([^,]*), ([^,]*), (.*)", text, re.DOTALL | re.MULTILINE)
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
                "start_time": groups[2],
                "end_time": groups[3],
                "building": groups[4],
                "room": "{} - {}".format(groups[5], groups[6].replace( ",", " - ")),
                "day": "{}".format(groups[1])
            }

        session_number = session_soup.find("span", class_="abbreviation")
        session_number = session_number.string.replace(" - ", "")

        session_level = session_number[3:6]

        session_title = session_soup.find("span", class_="title")
        session_title = session_title.string.rstrip().replace( "\"", "'" )

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

        write_contents = "{},\"{}\",{},{},\"{}\",{},{},{},{},{},{}".format(session_number, session_title, session_level, session_type, session_speakers, session_interest, session_timing['day'], session_timing['start_time'], session_timing['end_time'], session_timing['building'], session_timing['room'])
        file.write(write_contents.strip() + "\n")

        # Print the session title for each session written to the file
        #print (session_title.strip())

    file.close()

    print( "------------")
    print( "Unable to get details for the following sessions:")
    for session in unableToGet:
        print( "     {}".format( session ) )


# If we are downloading from web, due to interesting session issues that affect the venue selection
# but not the day, kill the driver when changing venues and write all the data to disk

if downloadDataFromWeb == True:

    # Login to the reinvent website
    for venue in range(0, len(VENUE_CODES):
        driver = webdriver.Chrome(chrome_options=chrome_options, executable_path=CHROME_DRIVER)
        login(driver, USERNAME, PASSWORD)
        for day in range(0, len(DAY_IDS)):
            loadSessonContentsFromURL(driver, venue, day )
        driver.close() 

loadSessonContentsFromFile()

