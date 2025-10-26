"""
RAG (Retrieval Augmented Generation) Application
-------------------------------------------------
This application allows users to upload documents (.txt and .pdf) and chat with them
using a conversational AI interface powered by LangChain and ChromaDB.

Requirements Implemented:
1. Codespace setup with requirements.txt
2. File upload for .txt files
3. RAG system with chunking, retrieval, and conversation
4. Support for .txt and .pdf formats
5. Multiple document uploads
"""

# ...existing code...
try:
    import streamlit as st
    # standard LangChain import paths (works with modern langchain + langchain-core)
    from langchain.document_loaders import TextLoader, PyPDFLoader
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.vectorstores import Chroma
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain.chat_models import ChatOpenAI
    from langchain.chains import ConversationalRetrievalChain
    from langchain.memory import ConversationBufferMemory
except Exception as e:
    raise RuntimeError(
        "Missing or incompatible Python packages. Install dependencies with:\n\n"
        "  pip3 install -r /workspaces/INFO-5940-Codespace/requirements.txt\n\n"
        "If you're using the devcontainer, rebuild it (Command Palette → Dev Containers: Rebuild and Reopen in Container).\n\n"
        f"Original import error: {e!r}"
    ) from e
# ...existing code...
import tempfile
import os
from pathlib import Path
import shutil

# ============================================================================
# API CONFIGURATION - Read from environment (simple like the example)
# ============================================================================
API_KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("API_KEY")
BASE_URL = os.environ.get("OPENAI_BASE_URL") or os.environ.get("BASE_URL") or "https://api.ai.it.cornell.edu"

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="RAG Chat Application",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
# Session state maintains data across Streamlit reruns
if "conversation" not in st.session_state:
    st.session_state.conversation = None  # Stores the LangChain conversation chain
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # Stores all Q&A pairs
if "processed_files" not in st.session_state:
    st.session_state.processed_files = []  # Tracks which files have been processed
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None  # Stores the ChromaDB vectorstore


# ============================================================================
# REQUIREMENT 2 & 4: FILE LOADING (.txt and .pdf)
# ============================================================================
def load_document(file_path, file_type):
    """
    Load document content based on file type.
    
    This function handles different file formats and extracts text content.
    - For .txt files: Uses TextLoader with UTF-8 encoding
    - For .pdf files: Uses PyPDFLoader to extract text from all pages
    
    Args:
        file_path (str): Path to the file to load
        file_type (str): Type of file ('txt' or 'pdf')
    
    Returns:
        list: List of LangChain Document objects containing the text and metadata
              Returns None if loading fails
    """
    try:
        if file_type == "txt":
            # TextLoader reads plain text files
            loader = TextLoader(file_path, encoding='utf-8')
        elif file_type == "pdf":
            # PyPDFLoader extracts text from PDF files page by page
            loader = PyPDFLoader(file_path)
        else:
            st.error(f"❌ Unsupported file type: {file_type}")
            return None
        
        # Load and return documents
        documents = loader.load()
        return documents
    
    except Exception as e:
        st.error(f"❌ Error loading {file_type} file: {str(e)}")
        return None


# ============================================================================
# REQUIREMENT 3.1: DOCUMENT CHUNKING
# ============================================================================
def chunk_documents(documents):
    """
    Split documents into smaller chunks for efficient retrieval.
    
    CHUNKING STRATEGY:
    - Uses RecursiveCharacterTextSplitter (best practice for text)
    - Chunk size: 1000 characters (balances context and performance)
    - Chunk overlap: 200 characters (maintains context between chunks)
    - Separators: ["\n\n", "\n", " ", ""] (tries to split on paragraphs first,
      then sentences, then words, preserving semantic meaning)
    
    Why chunking?
    - Large documents don't fit in LLM context windows
    - Smaller chunks = more precise retrieval
    - Overlap ensures we don't lose context at boundaries
    
    Args:
        documents (list): List of LangChain Document objects
    
    Returns:
        list: List of chunked Document objects
    """
    # Initialize the text splitter with our chosen strategy
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,        # Maximum characters per chunk
        chunk_overlap=200,      # Characters to overlap between chunks
        length_function=len,    # Function to measure chunk length
        separators=["\n\n", "\n", " ", ""]  # Try these separators in order
    )
    
    # Split documents into chunks
    chunks = text_splitter.split_documents(documents)
    return chunks


