# AI AudioBook Generator - System Workflow

## Text Processing Workflow

```
┌─────────────────────────────────────────────────────────────┐
│                    TEXT PROCESSING WORKFLOW                  │
└─────────────────────────────────────────────────────────────┘

                              ↓

        ┌──────────────────────────────────────┐
        │   1. User (Streamlit Web UI)         │
        │   • Two-tab interface                │
        │   • Session state management         │
        │   • Gradient modern design           │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   2. File Upload                     │
        │   • PDF, DOCX, Images, TXT           │
        │   • Checkboxes for options           │
        │   • AI Enhance / Save for Q&A        │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   3. Text Extraction                 │
        │   • pdfplumber (PDF text)            │
        │   • pytesseract (OCR for images)     │
        │   • python-docx (Word docs)          │
        │   • Stored in session state          │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   4. LLM Rewriting (Optional)        │
        │   • Google Gemini 2.5 Flash          │
        │   • Enhanced for narration           │
        │   • Improved readability             │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   5. Embeddings Generation           │
        │   • HuggingFace Transformers         │
        │   • all-MiniLM-L6-v2 model           │
        │   • 384-dimensional vectors          │
        │   • Saved to CSV                     │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   6. Vector Database Storage         │
        │   • ChromaDB persistence             │
        │   • Collection clearing enabled      │
        │   • Document-specific Q&A            │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   7. Q and A (RAG Pipeline)          │
        │   • LangChain orchestration          │
        │   • Retrieval with sources           │
        │   • Chat history tracking            │
        │   • Context-aware responses          │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   8. Text-to-Speech (TTS)            │
        │   • Edge-TTS (Primary - MP3)         │
        │   • High-quality neural voices       │
        │   • Fast synthesis                   │
        │   • Stored in session state          │
        └──────────────────────────────────────┘
                              ↓
        ┌──────────────────────────────────────┐
        │   9. User Download                   │
        │   • Audio download (WAV/MP3)         │
        │   • Text download (.txt)             │
        │   • Persistent across tabs           │
        └──────────────────────────────────────┘


## Technology Stack by Component

### 1. User Interface (Streamlit)
- **streamlit 1.36+** - Web framework
- **Custom CSS** - Inter font, gradients, animations
- **Session State** - Data persistence

### 2. File Upload
- **Streamlit file_uploader** - Multi-format support
- **tempfile** - Temporary file handling
- **pathlib** - Path management

### 3. Text Extraction
- **pdfplumber** - PDF text extraction
- **pytesseract + Tesseract OCR** - Image/scanned PDF OCR
- **pdf2image + Poppler** - PDF to image conversion
- **python-docx** - Word document processing
- **Pillow** - Image handling

### 4. LLM Rewriting
- **google-generativeai** - Gemini 2.5 Flash API
- **GOOGLE_API_KEY** - Authentication
- Prompt: Rewrite for audiobook narration

### 5. Embeddings Generation
- **sentence-transformers** - HuggingFace model loading
- **all-MiniLM-L6-v2** - 384-dim semantic embeddings
- **pandas** - CSV export for embeddings

### 6. Vector Database
- **chromadb 1.3+** - Vector storage and search
- **Collection clearing** - Single-document Q&A mode
- **Unique document IDs** - `{source_name}_{i}` format

### 7. Q and A (RAG)
- **langchain** - RAG orchestration
- **langchain-chroma** - ChromaDB integration
- **langchain-google-genai** - LLM integration
- **langchain-huggingface** - Embeddings integration
- **RetrievalQA chain** - Question answering pipeline

### 8. Text-to-Speech
- **edge-tts 6.1+** ⭐ Primary engine
- **Microsoft Neural Voices** - High quality
- **Async synthesis** - Fast generation
- **MP3 output** - Compressed audio

### 9. User Download
- **st.download_button** - Download UI
- **Audio player** - In-browser playback
- **File persistence** - Session state storage


## Data Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FRONTEND (Tab 1)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ File Upload  │→ │  Processing  │→ │   Results    │      │
│  │   Widget     │  │   Pipeline   │  │   Display    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│         ↓ Session State (audio_path, extracted_text)         │
│                                                               │
│                        FRONTEND (Tab 2)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Load Vector  │→ │  User Query  │→ │     RAG      │      │
│  │   Store      │  │    Input     │  │   Response   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND MODULES                         │
│                                                               │
│  extractor.py  →  Text extraction logic                      │
│  llm_enrich.py →  Gemini API integration                     │
│  embeddings.py →  HuggingFace embeddings                     │
│  vectordb_save.py → ChromaDB persistence                     │
│  rag_langchain.py → LangChain RAG pipeline                   │
│  tts.py        →  Edge-TTS synthesis                         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                           │
│                                                               │
│  outputs/text/        →  Extracted text files                │
│  outputs/audio/       →  Generated audio files               │
│  outputs/embeddings/  →  CSV embedding exports               │
│  vectordb/            →  ChromaDB collections                │
└─────────────────────────────────────────────────────────────┘
```

## Processing Pipeline Details

### Upload & Generate Tab
1. **File Upload** → User selects file (PDF/DOCX/Image/TXT)
2. **Options Selection** → AI Enhance checkbox, Save for Q&A checkbox
3. **Text Extraction** → Backend extracts text, stores in session
4. **AI Enhancement** (if enabled) → Gemini rewrites for narration
5. **Embeddings** (if Save for Q&A) → Generate 384-dim vectors
6. **Vector DB Save** (if Save for Q&A) → Store in ChromaDB with collection clearing
7. **TTS Generation** → Edge-TTS creates audio, stores in session
8. **Results Display** → Audio player + text area + download buttons

### Q&A Chat Tab
1. **Vector Store Load** → Initialize ChromaDB connection
2. **Chat History** → Display previous Q&A pairs with sources
3. **User Query** → Text input for question
4. **RAG Retrieval** → Search vector DB for relevant chunks
5. **LLM Response** → Gemini generates answer with context
6. **Display Answer** → Show response with source references

## Session State Management

```python
st.session_state = {
    'chat_history': [],              # Q&A conversation history
    'vectorstore': None,              # ChromaDB instance
    'last_audio_path': None,          # Audio file path
    'last_audio_filename': None,      # Audio filename
    'last_extracted_text': None,      # Extracted document text
    'last_document_name': None        # Source document name
}
```

## Error Handling & Fallbacks

- **Missing Tesseract** → Clear error message with installation link
- **Missing Poppler** → Fallback to text-only PDF extraction
- **API Quota Exceeded** → Skip AI enhancement, use original text
- **No Vector Store** → Prompt user to upload document first
- **TTS Failure** → Return error message, no audio generated
- **Empty Text** → Prevent processing, show warning message

## Performance Optimizations

- **HuggingFace Local** → No API calls, fast embeddings
- **Edge-TTS Async** → Non-blocking audio generation
- **Session State** → Avoid re-processing on tab switch
- **Collection Clearing** → Document-specific Q&A accuracy
- **Collapsible UI** → Minimal scrolling, clean interface
- **Status Container** → Real-time progress feedback
