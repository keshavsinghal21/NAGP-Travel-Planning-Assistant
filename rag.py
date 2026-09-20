import os
import asyncio

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.tools import tool

from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

load_dotenv()

CHROMA_DIR = "chroma_db"


def load_vector_store():
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    vector_store = Chroma(
        persist_directory=CHROMA_DIR,
        collection_name="singapore_travel",
        embedding_function=embeddings,
    )

    return vector_store


async def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY was not found. Please check your .env file."
        )

    print("Loading knowledge base...")
    vector_store = load_vector_store()
    retriever = vector_store.as_retriever(search_kwargs={"k": 4})

    # RAG search tool
    @tool
    def search_knowledge_base(query: str) -> str:
        """Search official Singapore travel guides for attractions, neighborhoods, transportation, food, and itineraries."""
        docs = retriever.invoke(query)
        results = []
        for doc in docs:
            source_title = doc.metadata.get("source_title", "Unknown source")
            source_url = doc.metadata.get("source_url", "")
            results.append(
                f"Source Title: {source_title}\n"
                f"Source URL: {source_url}\n"
                f"Content:\n{doc.page_content}\n"
            )
        return "\n---\n".join(results)

    print("Initializing MCP servers via stdio...")

    # Start MCP servers using stdio
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
        print(f"Warning: Could not load MCP tools: {e}")
        mcp_tools = []
        mcp_warning = str(e)

    all_tools = [search_knowledge_base] + mcp_tools

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.7-flash",
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
    
    agent = create_react_agent(llm, all_tools, prompt=system_prompt)

    print("\nSingapore Travel Assistant")
    print("Type 'exit' to stop the application.\n")

    # Keep same thread + chat history for multi-turn conversation
    config = {"configurable": {"thread_id": "singapore_trip_session"}}
    conversation_messages = []

    if mcp_warning:
        print("Note: MCP tools are currently unavailable. I will answer from local knowledge base only.")

    while True:
        question = input("\nYou: ")

        if question.lower().strip() == "exit":
            print("\nGoodbye!")
            break

        if not question.strip():
            continue

        print("\nThinking...")

        try:
            conversation_messages.append(("user", question))

            response = await agent.ainvoke(
                {"messages": conversation_messages},
                config=config,
            )

            final_message = response["messages"][-1].content
            print(f"\nAssistant:\n\n{final_message}")
            conversation_messages.append(("assistant", str(final_message)))

        except Exception as e:
            print(f"\nError while generating answer: {e}")


if __name__ == "__main__":
    asyncio.run(main())