# ============================================================================
# REQUIREMENT 3.2: VECTOR STORE CREATION (RAG - Retrieval Component)
# ============================================================================
def create_vectorstore(chunks):
    """
    Create or update ChromaDB vector store with document chunks.
    Uses HuggingFace embeddings (runs locally, no API needed)
    
    Args:
        chunks (list): List of document chunks
    
    Returns:
        Chroma: ChromaDB vectorstore instance
    """
    # Initialize HuggingFace embeddings (runs locally - no API needed!)
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )
    
    # Create or update the vector store
    if st.session_state.vectorstore is None:
        # First time: create new vectorstore with a fresh client
        import chromadb
        from chromadb.config import Settings
        
        # Create a fresh ephemeral client (in-memory)
        client = chromadb.EphemeralClient()
        
        vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            client=client,
            collection_name=f"rag_collection_{id(chunks)}"  # Unique name per session
        )
    else:
        # Subsequent times: add to existing vectorstore
        vectorstore = st.session_state.vectorstore
        vectorstore.add_documents(chunks)
    
    return vectorstore


# ============================================================================
# REQUIREMENT 3.2 & 3.3: CONVERSATIONAL RAG CHAIN
# ============================================================================
def initialize_conversation_chain(vectorstore):
    """
    Initialize the conversational retrieval chain.
    
    RAG PIPELINE:
    1. User asks a question
    2. Retrieve relevant chunks from vectorstore (similarity search)
    3. Pass retrieved chunks + question to LLM
    4. LLM generates answer grounded in the documents
    5. Store conversation history for multi-turn chat
    
    Args:
        vectorstore (Chroma): ChromaDB vectorstore instance
    
    Returns:
        ConversationalRetrievalChain: LangChain conversation chain
    """
    # Initialize the language model
    llm = ChatOpenAI(
        openai_api_key=API_KEY,
        base_url=BASE_URL,
        model_name="openai.gpt-4o",  # Using openai.gpt-4o as requested
        temperature=0.7       # Balance between creativity and consistency
    )
    
    # Initialize conversation memory
    # This stores chat history for multi-turn conversations
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer"
    )
    
    # Create the conversational retrieval chain
    # This combines retrieval + generation
    conversation_chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(
            search_type="similarity",  # Use cosine similarity for search
            search_kwargs={"k": 3}     # Retrieve top 3 most relevant chunks
        ),
        memory=memory,
        return_source_documents=True   # Return sources for transparency
    )
    
    return conversation_chain


# ============================================================================
# REQUIREMENT 5: PROCESS MULTIPLE UPLOADED FILES
# ============================================================================
def process_uploaded_files(uploaded_files):
    """
    Process multiple uploaded files and create/update the RAG system.
    
    PROCESSING STEPS:
    1. Check if file was already processed (avoid duplicates)
    2. Save file temporarily to disk
    3. Load document content
    4. Chunk the document
    5. Add chunks to vector store
    6. Initialize conversation chain
    
    Args:
        uploaded_files (list): List of Streamlit UploadedFile objects
    """
    all_chunks = []
    
    # Process each uploaded file
    for uploaded_file in uploaded_files:
        # Skip if file already processed (prevents duplicates)
        if uploaded_file.name in st.session_state.processed_files:
            st.info(f"📄 {uploaded_file.name} already processed. Skipping...")
            continue
        
        # Get file extension to determine type
        file_extension = Path(uploaded_file.name).suffix.lower()
        file_type = file_extension[1:]  # Remove the dot (.txt -> txt)
        
        # Save uploaded file to temporary location
        # (LangChain loaders need file paths, not file objects)
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(uploaded_file.read())
            tmp_file_path = tmp_file.name
        
        try:
            # Step 1: Load document
            with st.spinner(f"📖 Loading {uploaded_file.name}..."):
                documents = load_document(tmp_file_path, file_type)
            
            if documents:
                # Step 2: Chunk document
                with st.spinner(f"✂️ Chunking {uploaded_file.name}..."):
                    chunks = chunk_documents(documents)
                    all_chunks.extend(chunks)
                
                # Mark as processed
                st.session_state.processed_files.append(uploaded_file.name)
                st.success(f"✅ {uploaded_file.name} processed! ({len(chunks)} chunks created)")
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
    
    # Create/update vector store if we have new chunks
    if all_chunks:
        with st.spinner("🔧 Building vector database..."):
            st.session_state.vectorstore = create_vectorstore(all_chunks)
        
        # Initialize conversation chain
        with st.spinner("💬 Initializing conversation..."):
            st.session_state.conversation = initialize_conversation_chain(
                st.session_state.vectorstore
            )
        
        st.success("🎉 All files processed! You can now start chatting.")


