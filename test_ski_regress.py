
from __future__ import print_function

from sqlalchemy import or_

import logging
import numpy as np
from optparse import OptionParser
import sys
from time import time
import matplotlib.pyplot as plt
import random
from random import uniform
from urlparse import urlparse
from unidecode import unidecode

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_selection import SelectKBest, chi2
from sklearn.linear_model import BayesianRidge
from sklearn.svm import LinearSVC
from sklearn.linear_model import SGDClassifier
from sklearn.linear_model import Perceptron
from sklearn.linear_model import PassiveAggressiveClassifier
from sklearn.naive_bayes import BernoulliNB, MultinomialNB, GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestCentroid
from sklearn.utils.extmath import density
from sklearn.ensemble import BaggingClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neural_network import BernoulliRBM
from sklearn import metrics
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, PassiveAggressiveRegressor, SGDRegressor, ARDRegression
from sklearn.neighbors import KNeighborsRegressor, RadiusNeighborsRegressor
from sklearn.svm import SVR, NuSVR, SVC

from base.models import Article
from base.database import db_session

from skynet.nlp_util import tokenizer

from pandas import DataFrame

use_hashing = False
print_report = True
n_features = 2 ** 16

# Display progress logs on stdout
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s')

total_num = 2000

def get_articles(article_type, num):
    return (
        db_session
        .query(Article)
        .filter_by(user_id=1, last_action=article_type)
        .order_by(Article.last_action_timestamp.desc())
        .limit(num)
        .all()
    )

last_1k_articles = []
for ind, t in enumerate(('like', 'dislike', 'defer', 'pass')):
    last_1k_articles += get_articles(t, int((total_num - len(last_1k_articles)) / (4 - ind)))
    print(len(last_1k_articles))

score_map = {
    "like": 1.0,
    "dislike": 0.5,
    "defer": 0.7,
    "pass": -1.0,
}


def build_data_frame(article):
    parsed_uri = urlparse(article.url)
    domain = parsed_uri.netloc
    return DataFrame({
        "score": [score_map[article.last_action]],
        "origins": [[o.id for o in article.origins]],
        "domain": [domain],
        "title": [article.title],
        "article": [article],
    }, index=[article.id])


def gen_data_frame(data_set):
    result = DataFrame({'title': [], 'score': [], "domain": [], "origins": [], "article": []})
    for article in data_set:
        result = result.append(build_data_frame(article))

    return result.reindex(np.random.permutation(result.index))

random.shuffle(last_1k_articles)
# last_1k_articles.sort(key=lambda article: article.last_action_timestamp)
train_size = len(last_1k_articles) * 8 / 10
train_set = last_1k_articles[:train_size]
test_set = last_1k_articles[train_size:]

data_train = gen_data_frame(train_set)
data_test = gen_data_frame(test_set)

y_train, y_test = data_train['score'], data_test['score']

print("Extracting features from the training dataset using a sparse vectorizer")
if use_hashing:
    vectorizer = HashingVectorizer(stop_words='english', non_negative=True,
                                   preprocessor=lambda x: x,
                                   tokenizer=tokenizer,
                                   n_features=n_features)
    X_train = vectorizer.transform(data_train['article'])
else:
    # vectorizer = TfidfVectorizer(sublinear_tf=True, max_df=0.5,
    #                              preprocessor=lambda x: x,
    #                              tokenizer=tokenizer,
    #                              stop_words='english')
    vectorizer = CountVectorizer(preprocessor=lambda x: x,
                                 binary=True,
                                 tokenizer=tokenizer,
                                 stop_words='english')
    X_train = vectorizer.fit_transform(data_train['article'])


print("Extracting features from the test dataset using the same vectorizer")
X_test = vectorizer.transform(data_test['article'])

print(X_train.shape)

# from sklearn.feature_selection import SelectKBest
# from sklearn.feature_selection import chi2
# sel = SelectKBest(chi2, k=30000)

# X_train = sel.fit_transform(X_train, [int(y * 10) for y in y_train])
# X_test = sel.transform(X_test)

# mapping from integer feature name to original token string
if use_hashing:
    feature_names = None
else:
    feature_names = np.asarray(vectorizer.get_feature_names())

###############################################################################
# Benchmark regressors
def benchmark(rgs, name="eh"):
    print('_' * 80)
    print("Training: ")
    print(rgs)
    t0 = time()
    try:
        rgs.fit(X_train, y_train, [1 if i < 0 else 10 for i in y_train])
    except:
        rgs.fit(X_train, y_train)
    train_time = time() - t0
    print("train time: %0.3fs" % train_time)

    t0 = time()
    pred = rgs.predict(X_test)
    test_time = time() - t0
    print("test time:  %0.3fs" % test_time)

    from sklearn.metrics import explained_variance_score, mean_squared_error, r2_score, mean_absolute_error
    from scipy.stats import wilcoxon, spearmanr, pearsonr
    # print(y_test, pred)
    # score = explained_variance_score(y_test, pred)
    # score = mean_squared_error(y_test, pred)
    # score = mean_absolute_error(y_test, pred)
    # score = r2_score(y_test, pred)
    # eh, score = wilcoxon(y_test, pred)
    score, pval = spearmanr(y_test, pred)
    # score, pval = pearsonr(y_test, pred)
    print(pval, 'pvalue')

    result_image = []
    fake_y = [uniform(y, 0) if y < 0 else uniform(0, y) for y in y_test]
    for i, key in enumerate(y_test.keys()):
        result_image.append({
            "size": 2,
            'id': str(i),
            'x': fake_y[i],
            'y': -pred[i],
            'label': data_test['article'][key].title,
        })

    import json
    with open('visualize/{0}.json'.format(name), 'w') as f:
        json.dump({'nodes': result_image}, f)

    plt.figure(figsize=(12, 8))
    plt.plot(fake_y, pred, 'ro')
    plt.show()

    clf_descr = str(rgs).split('(')[0]

    return clf_descr, score, train_time, test_time
    # return clf_descr, score, train_time, test_time


