#!/usr/bin/env python
"""Complete BakeryAI API with multiple endpoints"""

import os
from typing import List
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from langserve import add_routes

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from pydantic import BaseModel, Field
import pandas as pd
from datetime import datetime, timedelta
from operator import itemgetter

load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="BakeryAI Complete API",
    version="2.0",
    description="Full-featured BakeryAI with RAG, agents, and tools"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
llm = ChatOpenAI(model="gpt-4o")
embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

# Load vector store (if available)
try:
    vectorstore = FAISS.load_local(
        "bakery_faiss_index",
        embeddings,
        allow_dangerous_deserialization=True
    )
    print("✅ Loaded vector store")
except:
    vectorstore = None
    print("⚠️  No vector store found")

# ============================================================
# ENDPOINT 1: Simple Chat
# ============================================================
chat_prompt = ChatPromptTemplate.from_template(
    "You are a helpful bakery assistant. Answer: {question}"
)
chat_chain = chat_prompt | llm | StrOutputParser()

add_routes(app, chat_chain, path="/chat")

# ============================================================
# ENDPOINT 2: RAG Question Answering
# ============================================================
class RagInput(BaseModel):
    question: str

if vectorstore:
    retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
    
    rag_prompt = ChatPromptTemplate.from_template("""
    Answer based on this context:
    
    {context}
    
    Question: {question}
    
    Answer:
    """)
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {
            "context": itemgetter("question") | retriever | format_docs,
            "question": itemgetter("question")
        }
        | rag_prompt
        | llm
        | StrOutputParser()
    )
    
    add_routes(
        app,
        rag_chain.with_types(input_type=RagInput),
        path="/rag"
    )

# ============================================================
# ENDPOINT 3: Product Recommendations
# ============================================================
class RecommendationInput(BaseModel):
    occasion: str = Field(description="The occasion")
    preferences: str = Field(description="Customer preferences")

recommendation_prompt = ChatPromptTemplate.from_template("""
Recommend a cake for:
Occasion: {occasion}
Preferences: {preferences}

Provide specific recommendation with reasoning.
""")

recommendation_chain = recommendation_prompt | llm | StrOutputParser()

add_routes(
    app,
    recommendation_chain.with_types(input_type=RecommendationInput),
    path="/recommend"
)

# ============================================================
# ENDPOINT 4: Agent with Tools
# ============================================================
class AgentInput(BaseModel):
    input: str

# Load data for tools
try:
    cakes_df = pd.read_csv('data/cake_descriptions.csv', encoding='cp1252')
    prices_df = pd.read_csv('data/price_list.csv', encoding='utf-16')
except FileNotFoundError:
    print("⚠️  Could not find data files for agent tools. Agent may not work correctly.")
    cakes_df = pd.DataFrame()
    prices_df = pd.DataFrame()

@tool
def check_product_availability(product_name: str) -> str:
    """Check if a product is available in inventory."""
    if cakes_df.empty:
        return "Inventory data is not available."
    product = cakes_df[cakes_df['Name'].str.contains(product_name, case=False, na=False)]
    if product.empty:
        return f"Product '{product_name}' not found."
    product_info = product.iloc[0]
    if product_info['Available'] == 'Yes':
        return f"✅ {product_info['Name']} is available! Delivery time: {product_info['Delivery_time_hr']} hours."
    else:
        return f"❌ {product_info['Name']} is currently out of stock."

@tool
def calculate_order_total(product_name: str, quantity: int = 1) -> str:
    """Calculate the total cost of an order, including delivery."""
    if prices_df.empty:
        return "Pricing data is not available."
    try:
        filtered = prices_df[prices_df['Item'].str.contains(product_name, case=False, na=False)]
        price = filtered['Unit_Price_AED'].iloc[0]
    except (IndexError, KeyError):
        return f"Price for '{product_name}' not found."

    subtotal = price * quantity
    delivery_fee = 10 if subtotal < 100 else 0
    total = subtotal + delivery_fee
    return f"Order Summary:\n- Product: {product_name} x {quantity}\n- Subtotal: {subtotal} AED\n- Delivery Fee: {delivery_fee} AED\n- Total: {total} AED"

class DeliverySlotInput(BaseModel):
    date: str = Field(description="Delivery date (e.g., 'tomorrow', '2025-10-23')")
    time: str = Field(description="Delivery time (e.g., '2 PM', '14:00')")

@tool(args_schema=DeliverySlotInput)
def check_delivery_slot(date: str, time: str) -> str:
    """Check if a delivery slot is available."""
    import random
    is_available = random.random() < 0.9
    if is_available:
        return f"✅ Delivery slot available for {date} at {time}."
    else:
        return f"❌ Delivery slot for {date} at {time} is fully booked. Alternative times: 10 AM, 4 PM."

tools = [check_product_availability, calculate_order_total, check_delivery_slot]

agent_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are BakeryAI assistant."),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

agent = create_openai_functions_agent(llm, tools, agent_prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=False)

add_routes(
    app,
    agent_executor.with_types(input_type=AgentInput),
    path="/agent"
)

# ============================================================
# Custom REST Endpoints
# ============================================================
@app.get("/")
def root():
    return {
        "message": "Welcome to BakeryAI API!",
        "endpoints": {
            "chat": "/chat (simple chat)",
            "rag": "/rag (knowledge base Q&A)",
            "recommend": "/recommend (cake recommendations)",
            "agent": "/agent (full agent with tools)"
        },
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "vectorstore": vectorstore is not None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
