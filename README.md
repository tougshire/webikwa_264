# webikwa_264

webikwa_264 is a configuration of Wagtail

## Important Note

This project is in development and there may be breaking changes until this note is removed

## Installation

webikwa_264 requires webikwa_templates_264 and touglates. If you're using a different template app than webikwa_templates_264, you can substitute that app

These instructions are written with the assumption that you're starting a new project

- create a new Wagtail project (see [Wagtail's instructions](https://docs.wagtail.org/en/v6.2.1/getting_started/) )
  - This will work if you stop after creating the superuser, but the rest of the tutorial covers features that might be useful 
- pip install [wagtail-markdown](https://pypi.org/project/wagtail-markdown/)
- pip install [nh3](https://pypi.org/project/nh3/)
- git clone [https://github.com/tougshire/touglates](https://github.com/tougshire/touglates)
- git clone [https://github.com/tougshire/webikwa_templates_264](https://github.com/tougshire/webikwa_templates_264)
- git clone [https://github.com/tougshire/webikwa_264](https://github.com/tougshire/webikwa_264)
- add the following to INSTALLED_APPS in settings/base.py:
  - "wagtail.contrib.settings",
  - "wagtailmarkdown",
  - "wagtail.contrib.table_block",
  - "touglates",
  - "webikwa_templates_264",
  - "webikwa_264",
- Add the following markdown setting to your base settings file:

    WAGTAILMARKDOWN = {
        "autodownload_fontawesome": True,
        "extensions": ['extra'],
    }

- run the migrations again
- run collectstatic

## Setting Up Tutorial

### Basic setup making use of a featured article page and a redirect page

- run the server and browse to the dashboard (http(s)://[your_url_or_ip]/admin/)
- rename the automatically-created page
  - in the dashboard, click "Pages", then the edit icon (a pencil) for the automatically created home page 
  - Add "-old" to the pages title
  - In the promote tab, add "-old" to to the slug.
  - publish the page
- create a redirect page and name it 'Home'
  - click the plus sign next to 'root'
  - click "Redirect page"
  - title the page 'Home'
  - publish the page
- make the new home page the site's root page
  - click 'Settings'
  - click 'Sites'
  - click 'localhost'
  - under "Root page", next to 'Home-old', click the three dots and "Choose a different page"
  - choose the new home page
  - save the changes
- create a new article index page
  - click 'Pages'
  - click 'Home' (click the title, not the edit icon)
  - using the "add child page" link next 'Home', create a new article index page
  - title it "Articles"
  - publish the page
- create a new placement page
  - using the 'add child page' link, create a new placement page
  - title it "Featured Articles"
  - click "Add Page Zone"
  - name the page zone "1".  You can leave the title blank
  - add four more page zones and name them "2","3","4", and "5" 
  - publish the page
- set the home page to redirect to the featured articles page
  - go to pages -> home, the click on the edit icon (a pencil)
  - click "choose a page"
  - click the angle bracket to the right of "Home", and click "Featured Articles"

### Adding featured articles

- Add articles 
  - Do the following at least five times
    - Click "Articles" in the sidebar
    - Click "+ Add Article"
    - Give the article a title, for example "Test Article 1"
    - Give the article a summary, for example "This is my first test article"
    - Click on body and add blocks to the body
      - Click the plus sign under "The body of the article"
        - If this is the first time through:
          - add a summary block
          - below the summary block, add a markdown block.  
          - In the markdown block, type:
              Here are some details about my first test article. 
        - For articles other than the first, experiment with different blocks
    - Place the article in the "Featured Articles" page
      - Click "Add Article Placement"
      - If this is the first article, place it in Featured Articles 1.  
      - Place other articles in other zones.  Use all zones and make some zones have more than one article
    - Publish the article

### Adding sidebar articles

- Show the left sidebar 
  - Click "Settings", the "Site Template Settings"
  - Check "Show Leftbar"
  - Save
- Create a sidebar page
  - Click "Pages" 
  - Click "Home"
  - Click the plus sign next to Home
  - Click "Sidebar Page"
  - Title the page "Left Sidebar"
  - For Location choose "Left"
  - Publish the page
- Create a sidebar article
  - Click "Sidebar Articles"
  - Click "Add sidebar article page"
  - Title it "Upcoming events"
  - Place the article in the sidebar
    - Click "Add a sidebar article placement"
    - For "Page" choose "Left Sidebar"
  - Click the plus sign under body and choose "Eventlist Block"
  - Add a date, time and description
  - Publish the event block
- Upon completion of the above steps, visit the website (http(s)://[your_url_or_ip]).  You should see the featured articles in the main windows and the even in the sidebar

