from langgraph.graph import StateGraph ,START,END
from typing import TypedDict,Annotated ,Literal
import google.generativeai as genai
from pydantic import BaseModel,Field
import operator 
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from langchain_core.messages import BaseMessage, SystemMessage , HumanMessage 
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver   
import sqlite3    # memory save in ram by check pointer

load_dotenv()

## load model 
os.environ["GOOGLE_API_KEY"] = os.getenv("gen_api")

model = ChatGoogleGenerativeAI(model="gemini-2.5-flash-lite")


class chat_state(TypedDict):
    message : Annotated[list[BaseMessage], add_messages]
    
    
def chat_bot(state : chat_state):
    # prompt= SystemMessage(content=f"""you are a friendly bot chatting and answer the user query  """),
    # HumanMessage(content= f"""
    #              reply a user query on the bases of message that user give {state["message"]}
    #              """)
    message =state["message"]
    response = model.invoke(message)
    return {"message" : [response]}

conn=sqlite3.connect(database="chatbot.db", check_same_thread=False)

checkpointer = SqliteSaver(conn=conn)

graph= StateGraph(chat_state)

graph.add_node("chat_bot",chat_bot)

graph.add_edge(START,"chat_bot")
graph.add_edge("chat_bot",END)

chatbot = graph.compile(checkpointer=checkpointer)

all_thread_id=()
def all_thread():
    for checkpoint in checkpointer.list(None):
        all_thread_id = (checkpoint.config["configurable"]["thread_id"])
        return list(all_thread_id)
    
    
    
# CONFIG = {'configurable': {'thread_id':'thread-1'}}

# response= chatbot.invoke(
#                 {"message": [HumanMessage(content="tell me your self")]},
#                 config=CONFIG
#             )
# print (response)


# state = chatbot.get_state(config=CONFIG)
# messages = state.values["message"]

# first_user_message = None
# for m in messages:
#     if isinstance(m, HumanMessage):
#         first_user_message = m
#         break

# print (first_user_message.content)




