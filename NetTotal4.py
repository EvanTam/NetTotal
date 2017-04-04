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

def ajaxGoogle(n, i, q):
    query = urllib.parse.urlencode({'rsz':str(n), 'start':str(i), 'q':q})
    url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&%s' % (query)
    while True:
        json = simplejson.loads(urllib.request.urlopen(url).read())
        if json['responseData']:
            results = json['responseData']['results']
            break
        time.sleep(10)
    return [result['url'] for result in results]

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

class CrawlerThread(threading.Thread):
    def __init__(self, gui, new_search_event):
        threading.Thread.__init__(self)
        self.gui = gui    # get a handle on gui to print status
        self.new_search_event = new_search_event
        self.chunk_size = 1    # This specifies how many URLs are processed in each task, right now each task consist of only one URL
        self.result_per_batch = 8    # This specifies how many URLs are returned each time we query Google Search
        self.timeout_duration = 30    # This is a fail-safe timeout to break out of the infinite loop when an unknown error occurs, right now it is 30 seconds
        self.task_queue = multiprocessing.Manager().Queue()    # This queue represents the conveyor belt that delivers to-do tasks to the workers
        self.result_queue = multiprocessing.Manager().Queue()    # This queue represents the conveyor belt that collects the completed tasks from the workers
        self.number_of_process_to_spawn = multiprocessing.cpu_count()    # This variable tells us how many core/cpu this computer has, the number of works equals the number of cpu
        self.stop_flag = False    # This flag is used to stop in the middle of the crawling process
        self.quit_flag = False    # This flag signals the user wants to quit the program

    def run(self):
        while self.new_search_event.wait() and not self.quit_flag:   # This loop is not part of the crawling procss, it is just used to restart search on a new query as run() can only be called once
            crawlers = [CrawlerProcess(self.task_queue, self.result_queue, self.gui.stemmed_query, idx) for idx in range(self.number_of_process_to_spawn)]    # Spawn crawlers
            for crawler in crawlers:
                crawler.start()    # Start all the crawlers to wait for tasks to arrive
            self.gui.putStatus('%d crawlers spawned' % self.number_of_process_to_spawn)    # Tell user how many worker was spawned
            
            threshold = self.gui.max_number_of_result + 1 - self.result_per_batch    # This sets the stopping condition when the number of URLs visited reaches the maximum number of result specified by the user
            current_batch_index = 0    # This specifies which batch of result we want from Google making sure we dont get the same part more than once

            time_out = self.timeout_duration    # We set the count down timer, when this reaches zero, execution of the crawl loop ends regardless if all tasks are completed or not
            task_sent = 0    # This counts how many tasks was produced so we know when all the tasks are completed
            self.gui.result = collections.OrderedDict()    # This is a temporary storage to repackage Google results into tasks containing a different number of URLs than the batch size from Google
            start_time = time.time()    # We want to measure how long the summarization took to generate
            
            while not self.stop_flag:    # We keep going until all tasks are completed as long as the user do not terminate us in the middle of the crawling process
                if current_batch_index < threshold:    # If the number of Google results (in terms of batches) do not exceed the maximum number specified by the user
                    try:
                        batch = ajaxGoogle(self.result_per_batch, current_batch_index, self.gui.query)    # Try to get a batch of result from Google
                        if batch:    # If the batch we just retrived contains something
                            for url in batch:    # Append the new batch of result to the original
                                self.gui.result[url] = []
                            url_list = list(self.gui.result.keys())
                            result_len = len(url_list)    # Get the length of the original
                            overflow_height = ((task_sent + 1) * self.chunk_size)    # Calculate the position relative to the data we just added to the original of where we should start to extract the next task from
                            if result_len >= overflow_height:    # If the cache fill level is high enough to make as least one task
                                interval = range(overflow_height, result_len, self.chunk_size)    # Divide batch cache content into equal portions
                                for idx in interval:
                                    self.task_queue.put(url_list[(idx - self.chunk_size):idx])    # Repackage each portion into a task and put it on the task queue
                                    task_sent += 1    # Keep track of the task we just sent
                                    self.gui.putStatus('Number of task sent: %d' % task_sent)    # Tell the userr how many task was sent
                    except:
                        pass    # Do not try to correct any error, simply skip to the next batch. quantity is more important than quality
                    current_batch_index += self.result_per_batch    # Increment the batch index to get the next batch of result for the same query from Google
                else:    # If we are here it means we have already retrived the maximum number of result specified by the user, this thread will now switch mode to collect results from the workers
                    if self.result_queue.empty():    # If the result queue is empty because no task has been completed yet
                        time.sleep(1)    # Then sleep for 1 second
                        time_out -= 1    # Record the time we just slept using the count down timer
                    else:
                        time_out = self.timeout_duration    # If there is something in the result queue then reset the count down timer
                        result = self.result_queue.get()    # Get a result from he result queue
                        self.gui.updateResult(result)    # Update the summary at the GUI using the result we just got
                        self.result_queue.task_done()    # Tell the result queue we just completed the task
                        task_sent -= 1    # Record that a task was completed
                        self.gui.putStatus('Remaining task to process: %d' % task_sent)    # Update the user how many task we still need to complete
                    if (task_sent == 0) or (time_out == 0):   # Break out if we are done or timed out
                        break

            while not self.task_queue.empty():    # Flush the task queue
                self.task_queue.get()    # Throw out all the tasks from the task queue
                self.task_queue.task_done()    # Mark all thrown tasks as done
            for poison_pill in range(self.number_of_process_to_spawn):    # kill the worker processes using the poison pill technique
                self.task_queue.put(None)
            self.task_queue.join()    # Check and wait for the task queue to empty
            while not self.result_queue.empty():    # Process the remaining results if any left in the result queue
                result = self.result_queue.get()    # Pickup a result
                self.gui.updateResult(result)    # Update the summary with it
                self.result_queue.task_done()    # Mark the complete task as done
                task_sent -= 1
            self.result_queue.join()    # Check and wait for the result queue to empty
            for crawler in crawlers:    # The work is done so terminate the workers
                crawler.terminate()
            self.gui.putStatus('%d crawlers were disposed of' % self.number_of_process_to_spawn)
            if task_sent == 0:
                self.gui.putStatus('All tasks completed successfully')    # Tell the user all task were completed
            else:
                self.gui.putStatus('Time-out initiated, fail to reach %d URLs!' % (task_sent * self.chunk_size))
            end_time = time()    # Stop the timer and see how long the crawl process took
            self.gui.putStatus('Your last crawl took ' + str(round(end_time-start_time)) + ' seconds!')
            self.stop_flag = False    # Make sure the inner loop can proceed for the next crawl
            self.new_search_event.clear()    # Reset the search event because we just handled it
        return

    def stop(self):
        if self.new_search_event.isSet() and self.stop_flag is False:    # If a new search event has not been handled yet but we are still in the inner loop then it means we are in the middle of a crawl
            self.stop_flag = True    # Set the stop flag to break out of the main crawl loop and proceed to clean up

    def quitThread(self):
        self.stop()
        self.quit_flag = True
        

