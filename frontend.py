"""
AudioBook Generator - Frontend
Two-tab interface:
1. Upload & Generate: Upload documents, generate audio, download results
2. Q&A Chat: RAG-based question answering with chat interface
run the code "streamlit run frontend.py"
"""

import streamlit as st
import os
import sys
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

# Import backend modules
from extractor import extract_text
from llm_enrich import enrich_text
from tts import tts_synthesize
from embeddings import generate_embeddings, save_embeddings_csv
from vectordb_save import save_to_vectordb
from rag_langchain import get_vectorstore, query_with_sources

# Page config
st.set_page_config(
    page_title="AI AudioBook Generator",
    page_icon="🎧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Reduce padding and margins */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 1200px;
    }
    
    /* Modern tabs with gradient */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 6px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.95rem;
        background-color: transparent;
        color: rgba(255, 255, 255, 0.7);
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: white;
        color: #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Primary buttons with gradient */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        font-weight: 600;
        padding: 0.6rem 1.2rem;
        transition: all 0.3s;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    /* Secondary buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
        border: 2px solid #e0e0e0;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: #667eea;
    }
    
    /* Expander with gradient header */
    .streamlit-expanderHeader {
        font-size: 0.95rem;
        font-weight: 600;
        background: linear-gradient(90deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 8px;
        padding: 0.8rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        background: linear-gradient(90deg, #e0e7ff 0%, #c7d2fe 100%);
    }
    
    /* Progress bar with animation */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
        background-size: 200% 100%;
        animation: gradient 2s ease infinite;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        padding: 0.5rem !important;
        border: 2px dashed #667eea;
        border-radius: 12px;
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #764ba2;
        background: linear-gradient(135deg, #e0e7ff 0%, #ffffff 100%);
    }
    
    /* Headers */
    h1, h2, h3 {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        color: #1a1a1a;
    }
    
    h2 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Info/Success/Error boxes */
    .stAlert {
        padding: 0.8rem 1rem !important;
        margin: 0.5rem 0 !important;
        border-radius: 10px;
        border-left: 4px solid;
    }
    
    /* Status container */
    [data-testid="stStatusWidget"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #ffffff 100%);
        border-radius: 12px;
        border: 1px solid #e0e0e0;
    }
    
    /* Text areas */
    .stTextArea textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        font-family: 'Courier New', monospace;
    }
    
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Download button styling */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        border-radius: 10px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(17, 153, 142, 0.4);
    }
    
    /* Checkboxes */
    .stCheckbox {
        padding: 0.3rem 0;
    }
    
    /* Audio player */
    audio {
        width: 100%;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'last_audio_path' not in st.session_state:
    st.session_state.last_audio_path = None
if 'last_audio_filename' not in st.session_state:
    st.session_state.last_audio_filename = None
if 'last_extracted_text' not in st.session_state:
    st.session_state.last_extracted_text = None
if 'last_document_name' not in st.session_state:
    st.session_state.last_document_name = None

# Load API key from .env
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# Sidebar - Enhanced version
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h2 style='color: #667eea; margin: 0;'>🎧 AudioBook<br/>Generator</h2>
        <p style='color: #888; font-size: 0.85rem; margin: 0.5rem 0;'>AI-Powered Audio Creation</p>
    </div>
    """, unsafe_allow_html=True)
    
    if api_key:
        st.success("✅ API Key Active", icon="🔑")
    else:
        st.error("❌ No API Key", icon="🔑")
    
    st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 1rem; border-radius: 10px;'>
        <h4 style='margin: 0 0 0.8rem 0; color: #667eea;'>✨ Features</h4>
        <p style='margin: 0.3rem 0; font-size: 0.9rem;'>📤 Multi-format upload</p>
        <p style='margin: 0.3rem 0; font-size: 0.9rem;'>🎙️ High-quality TTS</p>
        <p style='margin: 0.3rem 0; font-size: 0.9rem;'>🤖 AI enhancement</p>
        <p style='margin: 0.3rem 0; font-size: 0.9rem;'>💬 RAG-powered Q&A</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.caption("Built with Streamlit • Edge-TTS • Gemini AI")

# Main header - Enhanced
st.markdown("""
<div style='text-align: center; padding: 1rem 0;'>
    <h1 style='margin: 0; font-size: 2.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 700;'>
        🎧 AI AudioBook Generator
    </h1>
    <p style='margin: 0.5rem 0 0 0; color: #666; font-size: 1rem;'>
        Transform documents into audio • AI-powered enhancement • Smart Q&A
    </p>
</div>
""", unsafe_allow_html=True)
st.markdown("")  # Small spacer

# Main content
tab1, tab2 = st.tabs(["📤 Upload & Generate", "💬 Q&A Chat"])

# ===========================
# TAB 1: Upload & Generate
# ===========================
with tab1:
    # Show last generated audio if exists - Enhanced version
    if st.session_state.last_audio_path and os.path.exists(st.session_state.last_audio_path):
        with st.expander("🎧 Last Generated AudioBook • Ready to Play", expanded=False):
            with open(st.session_state.last_audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
                st.audio(audio_bytes, format="audio/wav")
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.download_button(
                    "📥 Download",
                    data=audio_bytes,
                    file_name=st.session_state.last_audio_filename,
                    mime="audio/wav",
                    use_container_width=True
                )
            with col_b:
                if st.button("🗑️ Clear", use_container_width=True):
                    st.session_state.last_audio_path = None
                    st.session_state.last_audio_filename = None
                    st.rerun()
    
    # Show last extracted text if exists
    if st.session_state.last_extracted_text:
        with st.expander(f"📝 Document Content • {st.session_state.last_document_name}", expanded=False):
            st.text_area(
                "Document content",
                st.session_state.last_extracted_text,
                height=250,
                disabled=True,
                label_visibility="collapsed"
            )
            col_c, col_d, col_e = st.columns(3)
            with col_c:
                st.caption(f"📊 {len(st.session_state.last_extracted_text)} characters")
            with col_d:
                # Download button for extracted text
                txt_filename = st.session_state.last_document_name.rsplit('.', 1)[0] + "_extracted.txt"
                st.download_button(
                    "📥 Download Text",
                    data=st.session_state.last_extracted_text,
                    file_name=txt_filename,
                    mime="text/plain",
                    use_container_width=True
                )
            with col_e:
                if st.button("🗑️ Clear Text", use_container_width=True):
                    st.session_state.last_extracted_text = None
                    st.session_state.last_document_name = None
                    st.rerun()
    
    # Compact upload section
    uploaded_file = st.file_uploader(
        "📄 Choose your document",
        type=['pdf', 'docx', 'txt'],
        help="Upload PDF, DOCX, or TXT file"
    )
    
    # Inline options
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        enhance_text = st.checkbox("🤖 AI Enhance", value=True)
    with col2:
        save_embeddings = st.checkbox("💾 Save for Q&A", value=True)
    
    if uploaded_file is not None:
        # Compact file info
        file_size = uploaded_file.size / 1024
        st.info(f"✅ **{uploaded_file.name}** • {file_size:.1f} KB", icon="📄")
        
        # Generate button
        if st.button("🚀 Generate AudioBook", type="primary", use_container_width=True):
            try:
                with st.status("Processing...", expanded=True) as status:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                
                    # Save uploaded file temporarily
                    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                    temp_dir = tempfile.mkdtemp()
                    temp_file_path = os.path.join(temp_dir, uploaded_file.name)
                    
                    with open(temp_file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Step 1: Extract text
                    status_text.text("📄 Step 1/5: Extracting text from document...")
                    progress_bar.progress(20)
                    
                    extracted_text = extract_text(temp_file_path)
                    
                    if not extracted_text or len(extracted_text.strip()) < 10:
                        st.error("❌ Failed to extract text or text is too short!")
                        st.stop()
                    
                    # Store extracted text in session state
                    st.session_state.last_extracted_text = extracted_text
                    st.session_state.last_document_name = uploaded_file.name
                    
                    st.success(f"✅ Extracted {len(extracted_text)} characters")
                
                    # Step 2: Enhance text (optional)
                    if enhance_text:
                        status_text.text("🤖 Step 2/5: Enhancing text with AI...")
                        progress_bar.progress(40)
                        
                        enriched_text = enrich_text(extracted_text)
                        final_text = enriched_text if enriched_text else extracted_text
                        st.success("✅ Text enhanced for better narration")
                    else:
                        final_text = extracted_text
                        progress_bar.progress(40)
                        st.info("⏭️ Skipped AI enhancement")
                    
                    # Step 3: Generate embeddings and save to vectordb (optional)
                    if save_embeddings:
                        status_text.text("🧠 Step 3/5: Generating embeddings...")
                        progress_bar.progress(60)
                        
                        # Generate embeddings
                        base_name = Path(uploaded_file.name).stem
                        embeddings_result = generate_embeddings(
                            text=final_text,
                            model_name='all-MiniLM-L6-v2',
                            split_method='chunks',
                            chunk_size=400,
                            overlap=50
                        )
                        
                        if embeddings_result:
                            # Unpack the result tuple
                            text_segments, embeddings_array = embeddings_result
                            
                            # Save to CSV
                            csv_path = f"./outputs/embeddings/{base_name}_{timestamp}_embeddings.csv"
                            os.makedirs("./outputs/embeddings", exist_ok=True)
                            save_embeddings_csv(text_segments, embeddings_array, Path(csv_path))
                            
                            # Save to vectordb
                            save_to_vectordb(
                                csv_path=csv_path,
                                collection_name="audiobook_embeddings",
                                persist_directory="./vectordb"
                            )
                            
                            st.success(f"✅ Saved {len(text_segments)} embeddings to vector database")
                            
                            # Reload vectorstore immediately with the new embeddings
                            try:
                                st.session_state.vectorstore = get_vectorstore(
                                    collection_name="audiobook_embeddings",
                                    persist_directory="./vectordb"
                                )
                                st.info("🔄 Vector database reloaded with new document")
                            except Exception as ve:
                                st.warning(f"⚠️ Vector database saved but reload failed: {ve}")
                                st.session_state.vectorstore = None
                        else:
                            st.warning("⚠️ Failed to generate embeddings")
                    else:
                        progress_bar.progress(60)
                        st.info("⏭️ Skipped embedding generation")
                    
                    # Step 4: Generate audio
                    status_text.text("🎤 Step 4/5: Generating audio (this may take a while)...")
                    progress_bar.progress(80)
                    
                    # Create output directory
                    audio_output_dir = "./outputs/audio"
                    os.makedirs(audio_output_dir, exist_ok=True)
                    
                    audio_filename = f"{base_name}_{timestamp}_audio.wav"
                    audio_path = os.path.join(audio_output_dir, audio_filename)
                    
                    # Generate audio using TTS
                    try:
                        # Generate unique basename for audio file
                        audio_basename = f"{base_name}_{timestamp}"
                        audio_result_path = tts_synthesize(
                            text=final_text,
                            engine="edge-tts",  # Using Edge TTS for speed
                            language="en",
                            basename=audio_basename
                        )
                        # Copy to expected location if different
                        if str(audio_result_path) != audio_path:
                            import shutil
                            shutil.copy(str(audio_result_path), audio_path)
                        success = os.path.exists(audio_path)
                    except Exception as e:
                        st.error(f"TTS Error: {str(e)}")
                        success = False
                    
                    if success:
                        status_text.text("✅ Complete!")
                        progress_bar.progress(100)
                        status.update(label="✅ AudioBook Ready!", state="complete")
                        
                        # Store in session
                        st.session_state.last_audio_path = audio_path
                        st.session_state.last_audio_filename = audio_filename
                    else:
                        st.error("❌ Audio generation failed!")
                    
                    # Cleanup temp files
                    shutil.rmtree(temp_dir)
                
            # Display outside status container for better layout
                if 'success' in locals() and success:
                    st.balloons()
                    
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                    
                    st.success("🎉 Generation complete!")
                    st.audio(audio_bytes, format="audio/wav")
                    
                    st.download_button(
                        "📥 Download AudioBook",
                        data=audio_bytes,
                        file_name=audio_filename,
                        mime="audio/wav",
                        type="primary",
                        use_container_width=True
                    )
                    
                    with st.expander("📝 View Text", expanded=False):
                        st.text_area("Processed text", final_text, height=200, disabled=True)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)

# ===========================
# TAB 2: Q&A Chat
# ===========================
with tab2:
    # Initialize vectorstore
    if st.session_state.vectorstore is None:
        try:
            st.session_state.vectorstore = get_vectorstore(
                collection_name="audiobook_embeddings",
                persist_directory="./vectordb"
            )
        except Exception as e:
            st.error(f"❌ Database not found. Upload a document first!", icon="⚠️")
            st.stop()
    
    # Check document count
    try:
        collection_count = st.session_state.vectorstore._collection.count()
        if collection_count == 0:
            st.warning("⚠️ No documents yet. Upload one in the first tab!", icon="📄")
            st.stop()
        
        # Enhanced status bar
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); 
                    padding: 1rem; border-radius: 10px; margin: 1rem 0; text-align: center;'>
            <p style='color: white; margin: 0; font-weight: 600; font-size: 1.1rem;'>
                ✅ Database Ready • {collection_count} text segments loaded
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col2, col3 = st.columns(2)
        with col2:
            if st.button("🔄 Reload Database", use_container_width=True):
                st.session_state.vectorstore = get_vectorstore("audiobook_embeddings", "./vectordb")
                st.rerun()
        with col3:
            if st.button("🗑️ Clear Chat History", use_container_width=True):
                st.session_state.chat_history = []
                st.rerun()
    except Exception as e:
        st.error(f"⚠️ Error: {e}", icon="❌")
    
    # Display chat history
    for i, chat in enumerate(st.session_state.chat_history):
        with st.chat_message("user"):
            st.write(chat["question"])
        with st.chat_message("assistant"):
            st.write(chat["answer"])
            if chat.get("sources"):
                with st.expander("📚 View sources"):
                    st.text(chat["sources"])
    
    # Chat input
    query = st.chat_input("Type your question here...")
    
    if query:
        # Display user message
        with st.chat_message("user"):
            st.write(query)
        
        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Query the RAG system
                    answer = query_with_sources(
                        query=query,
                        vectorstore=st.session_state.vectorstore,
                        top_k=5,
                        show_sources=True,
                        verbose=False
                    )
                    
                    # Split answer and sources
                    if "\n\nSources:\n" in answer:
                        answer_text, sources_text = answer.split("\n\nSources:\n", 1)
                    else:
                        answer_text = answer
                        sources_text = None
                    
                    # Display answer
                    st.write(answer_text)
                    
                    # Display sources in expander
                    if sources_text:
                        with st.expander("📚 View sources"):
                            st.text(sources_text)
                    
                    # Save to chat history
                    st.session_state.chat_history.append({
                        "question": query,
                        "answer": answer_text,
                        "sources": sources_text
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray;'>
    <p>AudioBook Generator Made By Abhishek Roushan | Powered by Bark TTS, LangChain, and Gemini</p>
</div>
""", unsafe_allow_html=True)
