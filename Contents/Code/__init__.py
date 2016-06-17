######################################################################################
#
#	rawrANIME (BY TEHCRUCIBLE) - v0.06
#
######################################################################################

TITLE = "rawrANIME"
PREFIX = "/video/rawranime"
ART = "art-default.jpg"
ICON = "icon-default.png"
ICON_LIST = "icon-list.png"
ICON_COVER = "icon-cover.png"
ICON_SEARCH = "icon-search.png"
ICON_QUEUE = "icon-queue.png"
BASE_URL = "http://rawranime.tv"


######################################################################################
# Set global variables

def Start():

    ObjectContainer.title1 = TITLE
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON_COVER)
    DirectoryObject.art = R(ART)
    PopupDirectoryObject.thumb = R(ICON_COVER)
    PopupDirectoryObject.art = R(ART)
    VideoClipObject.thumb = R(ICON_COVER)
    VideoClipObject.art = R(ART)

    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'
    HTTP.Headers['Referer'] = 'http://rawranime.tv/'

######################################################################################
# Menu hierarchy

@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(LatestCategory, title="Latest Episodes"), title = "Latest Episodes", thumb = R(ICON_LIST)))
   # oc.add(DirectoryObject(key = Callback(ShowCategory, title="Most Popular", category = "/list/popular"), title = "Most Popular", thumb = R(ICON_LIST)))
    oc.add(DirectoryObject(key = Callback(ShowCategory, title="Top Rated", category = "r=1"), title = "Top Rated", thumb = R(ICON_LIST)))
    oc.add(DirectoryObject(key = Callback(ShowCategory, title="Ongoing Anime", category = "current"), title = "Ongoing Anime", thumb = R(ICON_LIST)))
    oc.add(DirectoryObject(key = Callback(Bookmarks, title="My Bookmarks"), title = "My Bookmarks", thumb = R(ICON_QUEUE)))
    oc.add(InputDirectoryObject(key=Callback(Search), title = "Search", prompt = "Search for anime?", thumb = R(ICON_SEARCH)))

    return oc


######################################################################################
# Loads bookmarked shows from Dict.  Titles are used as keys to store the show urls.

@route(PREFIX + "/bookmarks")
def Bookmarks(title):

    oc = ObjectContainer(title1 = title)

    for each in Dict:
        show_url = Dict[each]
        page_data = HTML.ElementFromURL(show_url)
        show_title = each
        show_thumb = "http://" + Regex('(?<=data-src="\/\/).*(?=">)').search(HTML.StringFromElement(page_data.xpath("//div[@id='anime-info-listimage']")[0])).group()
        show_summary = ""
        for p in page_data.xpath("//div[@id = 'anime-info-synopsis']/p"):
            show_summary = show_summary + "  " + p.xpath("./text()")[0]

        oc.add(DirectoryObject(
            key = Callback(PageEpisodes, show_title = show_title, show_url = show_url),
            title = show_title,
            thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
            summary = show_summary
            )
        )

    #add a way to clear bookmarks list
    oc.add(DirectoryObject(
        key = Callback(ClearBookmarks),
        title = "Clear Bookmarks",
        thumb = R(ICON_QUEUE),
        summary = "CAUTION! This will clear your entire bookmark list!"
        )
    )

    return oc

######################################################################################
# Takes query and sets up a http request to return and create objects from results

@route(PREFIX + "/search")
def Search(query):

    oc = ObjectContainer(title1 = query)

    #do http request for search data

    page_data = HTML.ElementFromString(JSON.ObjectFromURL(BASE_URL + '/index.php?ajax=anime&do=getlist&rs=0&as=' + query, cacheTime = CACHE_1MINUTE)['html'])
    if not HTML.StringFromElement(page_data).startswith("<div"):
        page_data = HTML.ElementFromString("<div>" + HTML.StringFromElement(page_data) + "</div>")
    for each in page_data:

        show_url = BASE_URL + each.get('href')
        show_title = each.xpath("./div[@class='al-name']/text()")[0].strip()
        show_thumb = "http://" + each.xpath("./div[@class='al-image']/@data-src")[0].split('//')[1]
        #show_summary = each.xpath(".//h4/text()")[0]

        oc.add(DirectoryObject(
            key = Callback(PageEpisodes, show_title = show_title, show_url = show_url),
            title = show_title,
            thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png')#,
         #   summary = show_summary
            )
        )

    #check for zero results and display error
    if len(oc) < 1:
        Log ("No shows found! Check search query.")
        return ObjectContainer(header="Error", message="Nothing found! Try something less specific.")

    return oc

######################################################################################
# Creates latest episode objects from the front page

