def jaccard_similarity(text1: list[str], text2: list[str]):
    """Returns the jaccard similarity between two lists """
    intersection_cardinality = len(set.intersection(*[set(text1), set(text2)]))
    union_cardinality = len(set.union(*[set(text1), set(text2)]))
    return intersection_cardinality/float(union_cardinality)
