from base.models import Article
from base.database import db_session

from skynet.nlp_util import gen_feature

import nltk

feature_map = {
    'defer': 1,
    'like': 1,
    'dislike': 1,
    'pass': 0,
}

def show_prob(prob):
    return {
        k: prob.prob(k) for k in prob.samples()
    }

def learn(user_id):
    last_1k_articles = (
        db_session
        .query(Article)
        .filter(Article.last_action != None)
        .filter_by(user_id=user_id)
        .order_by(Article.last_action_timestamp.desc())
        .limit(1000)
        .all()
    )

    if not last_1k_articles:
        return

    article_features = [
        (gen_feature(a), feature_map[a.last_action]) for a in last_1k_articles
    ]

    import random
    # random.shuffle(article_features)
    train_size = len(article_features) * 9 / 10

    train_set = article_features[:train_size]
    test_set = article_features[train_size:]

    classifier = nltk.NaiveBayesClassifier.train(train_set)

    print classifier.most_informative_features()
    for ind, t in enumerate(test_set):
        c = classifier.classify(t[0])
        if t[1] != c and t[1] == 1:
            print t, show_prob(classifier.prob_classify(t[0]))
            print last_1k_articles[train_size + ind].title.encode('utf-8')
    return nltk.classify.accuracy(classifier, test_set)

times = 1
t = 0
for i in xrange(times):
    t += learn(1)
print t / times