class ProbClassifier():

    def __init__(self, clf):
        self.clf = clf

    def fit(self, x, y):
        self.clf.fit(x, [int(i * 10) for i in y])

    def predict(self, test):
        confidence = self.clf.predict_proba(test)
        return [
            sum(float(c) * self.clf.classes_[ind] / 10 for ind, c in enumerate(con)) for con in confidence
        ]



class L1LinearSVC(LinearSVC):

    def fit(self, X, y):
        # The smaller C, the stronger the regularization.
        # The more regularization, the more sparsity.
        self.transformer_ = LinearSVC(penalty="l1",
                                      dual=False, tol=1e-3)
        X = self.transformer_.fit_transform(X, y)
        return LinearSVC.fit(self, X, y)

    def decision_function(self, X):
        X = self.transformer_.transform(X)
        return LinearSVC.decision_function(self, X)

import nltk
class NLTKRegressor():
    def fit(self, X, y):
        # article_features = [
        #     (gen_feature(a), feature_map[a.last_action]) for a in last_1k_articles
        # ]
        labeled_sets = zip([
            {k: True for k in vec.nonzero()[1]} for vec in X
        ], y)
        self.classifier = nltk.NaiveBayesClassifier.train(labeled_sets)
        self.classes_ = [int(i) for i in self.classifier._labels]

    def predict_proba(self, X):
        result = []
        for vec in X:
            prob_dist = self.classifier.prob_classify({k: True for k in vec.nonzero()[1]})
            result.append([prob_dist.prob(s) for s in self.classes_])
            print(prob_dist._prob_dict)
        print(result, self.classes_)
        return result

class DummyRegressor():

    def fit(self, X, y):
        pass

    def predict(self, test):
        return [
            uniform(-1.0, 1.0) for i in test
        ]

results = []
for clf, name in (
        (DummyRegressor(), "Dummy"),
        (ProbClassifier(NLTKRegressor()), "NLTK"),
        (ProbClassifier(SVC(probability=True, kernel="linear")), "SVC"),
        (ProbClassifier(BernoulliNB(alpha=.1)), "nbb"),
        (ProbClassifier(MultinomialNB(alpha=.1)), "nbm"),
        # (LogisticRegression(), "LogisticRegression"),
        (PassiveAggressiveRegressor(), "PassiveAggressiveRegressor"),
        (SGDRegressor(loss="huber"), "SGDRegressor"),
        # (KNeighborsRegressor(weights="distance", n_neighbors=10), "KNeighborsRegressor"),
        (SVR(kernel="linear"), "SVR"),
        (NuSVR(kernel="linear"), "NuSVR"),
        ):
    print('=' * 80)
    print(name)
    results.append(benchmark(clf, name))

# for penalty in ["l2", "l1"]:
#     print('=' * 80)
#     print("%s penalty" % penalty.upper())
#     # Train Liblinear model
#     results.append(benchmark(LinearSVC(loss='l2', penalty=penalty,
#                                             dual=False, tol=1e-3)))

#     # Train SGD model
#     results.append(benchmark(SGDClassifier(alpha=.0001, n_iter=50,
#                                            penalty=penalty)))

# # Train SGD with Elastic Net penalty
# print('=' * 80)
# print("Elastic-Net penalty")
# results.append(benchmark(SGDClassifier(alpha=.0001, n_iter=50,
#                                        penalty="elasticnet")))

# # Train NearestCentroid without threshold
# print('=' * 80)
# print("NearestCentroid (aka Rocchio classifier)")
# results.append(benchmark(NearestCentroid()))

# # Train sparse Naive Bayes classifiers
# print('=' * 80)
# print("Naive Bayes")
# results.append(benchmark(MultinomialNB(alpha=.01)))
# results.append(benchmark(BernoulliNB(alpha=.01)))

# print('=' * 80)
# print("LinearSVC with L1-based feature selection")
# results.append(benchmark(L1LinearSVC()))


# make some plots

indices = np.arange(len(results))

results = [[x[i] for x in results] for i in range(4)]
print(results)

clf_names, score, training_time, test_time = results
training_time = np.array(training_time) / np.max(training_time)
test_time = np.array(test_time) / np.max(test_time)

plt.figure(figsize=(12, 8))
plt.title("Score")
plt.barh(indices, score, .2, label="score", color='r')
plt.barh(indices + .3, training_time, .2, label="training time", color='g')
plt.barh(indices + .6, test_time, .2, label="test time", color='b')
plt.yticks(())
plt.legend(loc='best')
plt.subplots_adjust(left=.25)
plt.subplots_adjust(top=.95)
plt.subplots_adjust(bottom=.05)

for i, c in zip(indices, clf_names):
    plt.text(-.3, i, c)

plt.show()