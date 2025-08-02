import streamlit as st
from dotenv import load_dotenv
import os
import logging
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template, hide_st_style, footer
from langchain_huggingface import HuggingFaceEndpoint
from matplotlib import style

# Configure logging to suppress warnings from libraries
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("langchain").setLevel(logging.ERROR)
logging.getLogger("langchain_core").setLevel(logging.ERROR)
logging.getLogger("langchain_community").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

# Disable HuggingFace symlinks warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
# Suppress additional warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
# Suppress sentence-transformers device warnings
os.environ["SENTENCE_TRANSFORMERS_DEVICE_DEPRECATION"] = "ignore"
# Additional warning suppression
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_VERBOSITY"] = "error"

import warnings
# Suppress all types of warnings that appear in the console
warnings.filterwarnings("ignore")  # Suppress all warnings
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=PendingDeprecationWarning)
warnings.filterwarnings("ignore", module="sentence_transformers")
warnings.filterwarnings("ignore", module="langchain")
warnings.filterwarnings("ignore", module="transformers")
warnings.filterwarnings("ignore", module="huggingface_hub")
warnings.filterwarnings("ignore", module="langchain_community")
warnings.filterwarnings("ignore", module="langchain_core")
# Suppress specific LangChain deprecation warnings
warnings.filterwarnings("ignore", message=".*migrating_memory.*")
warnings.filterwarnings("ignore", message=".*_target_device.*")
warnings.filterwarnings("ignore", message=".*deprecated.*")
warnings.filterwarnings("ignore", message=".*ConversationBufferMemory.*")

# Check API keys availability (for informational purposes only)
openai_key = os.getenv("OPENAI_API_KEY")
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

# Note: No more automatic warnings - users will choose their processing mode explicitly


@st.cache_resource
def get_embeddings_model():
    """Cache the embeddings model to avoid repeated downloads"""
    return HuggingFaceInstructEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


@st.cache_resource
def get_llm_model(processing_mode="hf_no_token"):
    """Cache the LLM model to avoid repeated downloads"""
    if processing_mode == "hf_with_token":
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
    else:
        hf_token = None
    
    return HuggingFaceEndpoint(
        repo_id="google/flan-t5-small",  # Smaller, more reliable for public inference
        temperature=0.1,
        max_new_tokens=100,  # Conservative for reliability
        timeout=30,  # Reasonable timeout
        huggingfacehub_api_token=hf_token
    )


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            st.info(f"Processing PDF: {pdf.name} ({len(pdf_reader.pages)} pages)")
            
            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += page_text
                else:
                    st.warning(f"No text found on page {page_num + 1} of {pdf.name}")
                    
        except Exception as e:
            st.error(f"Error reading PDF {pdf.name}: {str(e)}")
            
    if not text.strip():
        st.error("No readable text found in any of the uploaded PDF files.")
        return ""
    
    st.success(f"Extracted {len(text)} characters from PDF files.")
    return text


def get_text_chunks(text):
    if not text or len(text.strip()) == 0:
        st.error("No text found in the PDF files. Please check if the PDFs contain readable text.")
        return []
    
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    if not chunks:
        st.error("No text chunks created. The PDF might be empty or unreadable.")
        return []
    
    st.info(f"Created {len(chunks)} text chunks for processing.")
    return chunks


def get_vectorstore(text_chunks, processing_mode="hf_no_token"):
    if not text_chunks:
        st.error("No text chunks available to create vector store.")
        return None
    
    try:
        # Determine which embeddings to use based on user choice
        if processing_mode == "openai":
            # Try OpenAI embeddings first
            if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
                try:
                    embeddings = OpenAIEmbeddings()
                    st.info(f"🚀 Using OpenAI embeddings (user selected) - creating vector store from {len(text_chunks)} text chunks...")
                    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
                    st.success("✅ Vector store created successfully with OpenAI embeddings!")
                    return vectorstore
                except Exception as openai_error:
                    if "quota" in str(openai_error).lower() or "429" in str(openai_error):
                        st.error("❌ OpenAI quota exceeded! Falling back to HuggingFace embeddings...")
                    else:
                        st.error(f"❌ OpenAI error: {str(openai_error)}. Falling back to HuggingFace embeddings...")
            else:
                st.error("❌ No valid OpenAI API key found! Please add it to your .env file or choose a different processing mode.")
                st.info("💡 Switching to HuggingFace embeddings...")
        
        # Use HuggingFace embeddings (free) - works with or without token
        st.info("🤗 Using free HuggingFace embeddings (cached - faster after first run)...")
        embeddings = get_embeddings_model()  # Use cached model
        
        st.info(f"🔄 Creating vector store from {len(text_chunks)} text chunks...")
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
        st.success("✅ Vector store created successfully with HuggingFace embeddings!")
        return vectorstore
        
    except Exception as e:
        st.error(f"❌ Error creating vector store: {str(e)}")
        return None


