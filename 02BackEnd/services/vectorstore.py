from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_weaviate.vectorstores import WeaviateVectorStore
from weaviate.connect import ConnectionParams
from weaviate.classes.init import AdditionalConfig, Timeout, Auth
import weaviate

# Weaviate VectorStorManager 클래스
class VectorStoreManager:
    _instance = None
    _vectorstore_cache = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VectorStoreManager, cls).__new__(cls)
            cls._instance.client = weaviate.WeaviateClient(
                connection_params=ConnectionParams.from_params(
                    http_host="172.17.0.2",  # 내부 IP
                    http_port=8080,
                    http_secure=False,
                    grpc_host="172.17.0.2",
                    grpc_port=50051,
                    grpc_secure=False,
                ),
                additional_config=AdditionalConfig(
                    timeout=Timeout(init=30, query=90, insert=120),
                )
            )
            # 클라이언트 연결 최초 1회
            cls._instance.client.connect()
        return cls._instance

    def get_client(self):
        return self.client

    def get_embeddings(self):
        # EmbeddingsManager에서 get.embeddings
        return get_embeddings_instance().get_embeddings()

    def get_vectorstore(self, _classname):
        # 벡터스토어 캐싱 처리
        if _classname not in self._vectorstore_cache:
            embeddings = self.get_embeddings()  # embeddings 호출
            self._vectorstore_cache[_classname] = WeaviateVectorStore(
                client=self.client,
                index_name=_classname,
                text_key='text',
                embedding=embeddings  
            )
        return self._vectorstore_cache[_classname]

    def load_retriever(self, _classname, _k):
        # 문서에 맞는 vectorstore 로드
        vectorstore = self.get_vectorstore(_classname)
        retriever = vectorstore.as_retriever(k=_k)
        return retriever

# 싱글턴 인스턴스
def get_vectorstoremanager_instance():
    return VectorStoreManager()

# Embeddings 관련 클래스 (Weaviate와 별도 관리)
class EmbeddingsManager:
    _instance = None
    _embeddings = None

    def __new__(cls, model="text-embedding-3-small"):
        if cls._instance is None:
            cls._instance = super(EmbeddingsManager, cls).__new__(cls)
            cls._instance._embeddings = OpenAIEmbeddings(model=model)  # user model 선언 가능
        return cls._instance

    def get_embeddings(self):
        return self._embeddings

# 싱글턴 인스턴스
def get_embeddings_instance(model="text-embedding-3-small"):
    return EmbeddingsManager(model)