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
    page_title="AudioBook Generator",
    page_icon="🎧",
    layout="wide"
)

# Initialize session state
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vectorstore' not in st.session_state:
    st.session_state.vectorstore = None
if 'last_audio_path' not in st.session_state:
    st.session_state.last_audio_path = None
if 'last_audio_filename' not in st.session_state:
    st.session_state.last_audio_filename = None

# Sidebar
with st.sidebar:
    st.title("🎧 AudioBook Generator")
    st.markdown("---")
    st.info("""
    **Features:**
    - Upload PDF, DOCX, TXT files
    - Generate high-quality audiobooks
    - AI-powered text enhancement
    - RAG-based Q&A system
    """)
    
    # API Key configuration
    st.markdown("---")
    st.subheader("⚙️ Configuration")
    
    # Load API key from .env
    from dotenv import load_dotenv
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    
    if api_key:
        st.success("✅ API Key loaded from .env")
    else:
        st.warning("⚠️ No API key found in .env")

# Main content
tab1, tab2 = st.tabs(["📤 Upload & Generate", "💬 Q&A Chat"])

# ===========================
# TAB 1: Upload & Generate
# ===========================
with tab1:
    st.header("📤 Upload Document & Generate Audio")
    
    # Show last generated audio if exists
    if st.session_state.last_audio_path and os.path.exists(st.session_state.last_audio_path):
        st.markdown("---")
        st.subheader("🎧 Last Generated AudioBook")
        
        with open(st.session_state.last_audio_path, "rb") as audio_file:
            audio_bytes = audio_file.read()
            st.audio(audio_bytes, format="audio/wav")
        
        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.download_button(
                label="📥 Download AudioBook",
                data=audio_bytes,
                file_name=st.session_state.last_audio_filename,
                mime="audio/wav",
                use_container_width=True
            )
        with col_b:
            if st.button("🗑️ Clear Audio", use_container_width=True):
                st.session_state.last_audio_path = None
                st.session_state.last_audio_filename = None
                st.rerun()
        st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded_file = st.file_uploader(
            "Choose a file (PDF, DOCX, TXT)",
            type=['pdf', 'docx', 'txt'],
            help="Upload your document to convert to audiobook"
        )
    
    with col2:
        st.markdown("### Options")
        enhance_text = st.checkbox("🤖 Enhance text with AI", value=True)
        save_embeddings = st.checkbox("💾 Save to vector database", value=True)
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        # Show file details
        file_size = uploaded_file.size / 1024  # KB
        st.info(f"📊 File size: {file_size:.2f} KB")
        
        # Generate button
        if st.button("🚀 Generate AudioBook", type="primary", use_container_width=True):
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
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
                    # Step 5: Complete
                    status_text.text("✅ Step 5/5: AudioBook generation complete!")
                    progress_bar.progress(100)
                    
                    st.success("🎉 AudioBook generated successfully!")
                    
                    # Store audio path in session state
                    st.session_state.last_audio_path = audio_path
                    st.session_state.last_audio_filename = audio_filename
                    
                    # Display audio player
                    st.markdown("---")
                    st.subheader("🎧 Listen to Your AudioBook")
                    
                    with open(audio_path, "rb") as audio_file:
                        audio_bytes = audio_file.read()
                        st.audio(audio_bytes, format="audio/wav")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download AudioBook",
                        data=audio_bytes,
                        file_name=audio_filename,
                        mime="audio/wav",
                        use_container_width=True
                    )
                    
                    # Show text preview
                    with st.expander("📝 View processed text"):
                        st.text_area("Text content", final_text, height=300)
                    
                else:
                    st.error("❌ Audio generation failed!")
                
                # Cleanup temp files
                shutil.rmtree(temp_dir)
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.exception(e)
                progress_bar.empty()
                status_text.empty()

# ===========================
# TAB 2: Q&A Chat
# ===========================
with tab2:
    st.header("💬 Question & Answer Chat")
    
    # Initialize or reload vectorstore
    if st.session_state.vectorstore is None:
        try:
            st.session_state.vectorstore = get_vectorstore(
                collection_name="audiobook_embeddings",
                persist_directory="./vectordb"
            )
            st.success("✅ Vector database loaded successfully")
        except Exception as e:
            st.error(f"❌ Failed to load vector database: {str(e)}")
            st.info("💡 Please upload a document in the 'Upload & Generate' tab first")
            st.stop()
    
    # Check if collection has any documents
    try:
        # Try to get collection info
        collection_count = st.session_state.vectorstore._collection.count()
        if collection_count == 0:
            st.warning("⚠️ No documents in the database. Please upload a document in the 'Upload & Generate' tab first.")
            st.stop()
        else:
            st.info(f"📚 Database contains {collection_count} text segments from your uploaded documents")
    except Exception as e:
        st.warning(f"⚠️ Could not verify document count: {e}")
    
    # Chat interface
    st.markdown("Ask questions about your uploaded documents:")
    
    # Add refresh button and clear chat button in columns
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔄 Reload Database", help="Refresh the vector database after uploading new documents"):
            st.session_state.vectorstore = get_vectorstore(
                collection_name="audiobook_embeddings",
                persist_directory="./vectordb"
            )
            st.success("✅ Database reloaded!")
            st.rerun()
    with col2:
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.success("✅ Chat history cleared!")
            st.rerun()
    
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
    <p>AudioBook Generator | Powered by Bark TTS, LangChain, and Gemini</p>
</div>
""", unsafe_allow_html=True)