# ============================================================================
# REQUIREMENT 3.3: HANDLE USER QUESTIONS
# ============================================================================
def handle_user_input(user_question):
    """
    Handle user's question and generate response using RAG.
    
    PROCESS:
    1. Check if documents are loaded
    2. Send question to conversation chain
    3. Retrieve relevant chunks
    4. Generate answer based on chunks
    5. Store in chat history
    
    Args:
        user_question (str): User's question
    """
    if st.session_state.conversation is None:
        st.warning("⚠️ Please upload and process documents first!")
        return
    
    # Get response from RAG chain
    with st.spinner("🤔 Thinking..."):
        response = st.session_state.conversation({
            "question": user_question
        })
    
    # Add to chat history with sources
    st.session_state.chat_history.append({
        "question": user_question,
        "answer": response["answer"],
        "sources": response.get("source_documents", [])
    })


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application function - defines the UI and logic flow"""
    
    # Header
    st.title("📚 RAG Chat Application")
    st.markdown("Upload documents (.txt or .pdf) and chat with them using AI!")
    
    # ========================================================================
    # SIDEBAR: File Upload (NO API KEY INPUT NEEDED!)
    # ========================================================================
    with st.sidebar:
        # File Upload Section
        st.header("📁 Upload Documents")
        
        # REQUIREMENT 2, 4, 5: File uploader with multiple file support
        uploaded_files = st.file_uploader(
            "Choose files",
            type=["txt", "pdf"],           # Support .txt and .pdf
            accept_multiple_files=True,    # Allow multiple uploads
            help="Upload one or more .txt or .pdf files"
        )
        
        # Process button
        if st.button("Process Documents", type="primary"):
            if not uploaded_files:
                st.error("⚠️ Please upload at least one file!")
            else:
                process_uploaded_files(uploaded_files)
        
        # Display processed files
        if st.session_state.processed_files:
            st.markdown("---")
            st.subheader("📋 Processed Files")
            for file_name in st.session_state.processed_files:
                st.text(f"✓ {file_name}")
        
        # Clear button to reset everything
        st.markdown("---")
        if st.button("🗑️ Clear All", type="secondary"):
            # Close vectorstore connection before deleting
            if st.session_state.vectorstore is not None:
                try:
                    # Try to delete the collection
                    st.session_state.vectorstore._client.delete_collection(
                        st.session_state.vectorstore._collection.name
                    )
                except:
                    pass  # Ignore errors if collection doesn't exist
            
            # Clear session state
            st.session_state.conversation = None
            st.session_state.chat_history = []
            st.session_state.processed_files = []
            st.session_state.vectorstore = None
            
            # Remove ChromaDB directory
            db_path = "/workspaces/INFO-5940-Codespace/chroma_db"
            if os.path.exists(db_path):
                try:
                    shutil.rmtree(db_path)
                except:
                    pass  # Ignore errors
            
            st.success("✅ Cleared! Refresh the page to start fresh.")
            st.rerun()
    
    # ========================================================================
    # MAIN AREA: Chat Interface
    # ========================================================================
    st.markdown("---")
    
    # Display chat history
    if st.session_state.chat_history:
        for i, chat in enumerate(st.session_state.chat_history):
            # User message
            with st.chat_message("user"):
                st.write(chat["question"])
            
            # Assistant message
            with st.chat_message("assistant"):
                st.write(chat["answer"])
    
    # Chat input (always visible at bottom)
    user_question = st.chat_input(
        "Ask a question about your documents...",
        disabled=st.session_state.conversation is None
    )
    
    # Handle new user input
    if user_question:
        handle_user_input(user_question)
        st.rerun()  # Refresh to show new message


# ============================================================================
# RUN APPLICATION
# ============================================================================
if __name__ == "__main__":
    main()