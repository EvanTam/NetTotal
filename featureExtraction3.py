import string
from socket import timeout
from bs4 import BeautifulSoup
from nltk import pos_tag
from nltk import word_tokenize
from nltk.chunk import ne_chunk
from nltk.corpus.reader.wordnet import Synset
from nltk.stem.lancaster import LancasterStemmer
from nltk.tree import Tree
from nltk.wsd import lesk
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen

def extractFeature(max_result, query):
    lancaster = LancasterStemmer()
    stemmed_query = stemTokens(lancaster, query.split(' '))

    index_to_synset = []
    noun_to_synset_index = dict()
    verb_to_synset_index = dict()
    subsumer_cache = dict()

    google_result = googleSearch(max_result, query)
#    google_result = dict([("http://www.ipdb.org/machine.cgi%3Fid%3D195", "Internet Pinball Machine Database: Data East &#39;<b>Batman</b>&#39;"), ("http://www.batmanlive.com/", "<b>Batman</b> Live"), ("http://www.comingsoon.net/movie/batman-v-superman-dawn-of-justice-2016", "<b>Batman</b> v Superman: Dawn of Justice - ComingSoon.net"), ("https://www.fanfiction.net/comic/Batman/", "<b>Batman</b> FanFiction Archive | FanFiction"), ("http://www.cinemablend.com/new/Batman-v-Superman-What-We-Know-So-Far-About-Dawn-Justice-38745.html", "<b>Batman</b> v Superman: What We Know So Far About Dawn Of Justice <b>...</b>"), ("https://www.sixflags.com/magicmountain/attractions/batman-ride", "<b>BATMAN</b> The Ride | Six Flags Magic Mountain"), ("https://store.usps.com/store/browse/productDetailSingleSku.jsp%3FproductId%3DS_588404", "<b>Batman</b> stamps - The Postal Store - USPS.com"), ("http://www.ign.com/articles/2015/04/20/new-batman-v-superman-imax-posters", "New <b>Batman</b> v Superman IMAX Posters - IGN"), ("http://www.imdb.com/title/tt0059968/", "<b>Batman</b> (TV Series 1966–1968) - IMDb"), ("https://xkcd.com/1004/", "xkcd: <b>Batman</b>"), ("http://www.batmanvsupermandawnofjustice.com/", "<b>BATMAN</b> v SUPERMAN: DAWN OF JUSTICE - Official Movie Site"), ("http://www.coverbrowser.com/covers/batman", "<b>Batman</b> Covers"), ("http://www.youtube.com/watch%3Fv%3DIwfUnkBfdZ4", "<b>Batman</b> v Superman: Dawn of Justice - Official Teaser Trailer [HD <b>...</b>"), ("http://www.esrb.org/ratings/synopsis.jsp%3FCertificate%3D33870%26Title", "<b>Batman</b>: Arkham Knight - ESRB"), ("http://screenrant.com/tag/batman-vs-superman/", "<b>Batman</b> V Superman: Dawn of Justice (2016) - Screen Rant"), ("http://batman-news.com/", "<b>Batman</b>-News.com - <b>Batman</b> v Superman: Dawn of Justice News <b>...</b>"), ("http://batman.wikia.com/", "<b>Batman</b> Wiki"), ("http://dc.wikia.com/wiki/Batman", "<b>Batman</b> - DC Comics Database"), ("https://www.batmanarkhamorigins.com/", "<b>Batman</b>: Arkham Origins -- In stores October 25th"), ("http://www.gamespot.com/batman-arkham-knight/", "<b>Batman</b>: Arkham Knight - GameSpot"), ("http://mashable.com/2015/04/20/batman-vs-superman-posters/", "Official &#39;<b>Batman</b> v Superman&#39; posters are pretty damn awesome"), ("http://www.batman-on-film.com/jettsmainpage.html", "BOF&#39;s main page - <b>Batman</b> On Film"), ("http://www.arkhamunderworld.com/", "<b>Batman</b>: Arkham Underworld: Home"), ("http://www.rottentomatoes.com/m/batman_the_movie/", "<b>Batman</b>: The Movie - Rotten Tomatoes"), ("http://www.boxofficemojo.com/franchises/chart/%3Fid%3Dbatman.htm", "<b>Batman</b> Moviesat the Box Office - Box Office Mojo"), ("http://vipstudiotour.warnerbros.com/the-batman-tour/", "The <b>Batman</b> Exhibit - Warner Bros. VIP Studio Tour"), ("http://www.lego.com/en-us/dccomicssuperheroes/games/batman-41737f39a61649c48e796268da665115", "<b>Batman</b> - Games - DC Comics Super Heroes LEGO.com"), ("http://www.cnet.com/news/batman-v-superman-goes-retro-with-adam-west-christopher-reeve/", "&#39;<b>Batman</b> v Superman&#39; goes retro with Adam West, Christopher <b>...</b>"), ("https://www.facebook.com/batman", "<b>Batman</b> | Facebook"), ("http://www.superherohype.com/heroes/batman", "<b>Batman</b> - SuperHeroHype"), ("http://www.kidsembrace.com/batman-car-seat.html", "Official <b>Batman</b> Toddler Baby Car Seat &amp; Booster by KidsEmbrace"), ("http://www.forbes.com/sites/scottmendelson/2015/04/17/batman-v-superman-trailer-casts-the-dark-knight-as-the-dark-sequel-villain/", "&#39;<b>Batman</b> V Superman&#39; Trailer Casts The Dark Knight As The <b>...</b> - Forbes"), ("http://www.theverge.com/2015/4/17/8439837/batman-v-superman-trailer-leak", "The first <b>Batman</b> v. Superman trailer has been officially released <b>...</b>"), ("https://www.batmanarkhamknight.com/", "<b>Batman</b>: Arkham Knight - Coming 06.23.15"), ("http://www.comicvine.com/batman/4005-1699/", "<b>Batman</b> (Character) - Comic Vine"), ("http://knowyourmeme.com/memes/my-parents-are-dead-batman-slapping-robin", "My Parents Are Dead / <b>Batman</b> Slapping Robin | Know Your Meme"), ("http://www.reddit.com/r/batman/", "The <b>Batman</b> subreddit"), ("http://io9.com/tag/batman", "<b>Batman</b> News, Videos, Reviews and Gossip - io9"), ("http://en.wikipedia.org/wiki/Batman", "<b>Batman</b> - Wikipedia, the free encyclopedia"), ("http://www.cnn.com/2015/04/17/entertainment/batman-v-superman-trailer-released/", "&#39;<b>Batman</b> v Superman&#39; Trailer Officially Released - CNN.com"), ("https://twitter.com/batmanarkham", "<b>Batman</b> Arkham (@BatmanArkham) | Twitter"), ("http://www.minecraftskins.net/batman", "<b>Batman</b> | Minecraft Skins"), ("http://theoatmeal.com/comics/realistic_batman", "Realistic <b>Batman</b> - The Oatmeal"), ("http://www.cartoonnetwork.com/games/batmanbb/index.html", "<b>Batman</b>: The Brave and the Bold Games | Play Free Online Games <b>...</b>"), ("http://batman.wikia.com/wiki/Batman", "Bruce Wayne - <b>Batman</b> - <b>Batman</b> Wiki - Wikia"), ("http://www.collegehumor.com/badman", "<b>Batman</b> Videos on Collegehumor"), ("http://www.bundlestars.com/all-bundles/batman-complete-bundle/", "<b>Batman</b> Complete Bundle - Bundle Stars"), ("http://ualuealuealeuale.ytmnd.com/", "ualuealuealeuale: YTMND - <b>Batman</b>"), ("http://batmanjs.org/", "<b>batman</b>.js — overview"), ("http://www.tv.com/shows/batman-adam-west/", "<b>Batman</b> - TV.com"), ("http://mondotees.com/products/batman-the-animated-series-die-cut-12-single", "<b>Batman</b>: The Animated Series Die-Cut 12&quot; Single – Mondo"), ("http://www.vox.com/2015/4/16/8438743/batman-superman-dawn-of-justice-trailer", "Here&#39;s the official <b>Batman</b> v. Superman: Dawn of Justice trailer - Vox"), ("https://www.sideshowtoy.com/collectibles/dc-comics-batman-sideshow-collectibles-300131/", "<b>Batman</b> Premium Format™ Figure - Sideshow Collectibles"), ("http://www.imdb.com/title/tt0096895/", "<b>Batman</b> (1989) - IMDb"), ("http://store.steampowered.com/app/208650/", "Pre-purchase <b>Batman</b>: Arkham Knight on Steam"), ("http://www.open-mesh.org/", "WikiStart - Open-mesh - Open Mesh"), ("http://www.denofgeek.us/movies/batman-v-superman-dawn-of-justice/178441/batman-v-superman-dawn-of-justice-everything-you-need-to-know", "<b>Batman</b> v. Superman: Dawn of Justice - Everything You Need to Know"), ("http://www.dccomics.com/characters/batman", "<b>Batman</b> | DC Comics"), ("http://www.worldofspectrum.org/infoseekid.cgi%3Fid%3D0000438", "<b>Batman</b> - World of Spectrum"), ("http://community.wbgames.com/t5/Batman-Arkham/ct-p/Batman", "<b>Batman</b>: Arkham - WB Games"), ("http://www.amazon.com/Batman-Complete-Television-Limited-Edition/dp/B00LT1JHLW", "Amazon.com: <b>Batman</b>: The Complete Television Series (Limited <b>...</b>"), ("http://www.entertainmentearth.com/hitlist.asp%3Ftheme%3Dbatman", "<b>Batman</b> - Entertainment Earth"), ("http://www.wbshop.com/category/wbshop_brands/batman.do", "<b>Batman</b> | WBshop.com"), ("http://www.wired.com/2015/04/batman-v-superman-trailer-2/", "Oh, Hey, There&#39;s That <b>Batman</b> v Superman Trailer We&#39;ve Been <b>...</b>")])
#    google_result = dict([("http://www.ipdb.org/machine.cgi%3Fid%3D195", []), ("http://www.batmanlive.com/", []), ("http://www.comingsoon.net/movie/batman-v-superman-dawn-of-justice-2016", []), ("https://www.fanfiction.net/comic/Batman/", []), ("http://www.cinemablend.com/new/Batman-v-Superman-What-We-Know-So-Far-About-Dawn-Justice-38745.html", []), ("https://www.sixflags.com/magicmountain/attractions/batman-ride", []), ("https://store.usps.com/store/browse/productDetailSingleSku.jsp%3FproductId%3DS_588404", []), ("http://www.ign.com/articles/2015/04/20/new-batman-v-superman-imax-posters", []), ("http://www.imdb.com/title/tt0059968/", []), ("https://xkcd.com/1004/", []), ("http://www.batmanvsupermandawnofjustice.com/", []), ("http://www.coverbrowser.com/covers/batman", []), ("http://www.youtube.com/watch%3Fv%3DIwfUnkBfdZ4", []), ("http://www.esrb.org/ratings/synopsis.jsp%3FCertificate%3D33870%26Title", []), ("http://screenrant.com/tag/batman-vs-superman/", []), ("http://batman-news.com/", []), ("http://batman.wikia.com/", []), ("http://dc.wikia.com/wiki/Batman", []), ("https://www.batmanarkhamorigins.com/", []), ("http://www.gamespot.com/batman-arkham-knight/", []), ("http://mashable.com/2015/04/20/batman-vs-superman-posters/", []), ("http://www.batman-on-film.com/jettsmainpage.html", []), ("http://www.arkhamunderworld.com/", []), ("http://www.rottentomatoes.com/m/batman_the_movie/", []), ("http://www.boxofficemojo.com/franchises/chart/%3Fid%3Dbatman.htm", []), ("http://vipstudiotour.warnerbros.com/the-batman-tour/", []), ("http://www.lego.com/en-us/dccomicssuperheroes/games/batman-41737f39a61649c48e796268da665115", []), ("http://www.cnet.com/news/batman-v-superman-goes-retro-with-adam-west-christopher-reeve/", []), ("https://www.facebook.com/batman", []), ("http://www.superherohype.com/heroes/batman", []), ("http://www.kidsembrace.com/batman-car-seat.html", []), ("http://www.forbes.com/sites/scottmendelson/2015/04/17/batman-v-superman-trailer-casts-the-dark-knight-as-the-dark-sequel-villain/", []), ("http://www.theverge.com/2015/4/17/8439837/batman-v-superman-trailer-leak", []), ("https://www.batmanarkhamknight.com/", []), ("http://www.comicvine.com/batman/4005-1699/", []), ("http://knowyourmeme.com/memes/my-parents-are-dead-batman-slapping-robin", []), ("http://www.reddit.com/r/batman/", []), ("http://io9.com/tag/batman", []), ("http://en.wikipedia.org/wiki/Batman", []), ("http://www.cnn.com/2015/04/17/entertainment/batman-v-superman-trailer-released/", []), ("https://twitter.com/batmanarkham", []), ("http://www.minecraftskins.net/batman", []), ("http://theoatmeal.com/comics/realistic_batman", []), ("http://www.cartoonnetwork.com/games/batmanbb/index.html", []), ("http://batman.wikia.com/wiki/Batman", []), ("http://www.collegehumor.com/badman", []), ("http://www.bundlestars.com/all-bundles/batman-complete-bundle/", []), ("http://ualuealuealeuale.ytmnd.com/", []), ("http://batmanjs.org/", []), ("http://www.tv.com/shows/batman-adam-west/", []), ("http://mondotees.com/products/batman-the-animated-series-die-cut-12-single", []), ("http://www.vox.com/2015/4/16/8438743/batman-superman-dawn-of-justice-trailer", []), ("https://www.sideshowtoy.com/collectibles/dc-comics-batman-sideshow-collectibles-300131/", []), ("http://www.imdb.com/title/tt0096895/", []), ("http://store.steampowered.com/app/208650/", []), ("http://www.open-mesh.org/", []), ("http://www.denofgeek.us/movies/batman-v-superman-dawn-of-justice/178441/batman-v-superman-dawn-of-justice-everything-you-need-to-know", []), ("http://www.dccomics.com/characters/batman", []), ("http://www.worldofspectrum.org/infoseekid.cgi%3Fid%3D0000438", []), ("http://community.wbgames.com/t5/Batman-Arkham/ct-p/Batman", []), ("http://www.amazon.com/Batman-Complete-Television-Limited-Edition/dp/B00LT1JHLW", []), ("http://www.entertainmentearth.com/hitlist.asp%3Ftheme%3Dbatman", []), ("http://www.wbshop.com/category/wbshop_brands/batman.do", []), ("http://www.wired.com/2015/04/batman-v-superman-trailer-2/", [])])
    todo_list = list(google_result.keys())
    counter = 0
    changed = True
    while todo_list and changed and counter < max_result:
        changed = False
        for url in todo_list[:]:
            if counter >= max_result:
                break
            if successfulUpdate(lancaster, stemmed_query, google_result, url, index_to_synset, noun_to_synset_index, verb_to_synset_index, subsumer_cache):
                todo_list.remove(url)
                changed = True
                counter += 1
                print(counter)

    for todo in todo_list:
        del google_result[todo]

    return (google_result, index_to_synset)

