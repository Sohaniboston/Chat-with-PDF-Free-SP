✅ give me conda enviorment.yml file so i can repeat this process more easy in future.

✅ give me a detail step by step ELI5 explaination of everything that happens in this application. Save the explaination to a markdown file.

✅ Make the app work completely free using HuggingFace models instead of OpenAI (no more quota errors!) 

TODO: 
Improve the application sidebar to give the user a three-way vertical radio button to choose the type of processing.  Include the necessary logic to make this work.  

Choose Type of Process to Use: 
[x] Hugging Face API NO Token (FREE default - slowest)
[x] Hugging Face API Token (FREE requires HF API token - faster)
[x] OpenAI API Key (PAY PER USE - faster than HF API token)


##################################################################################
DONE: Update the Sidebar to look like this with horizontal rules dividing sidebar sections: 

**Chat with PDFs**
-----------------------------
Add Your Documents: 

    Upload Button

-----------------------------
**Configure Processing**
Choose AI Processing Method: 
[x] Hugging Face API NO Token (FREE **DEFAULT** - slowest)
[ ] Hugging Face API Token (FREE requires HF API token - faster)
[ ] OpenAI API Key (PAY PER USE - faster than HF API token)
##################################################################################

##################################################################################
✅ FIXED: FIX THIS WARNING: 
No sentence-transformers model found with name hkunlp/instructor-xl. Creating a new one with mean pooling.
`SentenceTransformer._target_device` has been deprecated, please use `SentenceTransformer.device` instead.

SOLUTION: Changed model to "sentence-transformers/all-MiniLM-L6-v2" and implemented @st.cache_resource
##################################################################################

✅ COMPLETED:  Cache all models locally, do not repeatedly download them. 

✅ IMPLEMENTED: HuggingFace and LLM models are now cached using @st.cache_resource decorator
✅ IMPLEMENTED: Models are only downloaded the very first time the application is run
✅ IMPLEMENTED: Streamlit now knows models are cached after first run  
✅ IMPLEMENTED: Efficient cross-session caching - no repeated downloads of LLM assets
✅ IMPLEMENTED: Added HF_HUB_DISABLE_SYMLINKS_WARNING=1 to suppress Windows symlinks warnings
✅ IMPLEMENTED: Fixed HuggingFaceEndpoint parameter validation errors
✅ FIXED: Updated deprecated Chain.__call__ to use .invoke() method instead
✅ IMPLEMENTED: Enhanced error handling with specific error messages and debug info
✅ CRITICAL FIX: Resolved StopIteration error with retry mechanism and better HuggingFace model handling
✅ IMPLEMENTED: Added retry logic for failed model responses (3 attempts)
✅ OPTIMIZED: Switched to more reliable google/flan-t5-base model with reduced token limits
✅ IMPLEMENTED: Added timeout handling and specific StopIteration error messages 