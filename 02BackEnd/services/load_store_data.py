from langchain_weaviate.vectorstores import WeaviateVectorStore
#from preprocessing import get_vectorstore
from vectorstore import get_vectorstoremanager_instance
import requests

# Load Data function
def req_data_store(_url, _idx):
    
    params = {
    "class": _idx,  
    "limit": 500
    }
    response = requests.get(url, params)

    if response.status_code == 200:
        print('Done')
        return response.json()
    else:
        print(f"Failed to retrieve data: {response.status_code}")

# Not used
#def load_retriever_api_v1(_doc_idx, _k):
#    weaviate_client = get_weaviate_client()
#    vectorstore = get_vectorstore(weaviate_client, _doc_idx)
#    retriever = vectorstore.as_retriever(k=_k)  # (search_type="mmr")
#    return retriever, weaviate_client

# Not used
def load_data_retriever_api_v2():
    api_url = 'http://172.17.0.2:8080/v1/objects'
    raw_doc_idx   = 'LangChain_1d40505500e148f591bcca00bae6ed88'
    summ_doc_idx  = 'LangChain_751cf67395474a2da41a6bf0933ab0af'

    raw_response  = req_data_store(api_url, raw_doc_idx)
    summ_response = req_data_store(api_url, summ_doc_idx)

    raw_docs_cont = []
    raw_doc_ids = []

    for obj in raw_response.json()['objects']:
        doc_id = obj['properties']['doc_id']
        text = obj['properties']['text']
        
        raw_docs_cont.append(Document(metadata={'doc_id': doc_id}, page_content=text))
        raw_doc_ids.append(doc_id)

    summ_docs_cont = []

    for obj in summ_response.json()['objects']:
        doc_id = obj['properties']['doc_id']
        text = obj['properties']['text']
        
        summ_docs_cont.append(Document(metadata={'doc_id': doc_id}, page_content=text))

    store = InMemoryStore()
    id_key = "doc_id"

    # Init retriever
    multi_retriever = MultiVectorRetriever(
        vectorstore= get_vectorstoremanager_instance().get_vectorstore(summ_doc_idx),  
        byte_store=store, 
        id_key=id_key,  
        enable_limit=True,  
        search_kwargs={"k": 5}, 
    )

    # Set MultiRetriever
    converted_uuid_list = [uuid.UUID(item) for item in raw_doc_ids]
    multi_retriever.docstore.mset(list(zip(converted_uuid_list, raw_docs_cont))) 

    return  multi_retriever