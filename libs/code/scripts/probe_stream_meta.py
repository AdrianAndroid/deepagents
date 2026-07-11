"""Print stream chunk metadata to see what LangGraph gives us."""
from __future__ import annotations
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, MessagesState

def call_model(state):
    llm = ChatOpenAI(
        model="ark-code-latest",
        base_url="https://ark.cn-beijing.volces.com/api/coding/v3",
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return {"messages": [llm.invoke(state["messages"])]}

g = StateGraph(MessagesState)
g.add_node("call", call_model)
g.set_entry_point("call")
g.set_finish_point("call")
app = g.compile()

for chunk, meta in app.stream(
    {"messages": [HumanMessage("hi")]},
    stream_mode="messages",
):
    print("META:", {k: v for k, v in meta.items() if not k.startswith("_")})
    print("MSG.response_metadata:", getattr(chunk, "response_metadata", None))
    print("---")
    break