def successfulUpdate(lancaster, stemmed_query, url, index_to_synset, noun_to_synset_index, verb_to_synset_index, subsumer_cache):
    try:
        text = getPageText(url)
        tokens = word_tokenize(text)
        pos = sentencePOS(lancaster, stemmed_query, tokens)

        noun_to_verb = dict()
        verb_to_noun = dict()
        for p in pos:
            updateDictionary(p, index_to_synset, noun_to_synset_index, verb_to_synset_index, noun_to_verb, verb_to_noun)
        (noun_arc, verb_arc) = generateNounVerbArc(index_to_synset, subsumer_cache, noun_to_verb, verb_to_noun)
        return noun_arc.union(verb_arc)
    except (HTTPError, URLError, timeout):
        return False

def getPageText(url):
    html = urlopen(url).read()
    source = BeautifulSoup(html)
    lines = source.get_text().split('\n')
    lines = list(filter(lambda line: sum([c in string.whitespace for c in line]) > sum([c in string.punctuation for c in line]), lines))
    return '\n'.join(lines)

def sentencePOS(lancaster, stemmed_query, tokens):
    sentence = []
    sentences = []
    sentence_query_overlap = []
    for token in tokens:
        sentence.append(token)
        if isEndOfSentence(token):
            stemmed_sentence = stemTokens(lancaster, sentence)
            if len(stemmed_sentence.intersection(stemmed_query)) > 0:
                sentences.append(nameEntityPOS(sentence))
            sentence = []
    return sentences

