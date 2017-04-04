from urllib.request import urlopen
import re
import bs4

def getPageText(url):
    try:
        html = urlopen(url).read()
    except:
        return False
    source = bs4.BeautifulSoup(html)
    lines = source.findAll(text=True)
    return '\n'.join(list(filter(visible, lines))).encode('utf-8')

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True

print(getPageText("http://stackoverflow.com/questions/1936466/beautifulsoup-grab-visible-webpage-text"))
