import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_pinecone import PineconeVectorStore

from langchain.schema.runnable import RunnablePassthrough


def format_docs(docs):
    return "\n\n".join([doc.page_content for doc in docs])


load_dotenv("../../.env.development")


if __name__ == "__main__":
    print("Retrieving 시작")

    embeddings = OpenAIEmbeddings()
    llm = ChatOpenAI()

    # todo: 우리 서비스에 맞는 쿼리로 나중에 바꾸기 (제공된 유저 정보를 바탕으로 가장 적합한 공고를 최대 5개 추천하기. 추천의 조건은 다음과 같음 어쩌구저쩌구)
    query = "파이크에 가장 잘 어울리는 아군 원딜러는?"

    vectorstore = PineconeVectorStore(
        index_name=os.environ.get("INDEX_NAME"),
        embedding=embeddings,
    )

    template = """
    다음 맥락을 활용하여 마지막 질문에 답하세요. 답을 모른다면 그냥 모른다고 말하고, 지어내려고 하지 마세요.
    항상 한국어로 응답하세요.

    {context}

    Question: {question}

    Helpful Answer:
    """

    custom_rag_prompt = PromptTemplate.from_template(template=template)

    rag_chain = (
            {"context": vectorstore.as_retriever() | format_docs, "question": RunnablePassthrough()}
            | custom_rag_prompt
            | llm
    )

    result = rag_chain.invoke(query)
    print(result.content)