class CrawlerProcess(multiprocessing.Process):
    def __init__(self, task_queue, result_queue, stemmed_query, idx):
        multiprocessing.Process.__init__(self)
        self.task_queue = task_queue
        self.result_queue = result_queue
        self.stemmed_query = stemmed_query
        self.idx = idx

    def run(self):
        while True:
            if self.task_queue.empty():
                time.sleep(1)
                continue
            else:
                task = self.task_queue.get()
                if task is None:
                    self.task_queue.task_done()
                    break
                else:
                    result = crawlTask(task, self.stemmed_query)
                    self.result_queue.put(result)
                    self.task_queue.task_done()
        return

def crawlTask(task, stemmed_query):
    index_to_synset = dict()
    synset_to_index = dict()
    noun_to_synset_index = dict()
    verb_to_synset_index = dict()
    subsumer_cache = dict()
    result = dict()
    
    lancaster = nltk.stem.lancaster.LancasterStemmer()
    we_have_made_progress = True
    while task and we_have_made_progress:
        we_have_made_progress = False
        for url in task[:]:
            arcs = successfulUpdate(lancaster, stemmed_query, url, index_to_synset, synset_to_index, noun_to_synset_index, verb_to_synset_index, subsumer_cache)
            if arcs:
                result[url] = [index_to_synset[arc].name() for arc in arcs]
                task.remove(url)
                we_have_made_progress = True
    return result

