import os
from ..utils import env_loader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough


class RAGEngine:
    def __init__(self, index_type="default"):
        # llm 객체, 임베딩 객체 초기화
        env = env_loader.load_env_config("development")
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))
        self.llm = ChatOpenAI()
        
        # 객체 초기화때 인자로 받는 index_type에 따라 다른 벡터DB 인덱스명 사용
        self.index_name = (
            os.environ.get("CHATBOT_INDEX_NAME") if index_type == "chatbot" 
            else os.environ.get("INDEX_NAME")
        )
        
        self.namespace = os.environ.get("PINECONE_NAMESPACE", "")

        # 텍스트 분할기 설정
        self.text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)

        # 벡터스토어, rag 체인 (나중에 초기화)
        self.vectorstore = None
        self.rag_chain = None

        # 프롬프트 세팅 메서드 실행
        self._setup_prompt_template()

    def _setup_prompt_template(self):
        """프롬프트 템플릿 설정"""
        template = """
        Question: {question}

        {context}

        Helpful Answer:
        """
        self.custom_rag_prompt = PromptTemplate.from_template(template=template)

    def _format_docs(self, docs):
        """문서 포맷팅 함수"""
        return "\n\n".join([doc.page_content for doc in docs])

    def _initialize_vectorstore(self):
        if self.vectorstore is None:
            self.vectorstore = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=self.namespace, 
            )

    def _initialize_rag_chain(self):
        if self.rag_chain is None:
            self._initialize_vectorstore()
            self.rag_chain = (
                    {"context": self.vectorstore.as_retriever() | self._format_docs, "question": RunnablePassthrough()}
                    | self.custom_rag_prompt
                    | self.llm
            )


    def ingest_documents(self, file_path):
        """
        문서를 벡터 데이터베이스에 저장

        Args:
            file_path (str): 처리할 문서 파일 경로
        """
        print("ingesting 시작")

        try:
            loader = TextLoader(file_path)
            documents = loader.load()

            texts = self.text_splitter.split_documents(documents)

            PineconeVectorStore.from_documents(
                texts,
                self.embeddings,
                index_name=self.index_name,
                namespace=self.namespace,
            )
            print("ingestion 완료")

        except Exception as e:
            print(f"ingestion 중 오류 발생: {e}")
            raise
    
    def retrieve_policy_ids(self, query: str, k: int = 10, topn: int = 5) -> list[str]:
        """
        질의(query)에 대해 벡터스토어에서 유사 문서를 검색한 뒤,
        검색 결과 문서들의 metadata에서 정책 ID(policy_id)만 추출하여 반환한다.

        Args:
            query (str): 검색할 사용자 질의.
            k (int, optional): 벡터스토어에서 가져올 유사 문서 개수. 기본값은 10.
            topn (int, optional): 최종적으로 반환할 고유한 정책 ID의 최대 개수. 기본값은 5.

        Returns:
            list[str]: 중복되지 않는 정책 ID 문자열 리스트.
                      (metadata에 policy_id가 없으면 id 필드를 대신 사용)
        """
        self._initialize_vectorstore()
        docs = self.vectorstore.similarity_search(query, k=k, namespace=self.namespace)
        ids: list[str] = []
        for d in docs:
            meta = getattr(d, "metadata", {}) or {}
            pid = meta.get("policy_id") or meta.get("id")
            if pid and pid not in ids:
                ids.append(pid)
            if len(ids) >= topn:
                break
        return ids


    def retrieve_answer(self, query):
        """
        질의에 대한 답변 검색 및 생성

        Args:
            query (str): 사용자 질의

        Returns:
            str: 생성된 답변
        """
        print("Retrieving 시작")

        try:
            # RAG 체인 초기화 (처음 호출시에만)
            self._initialize_rag_chain()

            result = self.rag_chain.invoke(query)
            return result.content

        except Exception as e:
            print(f"retrieval 중 오류 발생: {e}")
            raise
