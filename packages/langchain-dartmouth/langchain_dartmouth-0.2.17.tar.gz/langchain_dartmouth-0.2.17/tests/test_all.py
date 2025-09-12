import os

import pytest

from langchain_dartmouth.llms import (
    DartmouthLLM,
    ChatDartmouth,
    DartmouthChatModel,
    ChatDartmouthCloud,
)
from langchain_dartmouth.embeddings import DartmouthEmbeddings
from langchain_dartmouth.exceptions import InvalidKeyError, ModelNotFoundError
from langchain_dartmouth.cross_encoders import TextEmbeddingInferenceClient
from langchain_dartmouth.retrievers.document_compressors import (
    TeiCrossEncoderReranker,
    DartmouthReranker,
)

from langchain.docstore.document import Document
from langchain.schema import SystemMessage, HumanMessage

from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


def test_dartmouth_llm():
    llm = DartmouthLLM()
    response = llm.invoke("Write a Python script to swap the values of two variables")
    assert response

    assert len(DartmouthLLM.list()) > 0


def test_dartmouth_llm_list():
    llms = DartmouthLLM.list()
    assert len(llms) > 0


def test_chat_dartmouth():
    llm = ChatDartmouth(model_name="llama-3-8b-instruct")
    response = llm.invoke("Please respond with the single word OK")
    assert response.content.strip() == "OK"

    llm = ChatDartmouth(model_name="llama-3-1-8b-instruct")
    response = llm.invoke(
        [
            SystemMessage(content="You are a cat."),
            HumanMessage(content="What is your name?"),
        ]
    )
    assert response.content


def test_chat_dartmouth_headers():
    llm = ChatDartmouth(model_name="llama-3-1-8b-instruct")
    response = llm.invoke(
        [
            HumanMessage(content="What is your name?"),
        ]
    )
    assert response.response_metadata["headers"]


def test_chat_dartmouth_list():
    llms = ChatDartmouth.list()
    assert len(llms) > 0


@pytest.mark.parametrize(
    "model_name",
    [
        "default",
    ]
    + [model["name"] for model in ChatDartmouthCloud.list()],
)
def test_chat_dartmouth_cloud(model_name):

    kwargs = dict()
    if model_name == "default":
        llm = ChatDartmouthCloud()
    else:
        if "gemini-2.5" in model_name.lower():
            # Gemini reasoning models with default settings often need too many tokens for reasoning to produce output
            llm = ChatDartmouthCloud(model_name=model_name, max_tokens=1024)
            kwargs = {"reasoning_effort": "low"}
        else:
            llm = ChatDartmouthCloud(model_name=model_name)

    response = llm.invoke("Ping", **kwargs)
    assert len(response.content) > 0


def test_chat_dartmouth_cloud_url():
    DEV_URL = "https://chat-dev.dartmouth.edu/api/"
    DEV_KEY = os.environ.get("DARTMOUTH_CHAT_DEV_API_KEY")
    if DEV_KEY is None:
        pytest.skip("No DARTMOUTH_CHAT_DEV_API_KEY available.")
    model = "anthropic.claude-3-7-sonnet-20250219"
    llm = ChatDartmouthCloud(
        model_name=model,
        inference_server_url=DEV_URL,
        dartmouth_chat_api_key=DEV_KEY,
    )
    response = llm.invoke("Are you there? Answer yes or no.")
    assert "yes" in response.content.lower()


def test_chat_dartmouth_cloud_headers():
    model = "anthropic.claude-3-7-sonnet-20250219"
    llm = ChatDartmouthCloud(model_name=model)
    response = llm.invoke("Are you there? Answer yes or no.")
    assert response.response_metadata["headers"]


def test_dartmouth_llm_bad_name():
    llm = DartmouthLLM(model_name="Bad name")

    with pytest.raises(ModelNotFoundError):
        llm.invoke("Who are you?")


def test_chat_dartmouth_bad_name():
    llm = ChatDartmouth(model_name="Bad name")

    with pytest.raises(ModelNotFoundError):
        llm.invoke("Who are you?")


def test_chat_dartmouth_bad_key():
    with pytest.raises(InvalidKeyError):
        ChatDartmouth(dartmouth_api_key="Bad")


def test_chat_dartmouth_cloud_bad_name():
    llm = ChatDartmouthCloud(model_name="Bad name")

    with pytest.raises(ModelNotFoundError):
        llm.invoke("Who are you?")


def test_chat_dartmouth_cloud_bad_key():
    llm = ChatDartmouthCloud(dartmouth_chat_api_key="Bad")

    with pytest.raises(InvalidKeyError):
        llm.invoke("Who are you?")


def test_chat_dartmouth_cloud_list():
    llms = ChatDartmouthCloud.list()
    assert len(llms) > 0


def test_litellm_model_list():
    models = ChatDartmouthCloud.list(
        dartmouth_chat_api_key=os.environ["LITELLM_TEAM_API_KEY"],
        url=os.environ["LITELLM_BASE_URL"],
        base_only=False,
    )
    # There should only be three models available to this team
    assert len(models) == 3


def test_dartmouth_chat():
    llm = DartmouthChatModel(model_name="codellama-13b-instruct-hf")
    response = llm.invoke("<s>[INST]Please respond with the single word OK[/INST]")
    assert response.strip() == "OK"

    llm = DartmouthChatModel(
        inference_server_url="https://ai-api.dartmouth.edu/tgi/codellama-13b-instruct-hf/",
    )
    print(llm.invoke("<s>[INST]Hello[/INST]"))


def test_streaming():
    chunks = []
    for chunk in ChatDartmouthCloud(seed=42).stream("Hi there!"):
        chunks.append(chunk)
    assert len(chunks) > 0


def test_dartmouth_embeddings():
    embeddings = DartmouthEmbeddings()
    result = embeddings.embed_query("Is there anybody out there?")
    assert result

    assert len(DartmouthEmbeddings.list()) > 0


def test_dartmouth_reranker():
    docs = [
        Document(page_content="Deep Learning is not..."),
        Document(page_content="Deep learning is..."),
    ]
    query = "What is Deep Learning?"
    reranker = DartmouthReranker()
    ranked_docs = reranker.compress_documents(query=query, documents=docs)
    assert ranked_docs

    reranker = DartmouthReranker(top_n=1)
    ranked_docs = reranker.compress_documents(query=query, documents=docs)
    assert len(ranked_docs) == 1

    assert len(DartmouthReranker.list()) > 0


@pytest.mark.skip(reason="Needs a locally running instance of TEI")
def test_tei_reranker():
    docs = [
        Document(page_content="Deep Learning is not..."),
        Document(page_content="Deep learning is..."),
    ]
    query = "What is Deep Learning?"
    cross_encoder = TeiCrossEncoderReranker()
    ranked_docs = cross_encoder.compress_documents(query=query, documents=docs)

    assert ranked_docs


@pytest.mark.skip(reason="Needs a locally running instance of TEI")
def test_tei_client():
    query = "What is Deep Learning?"
    texts = [
        "Deep Learning is not...",
        "Deep learning is...",
    ]
    tei_client = TextEmbeddingInferenceClient()
    scores = tei_client.rerank(query=query, texts=texts)

    assert scores


if __name__ == "__main__":
    models = ChatDartmouthCloud.list()
    # test_dartmouth_llm()
    # test_chat_dartmouth()
    # test_chat_dartmouth_cloud()
    # test_dartmouth_chat()
    # test_dartmouth_embeddings()
    # test_dartmouth_reranker()
    # test_tei_client()   # requires locally running instance of vanilla TEI
    # # test_tei_reranker()  # requires locally running instance of vanilla TEI
