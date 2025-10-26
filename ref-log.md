# Reference Log (ref-log.md)

This document logs all external sources, tools, and AI assistance used in completing Assignment 1.

## 📚 External Documentation & Resources

### LangChain Documentation
- **Source**: https://python.langchain.com/docs/
- **Usage**: 
  - Understanding ConversationalRetrievalChain implementation
  - Learning document loaders (TextLoader, PyPDFLoader)
  - Vector store integration with ChromaDB
  - Memory management with ConversationBufferMemory
- **Specific Pages Referenced**:
  - https://python.langchain.com/docs/modules/data_connection/document_loaders/
  - https://python.langchain.com/docs/modules/data_connection/text_splitter/
  - https://python.langchain.com/docs/modules/data_connection/vectorstores/

### Streamlit Documentation
- **Source**: https://docs.streamlit.io/
- **Usage**:
  - File uploader component (`st.file_uploader`)
  - Chat interface components (`st.chat_message`, `st.chat_input`)
  - Session state management
  - Sidebar layout and UI components
- **Specific Pages Referenced**:
  - https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
  - https://docs.streamlit.io/develop/api-reference/chat

### ChromaDB Documentation
- **Source**: https://docs.trychroma.com/
- **Usage**:
  - Understanding vector database setup
  - Learning about persistence with `persist_directory`
  - Integration with LangChain

### OpenAI API Documentation
- **Source**: https://platform.openai.com/docs
- **Usage**:
  - Understanding embeddings API
  - Chat completions API
  - Best practices for temperature settings

## 🤖 GenAI Usage

### Claude (Anthropic AI Assistant)
- **Tool**: Claude.ai / Claude API
- **Usage**: Code generation and documentation assistance
- **Rationale**: 
  - Generated initial boilerplate code structure for the RAG application
  - Assisted with writing comprehensive docstrings and comments
  - Helped create README.md documentation
  - Generated this ref-log.md template
- **Specific Contributions**:
  - Code structure and function organization
  - Detailed inline comments explaining RAG concepts
  - README.md setup instructions
  - Troubleshooting guide
  
**Human Oversight**: All generated code was reviewed, tested, and modified as needed. Understanding of RAG concepts and implementation decisions were verified through documentation.

### ChatGPT (Optional - if used)
- **Tool**: ChatGPT
- **Usage**: [Describe if used]
- **Rationale**: [Why used]

### GitHub Copilot (Optional - if used)
- **Tool**: GitHub Copilot
- **Usage**: [Describe if used]
- **Rationale**: [Why used]

## 📖 Course Materials

### Class Repository
- **Source**: https://github.com/AyhamB/INFO-5940-Codespace
- **Branch**: assignment1
- **Usage**:
  - Used provided `requirements.txt` as base
  - Referenced `chat_with_pdf.py` example for inspiration
  - Used `.devcontainer` configuration
  - Reviewed `langgraph_chroma_retreiver.ipynb` for syntax examples

### Class Lectures & Examples
- **Usage**:
  - Applied RAG concepts from class discussions
  - Implemented chunking strategies discussed in lecture
  - Used retrieval techniques demonstrated in class

## 🛠️ Libraries & Frameworks

### Core Dependencies

1. **LangChain** (v0.3.27)
   - **Purpose**: RAG pipeline framework
   - **Components Used**:
     - `langchain_community.document_loaders`: TextLoader, PyPDFLoader
     - `langchain.text_splitter`: RecursiveCharacterTextSplitter
     - `langchain_community.vectorstores`: Chroma
     - `langchain.chains`: ConversationalRetrievalChain
     - `langchain.memory`: ConversationBufferMemory

2. **LangChain OpenAI** (v0.3.35)
   - **Purpose**: OpenAI integration for LangChain
   - **Components Used**:
     - `OpenAIEmbeddings`: Convert text to vector embeddings
     - `ChatOpenAI`: Language model for response generation

3. **ChromaDB** (v0.4.0+)
   - **Purpose**: Vector database for document storage
   - **Usage**: Store and retrieve document embeddings

4. **Streamlit** (v1.36+)
   - **Purpose**: Web UI framework
   - **Components Used**:
     - File uploader
     - Chat interface
     - Session state
     - Sidebar layout

