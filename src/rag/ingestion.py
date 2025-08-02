import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore


load_dotenv("../../.env.development")


# 벡터 데이터베이스에 문서를 넣는 코드

if __name__ == "__main__":
    print("ingesting 시작")


    # todo: 나중에 크롤링 문서 가져온 것으로 바꿔넣어야함
    loader = TextLoader("pike_compatibility.txt")
    documents = loader.load()


    print("문서 분할 시작")
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(documents)
    embeddings = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))


    # todo: 추후 추천로직 정확도 향상을 위해 파인콘 메타데이터 기능 알아보고 적용
    print("파인콘 벡터디비에 문서 벡터임베딩해 저장 시작")
    PineconeVectorStore.from_documents(
        texts,
        embeddings,
        index_name=os.environ.get("INDEX_NAME")
    )
    print("ingestion 완료")