class ProcessingThread(threading.Thread):
    def __init__(self, gui, result_changed_event):
        threading.Thread.__init__(self)
        self.gui = gui
        self.result_changed_event = result_changed_event
        self.quit_flag = False    # This flag signals the user wants to quit the program

    def run(self):
        while self.result_changed_event.wait() and not self.quit_flag:
            self.result_changed_event.clear()
            self.gui.coverage_box.delete(0, END)
            result = self.gui.snapshotResult()
            (self.gui.sorted_inverse_result, self.gui.inverse_doc_frequency) = inverseResult(result)
            informative = informativeness(result, self.gui.inverse_doc_frequency)
            unsorted_summary = set([self.gui.sorted_inverse_result[synset_index][0] for synset_index in list(self.gui.sorted_inverse_result.keys())])
            summary_tuples = [(url, informative[url]) for url in unsorted_summary]
            self.gui.sorted_summary = collections.OrderedDict(sorted(summary_tuples, key=lambda u: u[1], reverse=True))
            summary_index_to_url = list(self.gui.sorted_summary.keys())
            highlighted_index = []
            idx = 0
            for url in self.gui.result:
                if url in self.gui.sorted_summary:
                    self.gui.sorted_summary[url] = idx
                    highlighted_index.append(idx)
                    self.gui.coverage_box.insert(END, str(summary_index_to_url.index(url)) + ' ' + url)
                else:
                    self.gui.coverage_box.insert(END, url)
                idx += 1
            [self.gui.coverage_box.itemconfig(idx, fg='red') for idx in highlighted_index]
        return

    def quitThread(self):
        self.quit_flag = True

def inverseResult(result):
    inverse_doc_frequency = dict()
    inverse_result = dict()
    sorted_inverse_result = collections.OrderedDict()
    n_result = len(result)
    for url in list(result.keys()):
        for synset_index in result[url]:
            if synset_index in inverse_doc_frequency:
                inverse_doc_frequency[synset_index] -= 1
                inverse_result[synset_index].append(url)
            else:
                inverse_doc_frequency[synset_index] = n_result
                inverse_result[synset_index] = [url]

    for synset_index in list(inverse_result.keys()):
        url_tuples = [(url, len(result[url])) for url in inverse_result[synset_index]]
        url_tuples = sorted(url_tuples, key=lambda u: u[1], reverse=True)
        inverse_result[synset_index] = [u[0] for u in url_tuples]

    synset_index_tuples = [(synset_index, inverse_doc_frequency[synset_index]) for synset_index in list(inverse_result.keys())]
    synset_index_tuples = sorted(synset_index_tuples, key=lambda u: u[1], reverse=True)
    for s in synset_index_tuples:
        sorted_inverse_result[s[0]] = inverse_result[s[0]]
    return (sorted_inverse_result, inverse_doc_frequency)

def informativeness(result, inverse_doc_frequency):
    informative = dict()
    for url in list(result.keys()):
        informative[url] = sum([inverse_doc_frequency[synset_index] for synset_index in result[url]])
    return informative

