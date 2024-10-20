from qdrant_client import QdrantClient
from qdrant_client import models
import cohere

from keys import QDRANT_API_TOKEN

co = cohere.Client('ACkNOOGu5ukthcUA6tyT7QjMMKyn9iNxfuB7RYgd')

qdrant_client = QdrantClient(
    url="https://8c281bb8-d969-461b-bc4f-dfea29aa22bb.us-east4-0.gcp.cloud.qdrant.io:6333",
    api_key=QDRANT_API_TOKEN,
)


def fetch_results(query_vector, filters):
    must = [
        models.FieldCondition(key="ratings",
                              range=models.Range(gte=filters['ratings'][0],
                                                 lte=filters['ratings'][1])),
        models.FieldCondition(key="actual_price",
                              range=models.Range(gte=filters['actual_price'][0],
                                                 lte=filters['actual_price'][
                                                     1]))
    ]
    if len(filters['must']) > 0:
        for k in filters['must']:
            must.append({"key": "name", "match": {"text": k.capitalize()}})
            must.append({"key": "name", "match": {"text": k}})

    must_not = []
    if len(filters['must_not']) > 0:
        for k in filters['must_not']:
            must_not.append({"key": "name", "match": {"text": k.capitalize()}})
            must_not.append({"key": "name", "match": {"text": k}})
    print(must)
    print(must_not)
    result = qdrant_client.query_points(collection_name="amazon_product",
                                        query=query_vector,
                                        query_filter=models.Filter(
                                            must=must,
                                            must_not=must_not,
                                        ),
                                        limit=500).points
    return [r.payload for r in result]


def rerank(query, data):
    p = list(filter(lambda x: x != "", [d['name'] for d in data]))
    results = co.rerank(query=query, documents=p, top_n=5, model='rerank-english-v3.0')
    return [data[results.results[i].index] for i in range(len(results.results))]
