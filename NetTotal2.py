import threading
import multiprocessing
import collections
import time
import nltk
from nltk.chunk import named_entity
import urllib
import bs4
import re
import string
import simplejson
import copy
import webbrowser
from tkinter import *

def successfulUpdate(lancaster, stemmed_query, url, index_to_synset, synset_to_index, noun_to_synset_index, verb_to_synset_index, subsumer_cache):
    text = getPageText(url)
    if not text:
        return False
    else:
        tokens = nltk.word_tokenize(text)
        pos = sentencePOS(lancaster, stemmed_query, tokens)
        noun_to_verb = dict()
        verb_to_noun = dict()
        for p in pos:
            updateDictionary(p, index_to_synset, synset_to_index, noun_to_synset_index, verb_to_synset_index, noun_to_verb, verb_to_noun)
        (noun_arc, verb_arc) = generateNounVerbArc(index_to_synset, synset_to_index, subsumer_cache, noun_to_verb, verb_to_noun)
        return noun_arc.union(verb_arc)

def updateDictionary(pos, index_to_synset, synset_to_index, noun_to_synset_index, verb_to_synset_index, noun_to_verb, verb_to_noun):
#    name_entity = [n[0] for n in set(filter(lambda t: 'NE' in t[1], pos))]
    noun = [n[0] for n in set(filter(lambda t: 'NN' in t[1], pos))]
    verb = [v[0] for v in set(filter(lambda t: 'VB' in t[1], pos))]
    tokens = noun + verb
    if (len(noun) > 0) and (len(verb) > 0):
        noun_synset_index = []
        verb_synset_index = []
        
        for n in noun:
            if (n not in noun_to_synset_index):
                meaning = nltk.wsd.lesk(tokens, n, 'n')
                if meaning is None:
                    continue
                else:
                    if meaning in synset_to_index:
                        noun_to_synset_index[n] = synset_to_index[meaning]
                    else:
                        idx = len(index_to_synset)
                        synset_to_index[meaning] = idx
                        index_to_synset[idx] = meaning
                        noun_to_synset_index[n] = idx
            noun_synset_index.append(noun_to_synset_index[n])
        for v in verb:
            if (v not in verb_to_synset_index):
                meaning = nltk.wsd.lesk(tokens, v, 'v')
                if meaning is None:
                    continue
                else:
                    if meaning in synset_to_index:
                        verb_to_synset_index[v] = synset_to_index[meaning]
                    else:
                        idx = len(index_to_synset)
                        synset_to_index[meaning] = idx
                        index_to_synset[idx] = meaning
                        verb_to_synset_index[v] = idx
            verb_synset_index.append(verb_to_synset_index[v])

        if noun_synset_index and verb_synset_index:
            for n in noun_synset_index:
                if n in noun_to_verb:
                    
                    for v in verb_synset_index:
                        if v not in noun_to_verb[n]:
                            noun_to_verb[n].append(v)
                            
                else:
                    noun_to_verb[n] = verb_synset_index
            for v in verb_synset_index:
                if v in verb_to_noun:
                    
                    for n in noun_synset_index:
                        if n not in verb_to_noun[v]:
                            verb_to_noun[v].append(n)
                            
                else:
                    verb_to_noun[v] = noun_synset_index
    return

def generateNounVerbArc(index_to_synset, synset_to_index, subsumer_cache, noun_to_verb, verb_to_noun):
    noun_arc = set()
    verb_arc = set()
    for n in list(noun_to_verb.keys()):
        verb = noun_to_verb[n]
        n_verb = len(verb)
        if n_verb > 1:
            for idx in range(n_verb - 1):
                synset_index = readFromSubsumerCache(subsumer_cache, verb[idx], verb[idx + 1])
                if not synset_index:
                    synset_index = writeToSubsumerCache(index_to_synset, synset_to_index, subsumer_cache, verb[idx], verb[idx + 1])
                if synset_index:
                    verb_arc.update(synset_index)
    for v in list(verb_to_noun.keys()):
        noun = verb_to_noun[v]
        n_noun = len(noun)
        if n_noun > 1:
            for idx in range(n_noun - 1):
                synset_index = readFromSubsumerCache(subsumer_cache, noun[idx], noun[idx + 1])
                if not synset_index:
                    synset_index = writeToSubsumerCache(index_to_synset, synset_to_index, subsumer_cache, noun[idx], noun[idx + 1])
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

def writeToSubsumerCache(index_to_synset, synset_to_index, subsumer_cache, synset_index_1, synset_index_2):
    combo = [synset_index_1, synset_index_2]
    combo.sort()
    synset = index_to_synset[synset_index_1].lowest_common_hypernyms(index_to_synset[synset_index_2])
    if not synset:
        return False
    else:
        synset_index = set()
        for s in synset:
            if s not in synset_to_index:
                idx = len(index_to_synset)
                synset_to_index[s] = idx
                index_to_synset[idx] = s
            synset_index.add(synset_to_index[s])
        subsumer_cache[tuple(combo)] = synset_index
        return synset_index

def getPageText(url):
    try:
        html = urllib.request.urlopen(url).read()
    except:
        return False
    source = bs4.BeautifulSoup(html)
    lines = source.findAll(text=True)
    return '\n'.join(list(filter(visible, lines)))

def visible(element):
    if element.parent.name in ['style', 'script', '[document]', 'head', 'title']:
        return False
    elif re.match('<!--.*-->', str(element)):
        return False
    return True

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

def isEndOfSentence(s):
    return False not in [c in ".!?" for c in s]

def stemTokens(lancaster, tokens):
    temp = []
    for word in tokens:
        if not isStopWord(word) and not isPunctuation(word):
            temp.append(lancaster.stem(word))
    return set(temp)