class GUI:
    def __init__(self, parent):
        parent.wm_protocol("WM_DELETE_WINDOW", self.quitProgram)
        
        self.menubar = Menu(parent)
        self.menubar.add_command(label="START", command=self.startSearch)
        self.menubar.add_command(label="HELP")
        self.menubar.add_command(label="STOP", command=self.stopSearch)
        self.menubar.add_command(label="ABOUT")
        self.menubar.add_command(label="EXIT", command=self.quitProgram)
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

        self.query = []
        self.result = []
        self.active_widget = []
        self.stemmed_query = []
        self.sorted_summary = []
        self.sorted_inverse_result = []
        self.inverse_doc_frequency = []

        self.max_number_of_result = 64

        self.snapshot_lock = threading.Lock()
        self.new_search_event = threading.Event()
        self.crawler_thread = CrawlerThread(self, self.new_search_event)
        self.crawler_thread.start()
        self.result_changed_event = threading.Event()
        self.processing_thread = ProcessingThread(self, self.result_changed_event)
        self.processing_thread.start()

    def activeWidget(self, event):
        self.active_widget = self.main_window.winfo_containing(event.x_root, event.y_root)

    def mouse_button_1_handler(self, event):
        mouse_pointer_address = str(self.active_widget).split('.')
        if "query_box" in mouse_pointer_address:
            pass
        if "status_box" in mouse_pointer_address:
            pass
        if "coverage_box" in mouse_pointer_address:
            highlighted_index = self.coverage_box.curselection()
            url_list = list(self.result.keys())
            if len(highlighted_index) == 1:
                url = url_list[highlighted_index[0]]
                self.openURL(url)

    def ctrl_mouse_button_1_handler(self, event):
        mouse_pointer_address = str(self.active_widget).split('.')
        if "query_box" in mouse_pointer_address:
            pass
        if "status_box" in mouse_pointer_address:
            pass
        if "coverage_box" in mouse_pointer_address and not self.new_search_event.isSet():
            highlighted_index = self.coverage_box.curselection()
            url_list = list(self.result.keys())
            coverage = set()
            for idx in highlighted_index:
                coverage.update(self.result[url_list[idx]])
            coverage_percent = 0
            numerator = sum([self.inverse_doc_frequency[synset_index] for synset_index in coverage])
            denominator = sum(self.inverse_doc_frequency.values())
            if not denominator == 0:
                coverage_percent = round((numerator * 100) / denominator)
            self.putStatus('Your selections cover ' + str(coverage_percent) + '% of all information in the first ' + str(len(url_list)) + ' Google Search results')

    def putStatus(self, text):
        max_number_of_lines = 100
        self.status_box.insert(END, text + '\n')
        while int(self.status_box.index('end-1c').split('.')[0]) > max_number_of_lines:
            self.status_box.delete("1.0", "2.0")
        self.status_box.see(END)

    def openURL(self, url):
        webbrowser.open(url, new=2, autoraise=True)

    def updateResult(self, new_result):
        if new_result:
            for url in new_result:
                self.result[url] = new_result[url]
            self.result_changed_event.set()

    def snapshotResult(self):
        self.snapshot_lock.acquire()
        result_copy = copy.deepcopy(self.result)
        self.snapshot_lock.release()
        return result_copy

    def startSearch(self):
        self.result = collections.OrderedDict()
        self.sorted_inverse_result = collections.OrderedDict()
        self.sorted_summary = collections.OrderedDict()
        self.inverse_doc_frequency = dict()
        self.query = self.query_box.get("1.0",'end-1c')    # Get the query from gui query box
        if not self.query:    # If there is no query then tell the user
            self.putStatus('Please insert query before clicking START!')
        else:
            tokens = nltk.word_tokenize(self.query)    # Break down the query into words
            self.stemmed_query = stemTokens(nltk.stem.lancaster.LancasterStemmer(), tokens)    # Filter stop-words and stem the remaining keywords into their base form
            self.new_search_event.set()    # Tell the crawler to start working

    def stopSearch(self):
        if self.new_search_event.isSet():
            self.crawler_thread.stop()
        else:
            self.putStatus('No running process!')

    def quitProgram(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            if self.crawler_thread.isAlive():
                self.crawler_thread.quitThread()
                self.crawler_thread.join()
            if self.processing_thread.isAlive():
                self.processing_thread.quitThread()
                self.processing_thread.join()
            self.parent.focus_set()
            self.destroy()
        pass

def main():
    root = Tk()
    gui = GUI(root)
    root.mainloop()
    return

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
