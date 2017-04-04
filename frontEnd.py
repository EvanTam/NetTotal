from backEnd import extractFeature
import numpy
import hashlib
import os
import sys
import random
import binascii

def extractStatistics(document):
    doc_idx_to_key = list(document.keys())

    frequency = dict()
    occurrence = dict()
    for doc_idx in range(len(doc_idx_to_key)):
        for synset in document[doc_idx_to_key[doc_idx]]:
            if synset in frequency:
                frequency[synset] += 1
                occurrence[synset].append(doc_idx)
            else:
                frequency[synset] = 1
                occurrence[synset] = [doc_idx]
    return (frequency, occurrence, doc_idx_to_key)

def genSignature(seed, occurrence, doc_idx_to_key):
    occ_idx_to_key = list(occurrence.keys())

    signature = dict()
    for occ_idx in range(len(occ_idx_to_key)):
        h = hashFunction(seed, len(occ_idx_to_key), occ_idx)
        for doc_idx in occurrence[occ_idx_to_key[occ_idx]]:
            if doc_idx_to_key[doc_idx] in signature:
                signature[doc_idx_to_key[doc_idx]] = numpy.minimum(signature[doc_idx_to_key[doc_idx]], h)
            else:
                signature[doc_idx_to_key[doc_idx]] = h
    return signature

def randHashSeed(n):
    random.getrandbits(128)
    return [int.from_bytes(os.urandom(16), sys.byteorder) for i in range(n)]

def hashFunction(seed, num_of_synset, i):
    m = int.from_bytes(hashlib.md5(str(i).encode()).digest(), sys.byteorder)
    return numpy.array([(s ^ m) % num_of_synset for s in seed])

n = 200
document = extractFeature(8)
(frequency, occurrence, doc_idx_to_key) = extractStatistics(document)
seed = randHashSeed(n)
signature = genSignature(seed, occurrence, doc_idx_to_key)
#signature['http://www.dccomics.com/characters/batman'] == signature['http://batman.wikia.com/wiki/Batman']

