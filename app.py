import os
import asyncio
import streamlit as st
from dotenv import load_dotenv

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()
CHROMA_DIR = "chroma_db"

# Page setup
st.set_page_config(page_title="AI Travel Assistant", layout="centered")

st.title("AI Travel Planning Assistant")
st.markdown("---")

# Sidebar status
st.sidebar.header("Assignment Status")
api_key_status = "Loaded" if os.getenv("GEMINI_API_KEY") else "Missing"
db_status = "Found" if os.path.exists(CHROMA_DIR) else "Missing (Run ingest.py)"

st.sidebar.text(f"API Key: {api_key_status}")
st.sidebar.text(f"Vector Store: {db_status}")

if st.sidebar.button("Reset Chat Session"):
    st.session_state.messages = []
    st.rerun()

# Load retriever
@st.cache_resource
def get_retriever():
    if not os.path.exists(CHROMA_DIR):
        return None
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name="singapore_travel",
        embedding_function=embeddings,
    )
    return vector_store.as_retriever(search_kwargs={"k": 4})

retriever = get_retriever()

# RAG search tool
@tool
def search_knowledge_base(query: str) -> str:
    """Search official Singapore travel guides for attractions, neighborhoods, transportation, food, and itineraries."""
    if not retriever:
        return "Error: Chroma vector store not found. Please run ingest.py first."
    docs = retriever.invoke(query)
    if not docs:
        return (
            "Knowledge base did not return enough matching content for this question. "
            "Please ask a more specific Singapore question."
        )
    results = []
    for doc in docs:
        title = doc.metadata.get("source_title", "Unknown Source")
        url = doc.metadata.get("source_url", "")
        results.append(f"Source Title: {title}\nSource URL: {url}\nContent:\n{doc.page_content}\n")
    return "\n---\n".join(results)

# Build MCP client + agent
async def get_agent_executor():
    mcp_client = MultiServerMCPClient(
        {
            "weather": {
                "transport": "stdio",
                "command": "python",
                "args": ["weather_server.py"],
            },
            "currency": {
                "transport": "stdio",
                "command": "python",
                "args": ["currency_server.py"],
            },
        }
    )
    
    mcp_warning = None
    try:
        mcp_tools = await mcp_client.get_tools()
    except Exception as e:
        mcp_tools = []
        mcp_warning = f"Live MCP tools are unavailable right now ({e})."
        
    all_tools = [search_knowledge_base] + mcp_tools
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        temperature=0.2,
    )

    system_prompt = (
                "You are an expert Travel Planning Assistant. "
                "Use the search_knowledge_base tool for destination facts, attractions, culture, transport, and itineraries. "
                "Use the MCP tools for real-time information like current weather conditions and currency conversions. "
                "If the user asks about weather or currency, must call an MCP tool before answering. "
                "If MCP tools are unavailable or fail, clearly say that current data could not be fetched. "
                "If the knowledge base does not have enough detail, clearly state that and do not invent facts. "
                "Guidelines for Output: "
                "1. Synthesize the information smoothly. Clean up any raw markdown headers, tags, or structural text artifacts retrieved from the source documents. "
                "2. Present your answers using clean, professional Markdown formatting (bullet points, bold text, and clear section dividers). "
                "3. **Ensure strict text spacing:** Never let words, numbers, punctuation, or brackets collide (e.g., always leave spaces around numbers, prices, and parentheses like '$34 respectively'). "
                "4. Always cite your sources clearly at the end or within the response when referencing knowledge-base content. "
                "5. Do not invent facts, numbers, or URLs that are not in tool results or retrieved content."
    )
    
    return create_react_agent(llm, all_tools, prompt=system_prompt), mcp_warning

# Chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I am ready to help you plan your trip. Ask me about attractions, weather, or budget conversions."}
    ]

# Show chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input
if prompt := st.chat_input("Type your question here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Running agent workflow..."):
            try:
                agent, mcp_warning = asyncio.run(get_agent_executor())
                config = {"configurable": {"thread_id": "assignment_session"}}

                conversation = []
                for msg in st.session_state.messages:
                    role = msg.get("role")
                    content = str(msg.get("content", "")).strip()
                    if role in {"user", "assistant"} and content:
                        conversation.append((role, content))
                
                response = asyncio.run(
                    agent.ainvoke({"messages": conversation}, config=config)
                )
                
                # Read final text safely from different output formats
                raw_content = response["messages"][-1].content
                
                if isinstance(raw_content, list):
                    text_chunks = []
                    for item in raw_content:
                        if isinstance(item, dict) and "text" in item:
                            text_chunks.append(item["text"])
                        elif isinstance(item, str):
                            text_chunks.append(item)
                    final_answer = "\n".join(text_chunks)
                elif isinstance(raw_content, dict):
                    final_answer = raw_content.get("text", str(raw_content))
                else:
                    final_answer = str(raw_content)

                if mcp_warning:
                    final_answer = (
                        f"Note: {mcp_warning}\n\n"
                        "I can still answer using the local Singapore knowledge base.\n\n"
                        f"{final_answer}"
                    )
                    
            except Exception as e:
                final_answer = f"Error executing request: {e}"
                
        # Show response and store it in chat history
        st.markdown(final_answer)
        st.session_state.messages.append({"role": "assistant", "content": final_answer})