@route(PREFIX + "/latestcategory")
def LatestCategory(title):

    oc = ObjectContainer(title1 = title)
    page_data = HTML.ElementFromURL(BASE_URL + "/recent", cacheTime = CACHE_1MINUTE)

    for each in page_data.xpath("//div[@class='ep '] | //div[@class='ep backlog']"):

        ep_url = BASE_URL + each.xpath("./a")[0].get('href')
        ep_title = each.xpath("./div[@class='ep-info']/a/text()")[1]
        style_string = HTML.StringFromElement(each.xpath("./a[@class='ep-bg']")[0])
        img_url = Regex('(?<=data-src="\/\/).*(?=" href)').search(style_string)
        if img_url:
            ep_thumb = "http://" + img_url.group()

        oc.add(PopupDirectoryObject(
            key = Callback(GetMirrors, ep_url = ep_url),
            title = ep_title,
            thumb = ep_thumb
            )
        )

    #check for results and display an error if none
    if len(oc) < 1:
        Log ("No shows found! Check xpath queries.")
        return ObjectContainer(header="Error", message="Error! Please let TehCrucible know, at the Plex forums.")

    return oc


######################################################################################
# Creates page url from category and creates objects from that page

@route(PREFIX + "/showcategory")
def ShowCategory(title, category):

    oc = ObjectContainer(title1 = title)
    page_data = HTML.ElementFromString(JSON.ObjectFromURL(BASE_URL + "/index.php?ajax=anime&do=getlist&rs=0&" + (category if (category == "r=1") else HTML.ElementFromURL(BASE_URL).xpath("//a[@class='navlink animelist-link']")[1].get('href')))['html']) 

    if not HTML.StringFromElement(page_data).startswith("<div"):
        page_data = HTML.ElementFromString("<div>" + HTML.StringFromElement(page_data) + "</div>")
    for i in range(0,len(page_data) if ((len(page_data) - ( len(page_data) % 200)) == 0) else 200):
        each = page_data[i]
        show_url = BASE_URL + each.get('href')
        show_title = each.xpath("./div[@class='al-name']/text()")[0].strip()
        show_thumb = "http://" + each.xpath("./div[@class='al-image']/@data-src")[0].split('//')[1]

        oc.add(DirectoryObject(
            key = Callback(PageEpisodes, show_title = show_title, show_url = show_url),
            title = show_title,
            thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png')#,
         #   summary = show_summary
            )
        )

    return oc


######################################################################################
# Creates an object for every 30 episodes (or part thereof) from a show url

@route(PREFIX + "/pageepisodes")
def PageEpisodes(show_title, show_url):

    oc = ObjectContainer(title1 = show_title)
    page_data = HTML.ElementFromURL(show_url)
    show_thumb = "http://" + Regex('(?<=data-src="\/\/).*(?=">)').search(HTML.StringFromElement(page_data.xpath("//div[@id='anime-info-listimage']")[0])).group()
    #show_ep_count = int(page_data.xpath("//div[@class='anime-info-data-info']/text()")[0].split()[0])
    show_summary = ""
    for p in page_data.xpath("//div[@id = 'anime-info-synopsis']/p"):
        show_summary = show_summary + "  " + p.xpath("./text()")[0]
    eps_list = page_data.xpath("//div[@class='ep-list']/div[contains(@class, 'ep ')]")
    show_ep_count = len(eps_list)
    #set a start point and determine how many objects we will need
    offset = 0
    rotation = (show_ep_count - (show_ep_count % 30)) / 30

    #add a directory object for every 30 episodes
    while rotation > 0:

        start_ep  = offset
        end_ep = offset + 30
        start_ep_title = eps_list[(start_ep)].xpath(".//div[@class='ep-number']/text()")[0] + ' ' + eps_list[(start_ep)].xpath(".//div[@class='ep-info']/div[@class='ep-title']/text()")[1].strip()
        end_ep_title = eps_list[(end_ep - 1)].xpath(".//div[@class='ep-number']/text()")[0] + ' ' + eps_list[(end_ep - 1)].xpath(".//div[@class='ep-info']/div[@class='ep-title']/text()")[1].strip()

        oc.add(DirectoryObject(
            key = Callback(ListEpisodes, show_title = show_title, show_url = show_url, start_ep = start_ep, end_ep = end_ep),
            title = "Episodes " + start_ep_title + " - " + end_ep_title,
            thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
            summary = show_summary
            )
        )

        offset += 30
        rotation = rotation - 1

    #if total eps is divisible by 30, add bookmark link and return
    if (show_ep_count % 30) == 0:

        #provide a way to add or remove from favourites list
        oc.add(DirectoryObject(
            key = Callback(AddBookmark, show_title = show_title, show_url = show_url),
            title = "Add Bookmark",
            summary = "You can add " + show_title + " to your Bookmarks list, to make it easier to find later.",
            thumb = R(ICON_QUEUE)
            )
        )
        return oc

    #else create directory object for remaining eps
    else:

        start_ep = offset
        end_ep = (offset + (show_ep_count % 30))

        start_ep_title = eps_list[(start_ep)].xpath(".//div[@class='ep-number']/text()")[0] + ' ' + eps_list[(start_ep)].xpath(".//div[@class='ep-info']/div[@class='ep-title']/text()")[1].strip()
        end_ep_title = eps_list[(end_ep - 1)].xpath(".//div[@class='ep-number']/text()")[0] + ' ' + eps_list[(end_ep - 1)].xpath(".//div[@class='ep-info']/div[@class='ep-title']/text()")[1].strip()

        oc.add(DirectoryObject(
            key = Callback(ListEpisodes, show_title = show_title, show_url = show_url, start_ep = offset, end_ep = offset + (show_ep_count % 30)),
            title = "Episodes " + start_ep_title + " - " + end_ep_title,
            thumb = Resource.ContentsOfURLWithFallback(url = show_thumb, fallback='icon-cover.png'),
            summary = show_summary
            )
        )

        #provide a way to add or remove from favourites list
        oc.add(DirectoryObject(
            key = Callback(AddBookmark, show_title = show_title, show_url = show_url),
            title = "Add Bookmark",
            summary = "You can add " + show_title + " to your Bookmarks list, to make it easier to find later.",
            thumb = R(ICON_QUEUE)
            )
        )
        return oc

