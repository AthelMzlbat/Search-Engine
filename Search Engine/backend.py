from inverted_index_gcp import *
from start import *
import re
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')

english_stopwords = frozenset(stopwords.words('english'))

# FROM GCP FOR THE SEARCH BODY PART
corpus_stopwords = ["category", "references", "also", "external", "links",
                    "may", "first", "see", "history", "people", "one", "two",
                    "part", "thumb", "including", "second", "following",
                    "many", "however", "would", "became"]

all_stopwords = english_stopwords.union(corpus_stopwords)


def Corpus_Tokenizer(text, method='norm'):
    """"
    we wanted to add stemming and lemmatization hence the method='norm'
    """

    RE_WORD = re.compile(r"""[\#\@\w](['\-]?\w){2,24}""", re.UNICODE)
    tokens = [token.group() for token in RE_WORD.finditer(text.lower())]
    if method == 'norm':
        return [token for token in tokens if token not in all_stopwords]


def get_binary(query, inv_idx, bucket_name, folder_name):
    """
    Function to binary search in indices (for either anchor or title retrieval)
    :param query:  query to tokenize and search
    :param inv_idx: inverted index to binary search in
    :param bucket_name : str , name of the bucket
    :param folder_name : str, name of the folder that contains the indices
    :return: list of relevant documents  , sorted by query tokens matches
    """
    tokens = Corpus_Tokenizer(query)
    return_dict = {}
    for tok in tokens:
        try:
            res = read_posting_list(inv_idx, bucket_name, tok, folder_name)
            for doc_id, _ in res:
                try:
                    return_dict[doc_id] += 1
                except:
                    return_dict[doc_id] = 1
        except Exception as e:
            print('Error in Anchor/Title index occurred - ', e)
    return sorted(return_dict, key=return_dict.get, reverse=True)


def text_title_Merge(query, text_idx, text_n_docs, text_avg_doc, title_idx, title_n_docs, title_avg_doc, N=200):
    """
    receives a query and runs it on text and title indices.
    returns a merged list of docs - based on BM25 score of each index and pre-determined weights.
    :param query: string, query to tokenize and search.
    :param text_idx : inverted index of text.
    :param text_n_docs : int, number of docs in text
    :param text_avg_doc : float , average length of doc in text index.
    :param title_idx : inverted index of title
    :param title_n_docs : int, number of docs in title.
    :param title_avg_doc : float , average length of title docs.
    :param N : int, amount to return
    :returns : list of doc_id . sorted by combined tf-idf scores and weights.
    """
    text_weight = 0.8
    title_weight = 0.22
    bucket_name = "208593988"
    folder_text = "postingText"
    folder_title = "postings_title"

    tokens = Corpus_Tokenizer(query)
    text_docs = opt_BM25_for_joint(tokens, text_idx, text_n_docs, text_avg_doc, bucket_name, folder_text, N=N)
    title_docs = opt_BM25_for_joint(tokens, title_idx, title_n_docs, title_avg_doc, bucket_name, folder_title, N=N)
    doc_dict = {}
    for doc, score in text_docs:
        doc_dict[doc] = text_weight * score
    for doc, score in title_docs:
        if doc not in doc_dict.keys():
            doc_dict[doc] = title_weight * score
        else:
            doc_dict[doc] += title_weight * score
    result = sorted(doc_dict, key=doc_dict.get, reverse=True)
    return result


def get_IR(q_text, index, corpus_docs, avg_dl, bucket_name, folder_name, N=100, opt='HW'):
    """
    Function that retrieves top N files matching each query according to TFIDF, BM25, and cosine similarity.
    :param q_text: free text of query
    :param index: inverted index to search in
    :param N: top number of documents to retrieve
    :param corpus_docs : int , optimization - number of docs in corpus
    :param avg_dl : float, optimization - average document size in corpus
    :param bucket_name : str , name of the bucket
    :param folder_name : str, name of the folder that contains the indices
    :param opt: differentiate between naive (homework pipe and optimized)
    :return: list of docs id, sorted by rank
    """
    q_tokens = list(set(Corpus_Tokenizer(q_text)))

    if opt == 'HW':
        ret = OPT_Tfidf(q_tokens, index, bucket_name, folder_name, corpus_docs, N)
        return ret

    if opt == 'opt':
        ret = opt_BM25(q_tokens, index, bucket_name, folder_name, corpus_docs, avg_dl, N)
        return ret

    if opt == 'cos':
        ret = OPT_Cosine(q_tokens, index, bucket_name, folder_name, N=100)
        return ret