def stemTokens(lancaster, tokens):
    temp = []
    for word in tokens:
        if not isStopWord(word) and not isPunctuation(word):
            temp.append(lancaster.stem(word))
    return set(temp)
    
def nameEntityPOS(sentence):
    pos = pos_tag(sentence)
    entity = ne_chunk(pos, binary=True)
    result = [('_'.join([l[0] for l in e.leaves()]), e.label()) if isinstance(e, Tree) else e for e in entity]
    return list(filter(lambda r: not isPunctuation(r[0]), result))

def updateDictionary(pos, index_to_synset, noun_to_synset_index, verb_to_synset_index, noun_to_verb, verb_to_noun):
#    name_entity = [n[0] for n in set(filter(lambda t: 'NE' in t[1], pos))]
    noun = [n[0] for n in set(filter(lambda t: 'NN' in t[1], pos))]
    verb = [v[0] for v in set(filter(lambda t: 'VB' in t[1], pos))]
    tokens = noun + verb
    if (len(noun) > 0) and (len(verb) > 0):
        noun_synset = []
        verb_synset = []
        
        for n in noun:
            if (n not in noun_to_synset_index):
                meaning = lesk(tokens, n, 'n')
                if meaning is None:
                    continue
                else:
                    if meaning in index_to_synset:
                        noun_to_synset_index[n] = index_to_synset.index(meaning)
                    else:
                        noun_to_synset_index[n] = len(index_to_synset)
                        index_to_synset.append(meaning)
            noun_synset.append(noun_to_synset_index[n])
        for v in verb:
            if (v not in verb_to_synset_index):
                meaning = lesk(tokens, v, 'v')
                if meaning is None:
                    continue
                else:
                    if meaning in index_to_synset:
                        verb_to_synset_index[v] = index_to_synset.index(meaning)
                    else:
                        verb_to_synset_index[v] = len(index_to_synset)
                        index_to_synset.append(meaning)
            verb_synset.append(verb_to_synset_index[v])

        if noun_synset and verb_synset:
            for n in noun_synset:
                if n in noun_to_verb:
                    
                    for v in verb_synset:
                        if v not in noun_to_verb[n]:
                            noun_to_verb[n].append(v)
                            
                else:
                    noun_to_verb[n] = verb_synset
            for v in verb_synset:
                if v in verb_to_noun:
                    
                    for n in noun_synset:
                        if n not in verb_to_noun[v]:
                            verb_to_noun[v].append(n)
                            
                else:
                    verb_to_noun[v] = noun_synset
    return

