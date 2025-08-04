import os
from ..utils import env_loader
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough


class RAGEngine:
    def __init__(self):

        env = env_loader.load_env_config("development")

        # 임베딜, llm, 인덱스명 가져와서 한번만 초기화(싱글톤느낌)
        self.embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))
        self.llm = ChatOpenAI()
        self.index_name = os.environ.get("INDEX_NAME")

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
        다음 맥락을 활용하여 마지막 질문에 답하세요. 답을 모른다면 그냥 모른다고 말하고, 지어내려고 하지 마세요.
        항상 한국어로 응답하세요.

        {context}

        Question: {question}

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
            )

    def _initialize_rag_chain(self):
        if self.rag_chain is None:
            self._initialize_vectorstore()
            self.rag_chain = (
                    {"context": self.vectorstore.as_retriever() | self._format_docs,
                     "question": RunnablePassthrough()}
                    | self.custom_rag_prompt
                    | self.llm
            )

    # 크롤링에서 써야함
    # todo: 추후 크롤링 문서 가져온 것으로 바꿔넣어야함
    # todo: 추후 추천로직 정확도 향상을 위해 파인콘 메타데이터 기능을 알아보고 크롤링 로직에 적용시켜야함
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

            print("문서 분할 시작")
            texts = self.text_splitter.split_documents(documents)

            print("파인콘 벡터디비에 문서 벡터 임베딩해 저장 시작")
            PineconeVectorStore.from_documents(
                texts,
                self.embeddings,
                index_name=self.index_name
            )
            print("ingestion 완료")

        except Exception as e:
            print(f"ingestion 중 오류 발생: {e}")
            raise

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

            # (제공된 유저 정보를 바탕으로 가장 적합한 공고를 최대 5개 추천하기)
            result = self.rag_chain.invoke(query)
            return result.content

        except Exception as e:
            print(f"retrieval 중 오류 발생: {e}")
            raise