######################################################################################
# Returns a list of VideoClipObjects for the episodes with a specified range

@route(PREFIX + "/listepisodes")
def ListEpisodes(show_title, show_url, start_ep, end_ep):

    oc = ObjectContainer(title1 = show_title)
    page_data = HTML.ElementFromURL(show_url)
    eps_list = page_data.xpath("//div[@class='ep-list']/div[contains(@class, 'ep ')]")

    for each in eps_list[int(start_ep):int(end_ep)]:
        ep_url = BASE_URL + each.xpath(".//a/@href")[0]
        ep_title = "Episode " + each.xpath(".//div[@class='ep-number']/text()")[0] + ' ' + each.xpath(".//div[@class='ep-info']/div[@class='ep-title']/text()")[1].strip()

        oc.add(PopupDirectoryObject(
            key = Callback(GetMirrors, ep_url = ep_url),
            title = ep_title,
            thumb = R(ICON_COVER)
            )
        )

    return oc

######################################################################################
# Returns a list of VideoClipObjects for each mirror, with video_id tagged to ep_url

@route(PREFIX + "/getmirrors")
def GetMirrors(ep_url):

    mirrors = {'stream.moe': '18', 'mp4upload': '2', 'videonest': '12', 'openload': '19', 'yourupload':'14'}

    oc = ObjectContainer()
    page_data = HTML.ElementFromURL(ep_url)

    show_data = HTML.ElementFromURL(BASE_URL + page_data.xpath("//a[@id='video-anime']/@href")[0])
    show_art = "http://" + Regex('(?<=data-src="\/\/).*(?=">)').search(HTML.StringFromElement(show_data.xpath("//div[@id='parallax-background']")[0])).group().split('"')[0]
    if len(show_data.xpath("//div[@class = 'listblur']")) > 0 :
        show_art = ""

    for each in page_data.xpath("//div[@id='mirrors']/div[@class= 'scroller-inner']/div[contains(@class, 'mirror')]"):
        video_type = each.xpath("./div[@class='mirror-lang']/text()")[0]
        video_quality = each.xpath("./div[@class='mirror-quality']/text()")[0]
        video_host = each.xpath("./div[@class='mirror-text']/div[@class='mirror-provider']/text()")[0]
        video_title = video_type + " " + video_quality + " " + video_host
        video_url = ep_url.split('?q=')[0] + '?q=' + video_quality + '&l=' +  video_type.lower() + '&p=' + mirrors[video_host] 

        if video_host in mirrors and video_host != "stream.moe" and video_host != "yourupload":
            oc.add(VideoClipObject(
                url = video_url,
                title = video_title,
                thumb = R(ICON_COVER) 
                )
            )

    return oc


######################################################################################
# Get episode thumbnails from the ep_url

@route(PREFIX + "/getthumb")
def GetThumb(video_thumb):

    try:
        data = HTTP.Request(video_thumb, cacheTime=CACHE_1MONTH).content
        return DataObject(data, 'image/jpg')
    except:
        return Redirect(R(ICON_COVER))

######################################################################################
# Adds a show to the bookmarks list using the title as a key for the url

@route(PREFIX + "/addbookmark")
def AddBookmark(show_title, show_url):

    Dict[show_title] = show_url
    Dict.Save()
    return ObjectContainer(header=show_title, message='This show has been added to your bookmarks.')

######################################################################################
# Clears the Dict that stores the bookmarks list

@route(PREFIX + "/clearbookmarks")
def ClearBookmarks():

    Dict.Reset()
    return ObjectContainer(header="My Bookmarks", message='Your bookmark list has been cleared.')
