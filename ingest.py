from pathlib import Path

from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


DATA_DIR = Path("data")
CHROMA_DIR = "chroma_db"


SOURCE_METADATA = {
    "wikivoyage_singapore.md": {
        "source_title": "Wikivoyage Singapore Travel Guide",
        "source_url": "https://en.wikivoyage.org/wiki/Singapore",
    },
    "visit_singapore_essential_information.md": {
        "source_title": "Visit Singapore - Essential Travel Information",
        "source_url": "https://www.visitsingapore.com/travel-tips/essential-travel-information/",
    },
    "visit_singapore_itineraries.md": {
        "source_title": "Visit Singapore - Sample Itineraries",
        "source_url": "https://www.visitsingapore.com/singapore-itineraries/",
    },
    "visit_singapore_things_to_do.md": {
        "source_title": "Visit Singapore - Things to Do",
        "source_url": "https://www.visitsingapore.com/see-do-singapore/",
    },
}


def main():
    print("Loading travel documents...")

    loader = DirectoryLoader(
        str(DATA_DIR),
        glob="*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )

    documents = loader.load()

    print(f"Loaded {len(documents)} documents")

    # Add source title and URL to document metadata
    for document in documents:
        filename = Path(document.metadata["source"]).name

        if filename in SOURCE_METADATA:
            document.metadata.update(SOURCE_METADATA[filename])

    print("Splitting documents into chunks...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
    )

    chunks = text_splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    print("Creating embeddings...")

    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    print("Creating Chroma vector store...")

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR,
        collection_name="singapore_travel",
    )

    print("RAG knowledge base created successfully.")
    print(f"Vector database location: {CHROMA_DIR}")
    print(f"Total chunks stored: {len(chunks)}")


if __name__ == "__main__":
    main()