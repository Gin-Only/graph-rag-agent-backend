from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_aiter import AsyncIteratorCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from langchain_community.chat_models import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

def get_embeddings_model():
    # model = DashScopeEmbeddings(
    #     model="text-embedding-v2",#os.getenv('OPENAI_EMBEDDINGS_MODEL'),
    #     api_key="sk-f2c1966eccb14a5ebf015261f49ff9e3",#os.getenv('OPENAI_API_KEY'),
    #     base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"#os.getenv('OPENAI_BASE_URL'),
    # )
    model = DashScopeEmbeddings(
        model="text-embedding-v2",
        dashscope_api_key="sk-f2c1966eccb14a5ebf015261f49ff9e3",
    )
    return model


def get_llm_model():
    model = ChatTongyi(
        model="qwen-plus",#os.getenv('OPENAI_LLM_MODEL'),
        temperature=os.getenv('TEMPERATURE'),
        max_tokens=os.getenv('MAX_TOKENS'),
        api_key="sk-f2c1966eccb14a5ebf015261f49ff9e3",#os.getenv('OPENAI_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"#os.getenv('OPENAI_BASE_URL'),
    )
    return model

def get_stream_llm_model():
    callback_handler = AsyncIteratorCallbackHandler()
    # 将回调handler放进AsyncCallbackManager中
    manager = AsyncCallbackManager(handlers=[callback_handler])

    model = ChatTongyi(
        model="qwen-plus",#os.getenv('OPENAI_LLM_MODEL'),
        temperature=os.getenv('TEMPERATURE'),
        max_tokens=os.getenv('MAX_TOKENS'),
        api_key="sk-f2c1966eccb14a5ebf015261f49ff9e3",#os.getenv('OPENAI_API_KEY'),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",#os.getenv('OPENAI_BASE_URL'),
        streaming=True,
        callbacks=manager,
    )
    return model

if __name__ == '__main__':
    # 测试llm
    # llm = get_llm_model()
    # print(llm.invoke("你好"))

    # # # # 由于langchain版本问题，这个目前测试会报错
    llm_stream = get_stream_llm_model()
    print(llm_stream.invoke("你好"))

    # # 测试embedding
    # test_text = "你好，这是一个测试。"
    # embeddings = get_embeddings_model()
    # print(len(embeddings.embed_query(test_text)))