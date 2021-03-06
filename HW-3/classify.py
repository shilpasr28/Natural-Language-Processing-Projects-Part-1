# -*- coding: utf-8 -*-
"""
Created on Fri Sep 22 20:00:19 2017

@author: SHILPASHREE RAO
"""

#!/usr/bin/env python
from collections import defaultdict
from csv import DictReader, DictWriter
import nltk
import codecs
import sys
from nltk.corpus import wordnet as wn
from nltk.tokenize import TreebankWordTokenizer
from nltk.tokenize import RegexpTokenizer
import string
from nltk.corpus import stopwords
from nltk.corpus import cmudict 

kTOKENIZER = TreebankWordTokenizer()

def morphy_stem(word):##root words
    """
    Simple stemmer
    """
    stem = wn.morphy(word)
    if stem:
        return stem.lower()
    else:
        return word.lower()
    
def type_token_ratio(tex):
    c = Counter()
    for sentence in sent_tokenize(tex.lower()):
        c.update([word for word in word_tokenize(sentence) if len(word) > 1])
    num_tokens = sum(c.values())
    num_types = len(c)
    return {'Ratio': float(num_types)/num_tokens}
   

class FeatureExtractor:
    def __init__(self):
        """
        You may want to add code here
        """
        None
    
    def features(self, text):
        d = defaultdict(int)
        tok = kTOKENIZER.tokenize(text)   
        trgrm = [text[i:i+3] for i in xrange(len(text)-2)]
        bgrm = [text[i:i+2] for i in xrange(len(text)-1)]
        fourgrm = [text[i:i+4] for i in xrange(len(text)-3)]
        lenW = [len(x) for x in tok]
        senlen = 0
        for i in lenW:
            senlen += i
        noPunc = [w for w in tok if w not in string.punctuation]
        bigrm = list(nltk.bigrams(noPunc))
        trigrm = list(nltk.trigrams(noPunc))
        noStpwrd = [w for w in noPunc if w not in stopwords.words('english')]

        for ii in noStpwrd:   
            d[morphy_stem(ii)] += 1  
            

        d["len"] = senlen
        d["lenb"] = len(bigrm)
        d["leng"] = len(trigrm)
        d["leng"] = len(fourgrm)
        d["fw"] = tok[0]  
        print tok[0]
        sys.exit()
        for ii in bgrm:
            d["br"] = ii
        for ii in trgrm:
            d["tr"] = ii
        for ii in fourgrm:
            d["fr"] = ii

        return d
    
reader = codecs.getreader('utf8')
writer = codecs.getwriter('utf8')

def prepfile(fh, code):
  if type(fh) is str:
    fh = open(fh, code)
  ret = gzip.open(fh.name, code if code.endswith("t") else code+"t") if fh.name.endswith(".gz") else fh
  if sys.version_info[0] == 2:
    if code.startswith('r'):
      ret = reader(fh)
    elif code.startswith('w'):
      ret = writer(fh)
    else:
      sys.stderr.write("I didn't understand code "+code+"\n")
      sys.exit(1)
  return ret

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument("--trainfile", "-i", nargs='?', type=argparse.FileType('r'), default=sys.stdin, help="input train file")
    parser.add_argument("--testfile", "-t", nargs='?', type=argparse.FileType('r'), default=None, help="input test file")
    parser.add_argument("--outfile", "-o", nargs='?', type=argparse.FileType('w'), default=sys.stdout, help="output file")
    parser.add_argument('--subsample', type=float, default=1.0,
                        help='subsample this fraction of total')
    args = parser.parse_args()
    trainfile = prepfile('train.tsv', 'r')
    if args.testfile is not None:
        testfile = prepfile(args.testfile, 'r')
    else:
        testfile = None
    outfile = prepfile(args.outfile, 'w')
    

    # Create feature extractor (you may want to modify this)
    fe = FeatureExtractor()
    
    # Read in training data
    train = DictReader(trainfile, delimiter='\t')
    
    # Split off dev section
    dev_train = []
    dev_test = []
    full_train = []

    for ii in train:
        if args.subsample < 1.0 and int(ii['id']) % 100 > 100 * args.subsample:
            continue
  
        feat = fe.features(ii['text'])    
       
        if int(ii['id']) % 5 == 0:
            dev_test.append((feat, ii['cat']))
        else:
            dev_train.append((feat, ii['cat']))
        full_train.append((feat, ii['cat']))

    # Train a classifier
    sys.stderr.write("Training classifier ...\n")
    classifier = nltk.classify.NaiveBayesClassifier.train(dev_train)

    right = 0
    total = len(dev_test)
    for ii in dev_test:
        prediction = classifier.classify(ii[0])
        if prediction == ii[1]:
            right += 1
    sys.stderr.write("Accuracy on dev: %f\n" % (float(right) / float(total)))

    if testfile is None:
        sys.stderr.write("No test file passed; stopping.\n")
    else:
        # Retrain on all data
        classifier = nltk.classify.NaiveBayesClassifier.train(dev_train + dev_test)

        # Read in test section
        test = {}
        for ii in DictReader(testfile, delimiter='\t'):
            test[ii['id']] = classifier.classify(fe.features(ii['text']))

        # Write predictions
        o = DictWriter(outfile, ['id', 'pred'])
        o.writeheader()
        for ii in sorted(test):
            o.writerow({'id': ii, 'pred': test[ii]})