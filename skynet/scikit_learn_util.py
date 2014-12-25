from pandas import DataFrame
import numpy as np

def build_data_frame(article):
    return DataFrame({
        "last_action": [article.last_action],
        "article": [article],
    }, index=[article.id])


def gen_data_frame(data_set):
    result = DataFrame({"last_action": [], "article": []})
    for article in data_set:
        result = result.append(build_data_frame(article))

    return result.reindex(np.random.permutation(result.index))