def isStopWord(w):
    return w.lower() in ["i", "me", "my", "myself", "we", "us", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "will", "would", "shall", "should", "can", "could", "may", "might", "must", "ought", "i'm", "you're", "he's", "she's", "it's", "we're", "they're", "i've", "you've", "we've", "they've", "i'd", "you'd", "he'd", "she'd", "we'd", "they'd", "i'll", "you'll", "he'll", "she'll", "we'll", "they'll", "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't", "doesn't", "don't", "didn't", "won't", "wouldn't", "shan't", "shouldn't", "can't", "cannot", "couldn't", "mustn't", "let's", "that's", "who's", "what's", "here's", "there's", "when's", "where's", "why's", "how's", "daren't", "needn't", "oughtn't", "mightn't", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "every", "least", "less", "many", "now", "ever", "never", "also", "just", "put", "whether", "since", "another", "however", "one", "two", "three", "four", "five", "first", "second", "new", "old", "high", "long"]

def isPunctuation(s):
    return False not in [c in string.punctuation for c in s]

def nameEntityPOS(sentence):
    pos = nltk.pos_tag(sentence)
    entity = nltk.chunk.ne_chunk(pos, binary=True)
    result = [('_'.join([l[0] for l in e.leaves()]), e.label()) if isinstance(e, nltk.tree.Tree) else e for e in entity]
    return list(filter(lambda r: not isPunctuation(r[0]), result))

class GUI:
    def __init__(self, parent):
        self.menubar = Menu(parent)
        self.menubar.add_command(label="START")
        self.menubar.add_command(label="HELP")
        self.menubar.add_command(label="STOP")
        self.menubar.add_command(label="ABOUT")
        self.menubar.add_command(label="EXIT")
        parent.config(menu=self.menubar)

        self.main_window = PanedWindow(parent, orient=HORIZONTAL, name="main_window")
        self.main_window.pack(fill=BOTH, expand=1)
        self.main_window.bind_all("<Button-1>", self.activeWidget)
        self.main_window.bind_all("<Control-Button-1>", self.activeWidget)
        self.main_window.bind_all("<ButtonRelease-1>", self.mouse_button_1_handler)
        self.main_window.bind_all("<Control-ButtonRelease-1>", self.ctrl_mouse_button_1_handler)

        self.search_window = PanedWindow(self.main_window, orient=VERTICAL, name="search_window")
        self.main_window.add(self.search_window)

        self.query_window = Frame(self.search_window, name="query_window")
        self.search_window.add(self.query_window)
        self.query_scroll = Scrollbar(self.query_window)
        self.query_scroll.pack(side=RIGHT, fill=Y)
        self.query_box = Text(self.query_window, yscrollcommand=self.query_scroll.set, name="query_box")
        self.query_scroll.config(command=self.query_box.yview)
        self.query_box.pack(side=LEFT, fill=BOTH, expand=1)

        self.status_window = Frame(self.search_window, name="status_window")
        self.search_window.add(self.status_window)
        self.status_scroll = Scrollbar(self.status_window)
        self.status_scroll.pack(side=RIGHT, fill=Y)
        self.status_box = Text(self.status_window, yscrollcommand=self.status_scroll.set, name="status_box")
        self.status_scroll.config(command=self.status_box.yview)
        self.status_box.pack(side=LEFT, fill=BOTH, expand=1)

        self.coverage_window = Frame(self.main_window, name="coverage_window")
        self.main_window.add(self.coverage_window)
        self.coverage_scroll = Scrollbar(self.coverage_window)
        self.coverage_scroll.pack(side=RIGHT, fill=Y)
        self.coverage_box = Listbox(self.coverage_window, selectmode=EXTENDED, yscrollcommand=self.coverage_scroll.set, name="coverage_box")
        self.coverage_scroll.config(command=self.coverage_box.yview)
        self.coverage_box.pack(side=LEFT, fill=BOTH, expand=1)

        self.active_widget = []

    def activeWidget(self, event):
        self.active_widget = self.main_window.winfo_containing(event.x_root, event.y_root)

    def mouse_button_1_handler(self, event):
        mouse_pointer_address = str(self.active_widget).split('.')
        if "query_box" in mouse_pointer_address:
            pass
        if "status_box" in mouse_pointer_address:
            pass
        if "coverage_box" in mouse_pointer_address:
            lancaster = nltk.stem.lancaster.LancasterStemmer()
            url = 'http://www.comicvine.com/batman/4005-1699/'
            arcs = successfulUpdate(lancaster, {'batm'}, url, dict(), dict(), dict(), dict(), dict())
            for arc in arcs:
                self.putStatus(str(arc))
                
    def ctrl_mouse_button_1_handler(self, event):
        mouse_pointer_address = str(self.active_widget).split('.')
        if "query_box" in mouse_pointer_address:
            pass
        if "status_box" in mouse_pointer_address:
            pass
        if "coverage_box" in mouse_pointer_address:
            self.putStatus("I pushed Ctrl M1!")

    def putStatus(self, text):
        max_number_of_lines = 100
        self.status_box.insert(END, text + '\n')
        while int(self.status_box.index('end-1c').split('.')[0]) > max_number_of_lines:
            self.status_box.delete("1.0", "2.0")
        self.status_box.see(END)

    def openURL(self, url):
        webbrowser.open(url, new=2, autoraise=True)

def main():
    root = Tk()
    gui = GUI(root)
    root.mainloop()
    
#    lancaster = nltk.stem.lancaster.LancasterStemmer()
#    url = 'http://www.comicvine.com/batman/4005-1699/'
    
#    arcs = successfulUpdate(lancaster, {'batm'}, url, dict(), dict(), dict(), dict(), dict())
#    print(arcs)

if __name__ == "__main__":
    main()