def get_conversation_chain(vectorstore, processing_mode="hf_no_token"):
    try:
        # Handle OpenAI mode
        if processing_mode == "openai":
            if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
                try:
                    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
                    st.info("🚀 Using OpenAI ChatGPT for conversations (user selected)...")
                    
                    memory = ConversationBufferMemory(
                        memory_key='chat_history', return_messages=True)
                    conversation_chain = ConversationalRetrievalChain.from_llm(
                        llm=llm,
                        retriever=vectorstore.as_retriever(),
                        memory=memory
                    )
                    st.success("✅ Conversation system ready with OpenAI!")
                    return conversation_chain
                    
                except Exception as openai_error:
                    if "quota" in str(openai_error).lower() or "429" in str(openai_error):
                        st.error("❌ OpenAI quota exceeded! Falling back to HuggingFace model...")
                    else:
                        st.error(f"❌ OpenAI error: {str(openai_error)}. Falling back to HuggingFace model...")
            else:
                st.error("❌ No valid OpenAI API key found! Please add it to your .env file or choose a different processing mode.")
                st.info("💡 Switching to HuggingFace model...")
        
        # Handle HuggingFace modes (with or without token)
        if processing_mode == "hf_with_token":
            st.info("🤗 Using HuggingFace model with API token for faster responses (cached)...")
            hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
            if not hf_token:
                st.warning("⚠️ No HuggingFace API token found in .env file!")
                st.info("💡 Get one free at: https://huggingface.co/settings/tokens")
                st.info("🔄 Falling back to public inference (no token mode)...")
                processing_mode = "hf_no_token"  # Switch to no token mode
        else:
            st.info("🤗 Using HuggingFace model with public inference (cached - faster after first run)...")
        
        # Use cached HuggingFace model
        llm = get_llm_model(processing_mode)
        
        memory = ConversationBufferMemory(
            memory_key='chat_history', return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
        
        if processing_mode == "hf_with_token" and hf_token:
            st.success("✅ Conversation system ready with HuggingFace (with token - faster responses)!")
        else:
            st.success("✅ Conversation system ready with HuggingFace (public inference - completely free)!")
        
        return conversation_chain
        
    except Exception as e:
        st.error(f"❌ Error creating conversation chain: {str(e)}")
        st.error("Please check your API keys or try again later.")
        return None


def handle_userinput(user_question):
    if st.session_state.conversation is None:
        st.error("Please upload PDF data before starting the chat.")
        return

    try:
        with st.spinner("Thinking..."):
            # Try to get response with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Format the question better for the model
                    formatted_question = f"Based on the document context, please answer: {user_question}"
                    response = st.session_state.conversation.invoke({'question': formatted_question})
                    st.session_state.chat_history = response['chat_history']
                    break  # Success, exit retry loop
                except StopIteration:
                    if attempt < max_retries - 1:
                        st.warning(f"⚠️ Model didn't respond (attempt {attempt + 1}/{max_retries}). Retrying...")
                        continue
                    else:
                        st.error("❌ The AI model is not responding. This often happens with HuggingFace public inference during high traffic.")
                        st.info("💡 **Try these solutions:**")
                        st.info("1. Wait a few minutes and try again")
                        st.info("2. Try a shorter, simpler question")  
                        st.info("3. Get a free HuggingFace API token for more reliable responses")
                        st.info("4. Switch to OpenAI if you have credits")
                        return
                except Exception as e:
                    if attempt < max_retries - 1:
                        st.warning(f"⚠️ Error occurred (attempt {attempt + 1}/{max_retries}): {str(e)}")
                        continue
                    else:
                        raise e  # Re-raise the last exception

        # Display conversation history
        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
                    
    except StopIteration:
        st.error("❌ The AI model stopped generating a response unexpectedly.")
        st.info("💡 **This is a common issue with free HuggingFace inference. Try:**")
        st.info("• Asking a shorter question")
        st.info("• Waiting a few minutes for server load to decrease") 
        st.info("• Getting a free HuggingFace API token for better reliability")
    except Exception as e:
        st.error(f"❌ Error during conversation: {str(e)}")
        if "quota" in str(e).lower() or "429" in str(e):
            st.info("💡 This appears to be an API quota issue. Try switching to a different processing mode in the sidebar.")
        elif "timeout" in str(e).lower():
            st.info("💡 Request timed out. Please try asking a shorter question or try again.")
        elif "token" in str(e).lower():
            st.info("💡 This might be a token issue. Check your API keys in the .env file.")
        else:
            st.info("💡 Try refreshing the page and reprocessing your documents, or switch to a different processing mode.")
            st.info(f"🔧 **Debug info**: {type(e).__name__}: {str(e)}")


def main():
    load_dotenv()
    st.set_page_config(page_title="Talk with PDF",
                       page_icon="icon.png")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None
    if "processing_mode" not in st.session_state:
        st.session_state.processing_mode = "hf_no_token"  # Default to free mode

    st.header("Chat with AI with Custom Data 🚀")
    user_question = st.text_input("Ask a question about your Data:")

    with st.sidebar:
        # Chat with PDFs Section
        st.markdown("### **Chat with PDFs**")
        st.markdown("---")
        
        st.subheader("📄 Add Your Documents:")
        pdf_docs = st.file_uploader(
            "Upload your Data here in PDF format and click on 'Process'", 
            accept_multiple_files=True, 
            type=['pdf']
        )
        
        # Process Button - moved above configuration and made primary
        if st.button("Process", type="primary", use_container_width=True):
            if pdf_docs is None or len(pdf_docs) == 0:
                st.error("Please upload at least one PDF file.")
            else:
                # Processing options for display
                processing_options = {
                    "hf_no_token": "🆓 HuggingFace NO Token (FREE **DEFAULT** - slowest)",
                    "hf_with_token": "⚡ HuggingFace Token (FREE requires HF API token - faster)", 
                    "openai": "💨 OpenAI API Key (PAY PER USE - faster than HF API token)"
                }
                
                with st.spinner(f"Processing with {processing_options[st.session_state.processing_mode]}..."):
                    # Extract text from PDFs
                    raw_text = get_pdf_text(pdf_docs)
                    
                    if not raw_text:
                        st.error("No text could be extracted from the uploaded PDFs.")
                        st.stop()
                    
                    # Create text chunks
                    text_chunks = get_text_chunks(raw_text)
                    
                    if not text_chunks:
                        st.error("No text chunks could be created.")
                        st.stop()
                    
                    # Create vector store with selected processing mode
                    vectorstore = get_vectorstore(text_chunks, st.session_state.processing_mode)
                    
                    if vectorstore is None:
                        st.error("Failed to create vector store.")
                        st.stop()
                    
                    # Create conversation chain with selected processing mode
                    conversation = get_conversation_chain(vectorstore, st.session_state.processing_mode)
                    
                    if conversation is None:
                        st.error("Failed to create conversation system.")
                        st.stop()
                    
                    st.session_state.conversation = conversation
                    st.balloons()
                    st.success(f"🎉 Your Data has been processed successfully using {processing_options[st.session_state.processing_mode]}!")

        # Processing Configuration Section
        st.markdown("---")
        st.markdown("### **Configure Processing**")
        
        # Radio button for processing mode selection
        processing_options = {
            "hf_no_token": "🆓 HuggingFace NO Token (FREE **DEFAULT** - slowest)",
            "hf_with_token": "⚡ HuggingFace Token (FREE requires HF API token - faster)", 
            "openai": "💨 OpenAI API Key (PAY PER USE - faster than HF API token)"
        }
        
        selected_mode = st.radio(
            "Choose AI Processing Method:",
            options=list(processing_options.keys()),
            format_func=lambda x: processing_options[x],
            index=0,  # Default to first option (hf_no_token)
            help="Select your preferred AI processing method"
        )
        
        # Store the selected mode in session state
        st.session_state.processing_mode = selected_mode
        
        # Show additional info based on selection
        if selected_mode == "hf_no_token":
            pass  # No additional info needed for default free option
        elif selected_mode == "hf_with_token":
            if not os.getenv("HUGGINGFACEHUB_API_TOKEN"):
                st.warning("⚠️ No HuggingFace token found in .env file!")
        elif selected_mode == "openai":
            st.info("💳 **OpenAI Account Required:**\n- Costs ~$0.002 per response\n- Fastest response time: ~2-8 seconds")
            if not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") == "your_openai_api_key_here":
                st.warning("⚠️ No OpenAI API key found in .env file!")
                st.info("🔑 Add `OPENAI_API_KEY=your_key` to .env file")

    # Show current processing mode info
    if st.session_state.conversation:
        current_mode = st.session_state.processing_mode
        processing_options = {
            "hf_no_token": "🆓 HuggingFace NO Token (FREE **DEFAULT** - slowest)",
            "hf_with_token": "⚡ HuggingFace Token (FREE requires HF API token - faster)", 
            "openai": "💨 OpenAI API Key (PAY PER USE - faster than HF API token)"
        }
        st.sidebar.success(f"✅ Ready with: {processing_options[current_mode]}")

    if user_question:
        handle_userinput(user_question)

    st.markdown(hide_st_style, unsafe_allow_html=True)
    st.markdown(footer, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
