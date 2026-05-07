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
  - Add "-old" to the pages title (If the title of the page is "Home", change the title to "Home-Old").
    In the promote tab, add "-old" to to the slug.
  - publish the page
- create a new article index page
  - using the "add child page" action next to the word "Root", create a new article index page
  - title it "Articles"
  - publish the page
- create a new placement page
  - from the root page, create a new placement page
  - title it "Featured Articles"
  - publish the page
- create a new redirect page
  - from root, create a new redirect page
  - title it "Home"
  - for the target page, choose the featured articles page
  - publish the page
- move the featured articles page and the articles index page under the home page
  - from the page list under root, check the checkboxes next to Featured Articles and Articles
  - click the "move" button
  - click "Choose a page"
  - choose Home
  - Click "Yes, move these pages"
- make Home the root page for the default site
  - click "Settings" then "Sites"
  - choose the default site (probably the only site, "localhost")
  - change the root page from the old home page to the new home page (which is the redirect page)
  - save the change

### Adding featured articles

- Add articles 
  - Do the following several times
    - Click "Articles" in the sidebar
    - Click "+ Add Article"
    - Give the article a title, for example "Test Article 1"
    - Place the article in the "Featured Articles" page
      - Click "Add Article Placement"
      - Under "Page", choose "Featured Articles" 
    - Add some text in the summary section
    - Add some content to the body
      - Click the plus sign under "The body of the article"
      - Click "Markdown Block"
      - Add some markdown
      - Experiment with other types of blocks as desired, 
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