def generateNounVerbArc(index_to_synset, subsumer_cache, noun_to_verb, verb_to_noun):
    noun_arc = set()
    verb_arc = set()
    for n in list(noun_to_verb.keys()):
        verb = noun_to_verb[n]
        n_verb = len(verb)
        if n_verb > 1:
            for idx in range(n_verb - 1):
                synset_index = readFromSubsumerCache(subsumer_cache, verb[idx], verb[idx + 1])
                if not synset_index:
                    synset_index = writeToSubsumerCache(index_to_synset, subsumer_cache, verb[idx], verb[idx + 1])
                if synset_index:
                    verb_arc.update(synset_index)
    for v in list(verb_to_noun.keys()):
        noun = verb_to_noun[v]
        n_noun = len(noun)
        if n_noun > 1:
            for idx in range(n_noun - 1):
                synset_index = readFromSubsumerCache(subsumer_cache, noun[idx], noun[idx + 1])
                if not synset_index:
                    synset_index = writeToSubsumerCache(index_to_synset, subsumer_cache, noun[idx], noun[idx + 1])
                if synset_index:
                    noun_arc.update(synset_index)
    return (noun_arc, verb_arc)

def readFromSubsumerCache(subsumer_cache, synset_index_1, synset_index_2):
    combo_1 = (synset_index_1, synset_index_2)
    combo_2 = (synset_index_2, synset_index_1)
    if combo_1 in subsumer_cache:
        return subsumer_cache[combo_1]
    elif combo_2 in subsumer_cache:
        return subsumer_cache[combo_2]
    else:
        return False

