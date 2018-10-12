# AWS re:Invent 2018 Schedule Extract Tool

Modified to work with the 2018 schedule
Original codebase  - https://github.com/mda590/reinvent_schedule_extract

-------------------------------------

This tool is meant to make it super easy to export your re:invent schedule into a text file and then import it into whatever tool makes it easier for you to work with.

This tool is given without warranty and probably little maintenance. I whipped it up over the weekend to try to solve my problems (explained below) and thought I would share.

For some reason, when looking at the total # of sessions on the re:Invent Session Catalog, that number is higher than if you look at the totals for each day in the catalog. I have not spent much time investigating why there is this discrepancy.

I didn't see anything in the re:Invent TOS regarding scraping schedule content. If I missed something, I'm happy to remove the tool.

## TL;DR How to use the tool:
1. Rename config.py.dist to config.py and in that file, update your event website credentials in the USERNAME and PASSWORD vars. These are the credentials you use when logging in on this page: https://www.portal.reinvent.awsevents.com/connect/login.ww. 
2. Download the Chrome web driver for your OS (https://sites.google.com/a/chromium.org/chromedriver/downloads).
3. Change the CHROME_DRIVER var to point to the driver location.
4. Run the file in Python. Assuming all goes well, you should end up with a output/sessions.csv, comma delimited text file, and a output/sessions.json file containing all of the re:Invent sessions. You should also geta field that shows if you have marked this as interested.
5. The sessions.csv file can be imported into Excel, etc, and the sessions.json file can be used in the Mac Viewer app (coming soon)

## Why did I make this?
I needed a way to visualise 2000+ sessions on a timeline rather than a long list, reduce the clutter and pick what I want to watch.  Unfortunately the re:Invent website doesn't yet allow this.

Fortunately, Matt Adorjan did a lot of work in creating the main script last year and this is based off this.
