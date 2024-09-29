from llama_parse import LlamaParse
from llama_index.core import SimpleDirectoryReader
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import InMemoryStore
from langchain_weaviate.vectorstores import WeaviateVectorStore
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
from openai import OpenAI
import weaviate, nest_asyncio, uuid, os, re
from dotenv import load_dotenv
from vectorstore import get_vectorstoremanager_instance, get_embeddings_instance

load_dotenv()
nest_asyncio.apply()
embeddings = get_embeddings_instance().get_embeddings()
weaviate_client = get_vectorstoremanager_instance().get_client()

def summarize_content_with_llm(content):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    message = [{'role': 'user', 'content': f'''
    다음 내용을 한국어로 간략하게 요약해 주세요. 
    마크다운 형식의 표가 있을 경우 각 행에 있는 모든 내용을 요약하지 말고, 필요한 설명부분만 참고하고 헤더 정보를 바탕으로 표의 역할을 요약해주세요.
    :\n\n{content}
    '''}]

    completion = client.chat.completions.create(
        model='gpt-4o',  
        messages=message
    )
    
    response_text = completion.choices[0].message.content.strip()
    return response_text

def get_llama_parse(_parsing_instruction):
    parser = LlamaParse(
        use_vendor_multimodal_model=True,
        vendor_multimodal_model_name="openai-gpt4o",
        vendor_multimodal_api_key=os.getenv("OPENAI_API_KEY"),
        result_type="markdown",
        language="ko",
        parsing_instruction=_parsing_instruction,
        )
    return parser

def preprocess_data_guide():
    """
    Preprocess data
    """
    print("데이터 전처리 작업 수행 중...")

    parser = get_llama_parse("You are parsing a manual of MyData Guide. Please extract tables and images in markdown format.")
    parsed_docs = parser.load_data(file_path="data/(221115 수정배포) (2022.10) 금융분야 마이데이터 기술 가이드라인.pdf")
    langchain_docs = [doc.to_langchain_format() for doc in parsed_docs]
    
    headers_to_split_on = [ 
    (
        "#",
        "Header_1",
    ),  
    (
        "##",
        "Header_2",
    ),  
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    replace_phrases = [
    "# 금융분야 마이데이터 기술 가이드라인",
    "# 금융분야 마이데이터 가이드라인",
    "# 1장. 개요",
    "# 2장. 개인신용정보 전송",
    "# 3장. 마이데이터서비스",
    "# 4장. 마이데이터 본인인증",
    "# 5장. 마이데이터 보안",
    "# 6장: Q&A",
    "# 6장. Q&A",
    "# 7장. 참고"
    ]
    pattern = re.compile('|'.join(re.escape(phrase) for phrase in replace_phrases))

    split_docs = []
    for doc in langchain_docs:
        # 정규표현식
        doc.page_content = re.sub(pattern, "", doc.page_content).strip()
        split_docs += markdown_splitter.split_text(doc.page_content)
    
    #print('split_docs: ', split_docs[0:300])

    try:
        weaviate_client.connect()  
        if weaviate_client.is_ready():
            print("Connected to Weaviate!")
            raw_vectorstore = WeaviateVectorStore.from_documents(
            split_docs, embeddings, client=weaviate_client, class_name="guide"
            )
            print("Saved 'guide'")
        else:
            print("Failed to connect to Weaviate.")
    except Exception as e:
        print(f"Error: {e}")

    weaviate_client.close()
    return "Done 'preprocess_data_guide'"

def preprocess_data_api_v1():
    """
    Preprocess data
    """
    print("데이터 전처리 작업 수행 중...")
    
    parser = get_llama_parse("You are parsing a manual of MyData API. Please extract tables and images in markdown format.")
    parsed_docs = parser.load_data(file_path="data/(수정게시) 금융분야 마이데이터 표준 API 규격 v1.pdf")

    langchain_docs = [doc.to_langchain_format() for doc in parsed_docs]

    headers_to_split_on = [ 
    (
        "#",
        "Header_1",
    ),  
    (
        "##",
        "Header_2",
    ),  
    #    (
    #        "###",
    #        "Header_3",
    #    ),  
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on,
        strip_headers=False,
    )

    replace_phrases = [
    "# 금융분야 마이데이터 표준API 규격"
    ]
    pattern = re.compile('|'.join(re.escape(phrase) for phrase in replace_phrases))

    split_docs = []
    for doc in langchain_docs:
        doc.page_content = re.sub(pattern, "", doc.page_content).strip()
        split_docs += markdown_splitter.split_text(doc.page_content)

    try:
        weaviate_client.connect()  
        if weaviate_client.is_ready():
            print("Connected to Weaviate!")
            
            raw_vectorstore = WeaviateVectorStore.from_documents(
            split_docs, embeddings, client=weaviate_client, class_name="api"
            )

            print("Saved 'api'")
        else:
            print("Failed to connect to Weaviate.")
    except Exception as e:
        print(f"Error: {e}")

    weaviate_client.close()
    return "Done 'preprocess_data_api_v1'"

def preprocess_data_api_v2():
    """
    Preprocess data
    """
    print("데이터 전처리 작업 수행 중...")
    
    parser = get_llama_parse("You are parsing a manual of MyData API. Please extract tables and images in markdown format.")
    parsed_docs = parser.load_data(file_path="data/(수정게시) 금융분야 마이데이터 표준 API 규격 v1.pdf")

    langchain_docs = [doc.to_langchain_format() for doc in parsed_docs]

    headers_to_split_on2 = [  
        (
            "#",
            "Header_1",
        ),  
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on2,
        strip_headers=False,
    )

    split_docs_1d = []
    for doc in langchain_docs:        
        doc.page_content = doc.page_content.replace("# 금융분야 마이데이터 표준API 규격", "").strip()
        split_content = markdown_splitter.split_text(doc.page_content)
        for content in split_content:
            tmp_doc = Document(
                page_content=content.page_content,
                metadata={**doc.metadata, 'doc_id': str(uuid.uuid4())}  # 기존 metadata에 'doc_id' 추가
            )
            split_docs_1d.append(tmp_doc)
    
    docs_id = []
    summary_docs = []
    for i, doc in enumerate(split_docs_1d):
        try:
            summary_docs.append(Document(page_content=summarize_content_with_llm(doc.page_content), metadata={id_key: doc.metadata['doc_id']}))
            docs_id.append(doc.metadata['doc_id'])
        except:
            print('err')
    
    # doc_ids, split_docs1d, summary_docs 길이 확인 권장
    try:
        weaviate_client.connect()  
        if weaviate_client.is_ready():
            print("Connected to Weaviate!")
            
            raw_vectorstore = WeaviateVectorStore.from_documents(
            split_docs_1d, embeddings, client=weaviate_client, class_name="raw_cont"
            )

            summary_vectorstore = WeaviateVectorStore.from_documents(
            summary_docs, embeddings, client=weaviate_client, class_name="summ_cont"
            )
            print("Saved 'raw_docs' and 'summary_docs'")
        else:
            print("Failed to connect to Weaviate.")
    except Exception as e:
        print(f"Error: {e}")

    weaviate_client.close()
    return "Done 'preprocess_data_api_v2'"