def writeToSubsumerCache(index_to_synset, subsumer_cache, synset_index_1, synset_index_2):
    combo = [synset_index_1, synset_index_2]
    combo.sort()
    synset = index_to_synset[synset_index_1].lowest_common_hypernyms(index_to_synset[synset_index_2])
    if not synset:
        return False
    else:
        synset_index = set()
        for s in synset:
            if s in index_to_synset:
                synset_index.add(index_to_synset.index(s))
            else:
                synset_index.add(len(index_to_synset))
                index_to_synset.append(s)
        subsumer_cache[tuple(combo)] = synset_index
        return synset_index

def inverseResult(google_result):
    inverse_doc_frequency = dict()
    inverse_google_result = dict()
    n_result = len(google_result)
    for key in list(google_result.keys()):
        for synset_index in google_result[key]:
            if synset_index in inverse_doc_frequency:
                inverse_doc_frequency[synset_index] -= 1
                inverse_google_result[synset_index].append(key)
            else:
                inverse_doc_frequency[synset_index] = n_result
                inverse_google_result[synset_index] = [key]
    return (inverse_google_result, inverse_doc_frequency)

def informativeness(google_result, inverse_doc_frequency):
    informative = dict()
    for key in list(google_result.keys()):
        informative[key] = sum([inverse_doc_frequency[synset_index] for synset_index in google_result[key]])
    return informative

