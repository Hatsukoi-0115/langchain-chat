import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

# 初始化模型
llm = ChatOpenAI(
    model = "gpt-4o-mini",
    api_key = os.getenv("OPENAI_API_KEY"),
    base_url = os.getenv("OPENAI_BASE_URL"),
)

# Prompt 模板
prompt = ChatPromptTemplate.from_template(
    "请解释：{topic}"
)

# 创建 Chain
chain = prompt | llm

# 调用
result = chain.invoke({
    "topic": "什么是 Transformer"
})
# response = llm.invoke("你好")

print(result.content)