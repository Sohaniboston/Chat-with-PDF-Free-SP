import streamlit as st
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings, HuggingFaceInstructEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.chat_models import ChatOpenAI

from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from htmlTemplates import css, bot_template, user_template, hide_st_style, footer
from langchain_community.llms import HuggingFaceHub
from matplotlib import style

# Load environment variables
load_dotenv()

# Check API keys - OpenAI is optional, HuggingFace is recommended
openai_key = os.getenv("OPENAI_API_KEY")
hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")

if not openai_key or openai_key == "your_openai_api_key_here":
    st.info("💡 No OpenAI API key found. The app will use free HuggingFace models instead!")
    if not hf_token:
        st.warning("⚠️ Consider adding a HuggingFace API token to .env for better performance.")
        st.info("Get one free at: https://huggingface.co/settings/tokens")
else:
    st.success("✅ OpenAI API key found - will try OpenAI first, with HuggingFace fallback.")


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


def get_vectorstore(text_chunks):
    if not text_chunks:
        st.error("No text chunks available to create vector store.")
        return None
    
    try:
        # Try OpenAI embeddings first
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
            try:
                embeddings = OpenAIEmbeddings()
                st.info(f"Using OpenAI embeddings to create vector store from {len(text_chunks)} text chunks...")
                vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
                st.success("Vector store created successfully with OpenAI embeddings!")
                return vectorstore
            except Exception as openai_error:
                if "quota" in str(openai_error).lower() or "429" in str(openai_error):
                    st.warning("OpenAI quota exceeded. Switching to free HuggingFace embeddings...")
                else:
                    st.warning(f"OpenAI error: {str(openai_error)}. Switching to free HuggingFace embeddings...")
        
        # Fallback to HuggingFace embeddings (free)
        st.info("Using free HuggingFace embeddings (this may take a moment to download the model first time)...")
        embeddings = HuggingFaceInstructEmbeddings(model_name="hkunlp/instructor-xl")
        
        st.info(f"Creating vector store from {len(text_chunks)} text chunks...")
        vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
        st.success("Vector store created successfully with HuggingFace embeddings!")
        return vectorstore
        
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return None


def get_conversation_chain(vectorstore):
    try:
        # Try OpenAI first if API key is available and valid
        if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
            try:
                llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
                st.info("Using OpenAI ChatGPT for conversations...")
                
                memory = ConversationBufferMemory(
                    memory_key='chat_history', return_messages=True)
                conversation_chain = ConversationalRetrievalChain.from_llm(
                    llm=llm,
                    retriever=vectorstore.as_retriever(),
                    memory=memory
                )
                st.success("Conversation system ready with OpenAI!")
                return conversation_chain
                
            except Exception as openai_error:
                if "quota" in str(openai_error).lower() or "429" in str(openai_error):
                    st.warning("OpenAI quota exceeded. Switching to free HuggingFace model...")
                else:
                    st.warning(f"OpenAI error: {str(openai_error)}. Switching to free HuggingFace model...")
        
        # Fallback to HuggingFace Hub (completely free)
        st.info("Using free HuggingFace model for conversations (this may be slower but completely free)...")
        
        # Get HuggingFace API token if available
        hf_token = os.getenv("HUGGINGFACEHUB_API_TOKEN")
        if not hf_token:
            st.warning("No HuggingFace API token found. Using public inference (may be slower).")
        
        # Use a free, powerful model from HuggingFace
        llm = HuggingFaceHub(
            repo_id="google/flan-t5-large",  # Better for Q&A tasks
            model_kwargs={
                "temperature": 0.1, 
                "max_length": 512,
                "max_new_tokens": 200
            },
            huggingfacehub_api_token=hf_token
        )
        
        memory = ConversationBufferMemory(
            memory_key='chat_history', return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )
        st.success("Conversation system ready with HuggingFace!")
        return conversation_chain
        
    except Exception as e:
        st.error(f"Error creating conversation chain: {str(e)}")
        st.error("Please check your API keys or try again later.")
        return None


def handle_userinput(user_question):
    if st.session_state.conversation is None:
        st.error("Please upload PDF data before starting the chat.")
        return

    try:
        with st.spinner("Thinking..."):
            response = st.session_state.conversation({'question': user_question})
            st.session_state.chat_history = response['chat_history']

        for i, message in enumerate(st.session_state.chat_history):
            if i % 2 == 0:
                st.write(user_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
            else:
                st.write(bot_template.replace(
                    "{{MSG}}", message.content), unsafe_allow_html=True)
                    
    except Exception as e:
        if "quota" in str(e).lower() or "429" in str(e):
            st.error("❌ OpenAI quota exceeded! Please restart the app to use free HuggingFace models.")
            st.info("💡 Refresh the page and reprocess your documents to use the free fallback.")
        else:
            st.error(f"Error during conversation: {str(e)}")
            st.info("💡 Try refreshing the page and reprocessing your documents.")


def main():
    load_dotenv()
    st.set_page_config(page_title="Talk with PDF",
                       page_icon="icon.png")
    st.write(css, unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = None

    st.header("Chat with AI with Custom Data 🚀")
    user_question = st.text_input("Ask a question about your Data:")

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader(
            "Upload your Data here  in PDF format and click on 'Process'", accept_multiple_files=True, type=['pdf'])

        if st.button("Process"):
            if pdf_docs is None or len(pdf_docs) == 0:
                st.error("Please upload at least one PDF file.")
            else:
                with st.spinner("Processing"):
                    # Extract text from PDFs
                    raw_text = get_pdf_text(pdf_docs)
                    
                    if not raw_text:
                        st.error("No text could be extracted from the uploaded PDFs.")
                        return
                    
                    # Create text chunks
                    text_chunks = get_text_chunks(raw_text)
                    
                    if not text_chunks:
                        st.error("No text chunks could be created.")
                        return
                    
                    # Create vector store
                    vectorstore = get_vectorstore(text_chunks)
                    
                    if vectorstore is None:
                        st.error("Failed to create vector store.")
                        return
                    
                    # Create conversation chain
                    conversation = get_conversation_chain(vectorstore)
                    
                    if conversation is None:
                        st.error("Failed to create conversation system.")
                        return
                    
                    st.session_state.conversation = conversation
                    st.success("Your Data has been processed successfully")

    if user_question:
        handle_userinput(user_question)

    st.markdown(hide_st_style, unsafe_allow_html=True)
    st.markdown(footer, unsafe_allow_html=True)


if __name__ == '__main__':
    main()
