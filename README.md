# RAG Chat Application

A Retrieval-Augmented Generation (RAG) application that allows users to upload documents and interact with them through a conversational AI interface.

## 📋 Features

- ✅ Upload `.txt` and `.pdf` files
- ✅ Multiple document support
- ✅ Intelligent document chunking for efficient retrieval
- ✅ Vector-based semantic search using ChromaDB and HuggingFace embeddings
- ✅ Conversational interface with chat history using GPT-4o
- ✅ Source document tracking for transparency
- ✅ In-memory vector database for fast performance

## 🛠️ Requirements

All dependencies are listed in `requirements.txt`. Key packages include:

- **Streamlit**: Web interface
- **LangChain**: RAG pipeline framework
- **ChromaDB**: Vector database for document storage
- **OpenAI**: Language model (GPT-4o) and embeddings
- **PyPDF**: PDF file parsing

## 🚀 Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd <your-repo-name>
git checkout assignment1
```

### 2. Install Dependencies

The Codespace environment should automatically install dependencies from `requirements.txt`. If not, run:

```bash
pip install -r requirements.txt
```

### 3. API Key Configuration

The application reads API keys from environment variables (configured in `.devcontainer/devcontainer.json`):

- `API_KEY` or `OPENAI_API_KEY`: Your Cornell/OpenAI API key
- `BASE_URL` or `OPENAI_BASE_URL`: API endpoint (default: `https://api.ai.it.cornell.edu`)

**For Cornell Students:**
- API keys are pre-configured in the devcontainer
- No manual configuration needed

**For Others:**
Set your API key as an environment variable:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 4. Run the Application

```bash
streamlit run chat_with_pdf.py
```

The application will open in your browser automatically. In Codespaces, click the "Open in Browser" button when prompted.

## 📖 How to Use

### Step 1: Upload Documents

1. Click "Browse files" in the sidebar
2. Select one or more `.txt` or `.pdf` files
3. Click "Process Documents"
4. Wait for processing to complete (you'll see progress indicators)

### Step 2: Start Chatting

1. Type your question in the chat input at the bottom
2. Press Enter to send
3. View the AI's response based on your documents
4. Click "View Source Documents" to see which parts of your documents were used

### Step 3: Multi-Turn Conversation

- Continue asking follow-up questions
- The system remembers previous conversation context
- Upload more documents anytime to expand the knowledge base

### Step 4: Clear and Restart

- Click "🗑️ Clear All" in the sidebar to:
  - Remove all uploaded documents
  - Clear conversation history
  - Reset the vector database

## 🏗️ Architecture

### Document Processing Pipeline

```
Upload Files → Load Documents → Chunk Text → Create Embeddings → Store in ChromaDB
```

### Query Processing Pipeline

```
User Question → Retrieve Relevant Chunks → Generate Answer with LLM → Display with Sources
```

### Key Components

1. **Document Loaders** (`langchain.document_loaders`)
   - `TextLoader`: Handles `.txt` files
   - `PyPDFLoader`: Handles `.pdf` files

2. **Text Splitter** (`langchain.text_splitter.RecursiveCharacterTextSplitter`)
   - Chunk size: 1000 characters
   - Chunk overlap: 200 characters
   - Separators: `["\n\n", "\n", " ", ""]`

3. **Embeddings** (`langchain_openai.OpenAIEmbeddings`)
   - Model: `openai.text-embedding-3-large`
   - Uses Cornell's API endpoint
   - Converts text to vector embeddings for semantic search

4. **Vector Store** (`langchain.vectorstores.Chroma`)
   - In-memory storage for fast performance
   - Enables semantic search
   - No persistence (resets on app restart)

5. **Retrieval Chain** (`langchain.chains.ConversationalRetrievalChain`)
   - Retrieves top 3 most relevant chunks
   - Generates answers using GPT-4o
   - Maintains conversation history

## 📝 Chunking Strategy Explanation

**Why do we chunk documents?**
- Large documents exceed LLM context window limits
- Smaller chunks enable more precise retrieval
- Better performance and accuracy

**Our Strategy:**
- **Chunk Size**: 1000 characters
  - Large enough to maintain context
  - Small enough for precise retrieval
  
- **Overlap**: 200 characters
  - Prevents losing context at chunk boundaries
  - Ensures related information stays connected

- **Separators**: `["\n\n", "\n", " ", ""]`
  - Prioritizes splitting on paragraph breaks
  - Falls back to line breaks, then spaces
  - Preserves semantic meaning

## 🔧 Configuration Changes

### Changes to `requirements.txt`

Added the following packages for RAG functionality:

```
chromadb>=0.4.0           # Vector database
langchain-chroma>=0.1.0   # ChromaDB integration
langchain-openai>=0.1.0   # OpenAI embeddings and models
```

All other dependencies were already present in the provided template.

### No Changes to `.devcontainer`

The provided devcontainer configuration works perfectly for this application.

## 💡 Design Decisions

### 1. OpenAI Embeddings with Cornell API

**Decision**: Use `openai.text-embedding-3-large` model via Cornell's API

**Rationale**:
- Model name provided by instructor works with Cornell's API endpoint
- High-quality embeddings for accurate semantic search
- Consistent with course infrastructure

### 2. In-Memory ChromaDB

**Decision**: Use ephemeral (in-memory) ChromaDB instead of persistent storage

**Rationale**:
- Avoids file permission issues in Codespace environment
- Faster performance (no disk I/O)
- Simpler cleanup process
- Documents reprocess on restart (acceptable for demo/assignment)

### 3. GPT-4o for Response Generation

**Decision**: Use `openai.gpt-4o` model

**Rationale**:
- Better understanding and response quality than GPT-3.5
- Available through Cornell's API
- Optimal balance of performance and capability

## 🎯 Requirements Checklist

- ✅ **Requirement 1**: Uses provided Codespace setup (documented changes above)
- ✅ **Requirement 2**: File upload for `.txt` files implemented
- ✅ **Requirement 3.1**: Document chunking with RecursiveCharacterTextSplitter
- ✅ **Requirement 3.2**: RAG pipeline with ChromaDB and LangChain
- ✅ **Requirement 3.3**: Conversational interface with chat history
- ✅ **Requirement 4**: Support for both `.txt` and `.pdf` files
- ✅ **Requirement 5**: Multiple document upload support

## 🐛 Troubleshooting

### Issue: "Module not found" errors

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: Numpy compatibility errors

**Solution**: Reinstall numpy with compatible version
```bash
pip install --force-reinstall numpy==1.24.3
```

### Issue: "Readonly database" error

**Solution**: Click "Clear All" button or refresh the browser page

### Issue: API key errors

**Solution**: 
- Verify your API key is set in devcontainer.json or environment
- Check the base URL matches your endpoint
- Ensure you have access to the API

### Issue: PDF not loading

**Solution**:
- Ensure the PDF contains extractable text (not just images)
- Try a different PDF file
- Check the console for specific error messages

## 📚 Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)

## 👨‍💻 Author

Matthew Lee
Course: INFO 5940  
Assignment: Assignment 1 - RAG Application  
Date: 10/26/25
## 📄 License

This project is for educational purposes as part of INFO 5940.