from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from vectorstore import get_vectorstoremanager_instance
from langchain import hub
import pprint

guide_doc_idx = 'LangChain_6e4361e2362640ec9b1b772fa130bc20'
api_doc_idx   = 'LangChain_9405daf90a3a4b83b150e3a543fb2dde'

def vectorstore_test():
    '''
    벡터스토어 연결 테스트 함수
    '''
    #vectorstore = get_vectorstoremanager_instance()
    #retriever_guide = vectorstore.load_retriever(guide_doc_idx, 5)
    #retriever_api = vectorstore.load_retriever(api_doc_idx, 5)

    weaviate_client = get_vectorstoremanager_instance().get_client()
    
    try:
        weaviate_client.connect()  
        if weaviate_client.is_ready():
            print("Connected to Weaviate!")
            
        else:
            print("Failed to connect to Weaviate.")
    except Exception as e:
        print(f"Error: {e}")
    weaviate_client.close()
    print('weaviate test ok')
    weaviate_client.close()
    print('closed weaviate')

def chain_test():
    '''
    retriever 연결 후 llm 호출 테스트 함수
    '''
    # 가이드 문서용 retriever
    vectorstore = get_vectorstoremanager_instance()
    retriever_guide = vectorstore.load_retriever(guide_doc_idx, 5)

    # API 문서용 retriever
    retriever_api = vectorstore.load_retriever(api_doc_idx, 5)
    prompt = hub.pull("rlm/rag-prompt")

    #llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
    llm = ChatOpenAI(temperature=0, model="gpt-4o")

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    rag_chain = (
        {"context": retriever_api | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    #question = 'LoA 3의 인증 요구사항은?'
    #question = '생성주체구분코드에서 C는 무엇을 뜻하는가?'
    #question = "x-api-tran-id에 대해 알려주세요"
    #question = '데이터 타입 중 aNS는 어떤 것을 뜻하나요'  # 160.p 표
    question = ' API 스펙 중 aNS는 어떤 것을 뜻하나요?' #  표
    response = rag_chain.invoke(question)
    print(response)

def workflow_test():
    app_workflow = get_workflow()

    inputs = {
        "messages": [
            HumanMessage(
                content="정보 전송 요구 연장은 언제 가능한가요?"
            )
        ]
    }
    for output in app_workflow.stream(inputs):
        for key, value in output.items():
            pprint.pprint(f"Output from node '{key}':")
            pprint.pprint("---")
            pprint.pprint(value, indent=2, width=80, depth=None)
        pprint.pprint("\n---\n")

def draw_workflow():
    '''
    Draw graph to png
    '''
    graph = get_workflow()
    from IPython.display import Image, display
    import os
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
    
    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    try:
        chain_test()
        #vectorstore_test()
        #workflow_test()
        #draw_workflow()
    except Exception as e:
        print('=== __main__ error ===')
        print(e)
        print('======================')
    finally:
        get_vectorstoremanager_instance().get_client().close()
        