def googleSimilarity(google_result, inverse_doc_frequency):
    synset_index = list(google_result.keys())
    column = dict()
    for outer in synset_index:
        row = dict()
        if google_result[outer]:
            for inner in synset_index:
                if not inner == outer:
                    row[similarity(google_result, outer, inner, inverse_doc_frequency)] = inner
        column[outer] = row
    return column

def similarity(google_result, k1, k2, inverse_doc_frequency):
    denominator = sum([inverse_doc_frequency[synset_index] for synset_index in google_result[k1]])
    if denominator == 0:
        return 0
    else:
        numerator = sum([inverse_doc_frequency[synset_index] for synset_index in google_result[k1].intersection(google_result[k2])])
        return numerator / denominator

def isEndOfSentence(s):
    return False not in [c in ".!?" for c in s]

def isPunctuation(s):
    return False not in [c in string.punctuation for c in s]

def isStopWord(w):
    return w.lower() in ["i", "me", "my", "myself", "we", "us", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "will", "would", "shall", "should", "can", "could", "may", "might", "must", "ought", "i'm", "you're", "he's", "she's", "it's", "we're", "they're", "i've", "you've", "we've", "they've", "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll", "you'll", "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't", "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't", "mustn't", "let's", "that's", "who's", "what's", "here's", "there's", "when's", "where's", "why's", "how's", "daren't", "needn't", "oughtn't", "mightn't", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "every", "least", "less", "many", "now", "ever", "never", "also", "just", "put", "whether", "since", "another", "however", "one", "two", "three", "four", "five", "first", "second", "new", "old", "high", "long"]

#(google_result, index_to_synset) = extractFeature(8, "engine")
#(inverse_google_result, inverse_doc_frequency) = inverseResult(google_result)
#informative = informativeness(google_result, inverse_doc_frequency)
#s = googleSimilarity(google_result, inverse_doc_frequency)