5. **langchain-openai** (v0.1.0+)
   - **Purpose**: OpenAI integration for LangChain
   - **Usage**: OpenAI embeddings and chat models

6. **langchain-chroma** (v0.1.0+)
   - **Purpose**: ChromaDB integration for LangChain
   - **Usage**: Vector store implementation

7. **PyPDF** (v4.0+)
   - **Purpose**: PDF file parsing
   - **Usage**: Extract text from PDF documents

6. **OpenAI** (v1.14)
   - **Purpose**: API client for OpenAI services
   - **Usage**: Embeddings and language model API calls

## 🔍 Stack Overflow & Community Forums

### Stack Overflow
- **Usage**: Troubleshooting specific errors
- **Topics Searched**:
  - ChromaDB persistence issues
  - Streamlit session state best practices
  - LangChain memory management
  - File upload handling in Streamlit

### Reddit (r/LangChain, r/MachineLearning)
- **Usage**: Understanding RAG best practices
- **Topics**: Chunking strategies, retrieval optimization

### GitHub Issues
- **Usage**: Troubleshooting specific errors
- **Topics**:
  - ChromaDB readonly database errors
  - LangChain integration patterns
  - OpenAI API configuration

## 📊 Design Decisions & Rationale

### 1. Embedding Strategy: OpenAI Embeddings

**Decision**: Use OpenAI Embeddings (`openai.text-embedding-3-large`) via Cornell's API

**Sources**: 
- Professor's example code
- Cornell API documentation
- LangChain OpenAI Integration: https://python.langchain.com/docs/integrations/text_embedding/openai

**Rationale**: 
- **Professor's Recommendation**: Model name provided by instructor (`openai.text-embedding-3-large`) works correctly with Cornell's API
- **High Quality**: OpenAI's embedding models provide excellent semantic understanding
- **Consistency**: Aligns with course infrastructure and examples
- **Integration**: Seamless integration with LangChain using `langchain_openai` package

### 2. Vector Database Storage: Persistent vs In-Memory

**Decision**: Use in-memory (ephemeral) ChromaDB instead of persistent storage

**Source**: ChromaDB Documentation: https://docs.trychroma.com/

**Rationale**:
- **Problem**: Encountered "readonly database" errors when using persistent storage in Codespace
- **Solution**: Switched to `chromadb.EphemeralClient()` for in-memory storage
- **Benefits**:
  - No file permission issues
  - Faster performance (no disk I/O)
  - Simpler cleanup and reset process
  - Fresh start on each session prevents stale data issues
- **Trade-off**: Documents must be re-uploaded if the app restarts (acceptable for demo/assignment)

### 3. Model Selection: GPT-4o

**Decision**: Use `openai.gpt-4o` for response generation

**Source**: Cornell API documentation and testing

**Rationale**:
- Available through Cornell's API with model name `openai.gpt-4o`
- Better understanding and response quality than GPT-3.5-turbo
- Optimal for educational/demonstration purposes

### 4. Chunking Strategy

**Decision**: RecursiveCharacterTextSplitter with 1000 char chunks, 200 char overlap

**Source**: LangChain documentation on text splitting best practices

**Rationale**: 
- Balances context preservation with retrieval precision
- 200 char overlap prevents information loss at boundaries
- Recursive splitting maintains semantic meaning by trying paragraph breaks first

## 📝 Notes

- All code was tested in the GitHub Codespace environment
- API key is stored as environment variable (not committed to repo)
- ChromaDB directory (`./chroma_db`) is gitignored
- All dependencies are specified in `requirements.txt`

## 🔄 Iterations & Changes

### Version 1.0 (Initial Implementation)
- Basic file upload and processing
- Simple chunking strategy
- Initial RAG pipeline

### Version 1.1 (Current)
- Added multi-file support
- Improved error handling
- Enhanced UI with source document display
- Added comprehensive documentation

## ✅ Declaration

I confirm that:
- All external sources are documented above
- AI assistance usage is clearly stated
- I understand all code in this project
- Design decisions were made thoughtfully with documented rationale

---

**Student Name**: Matthew Lee
**Date**: 10/26/25
**Course**: INFO 5940
**Assignment**: Assignment 1 - RAG Application