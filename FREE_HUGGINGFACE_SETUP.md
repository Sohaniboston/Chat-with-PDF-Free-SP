# Free HuggingFace Setup Guide 🤗

## Why Use HuggingFace Instead of OpenAI?

- **100% FREE** - No credit card required
- **No usage limits** - Use as much as you want
- **Privacy-focused** - Your data stays more private
- **Open source models** - Community-driven AI

## Quick Setup (Optional but Recommended)

### Step 1: Get a Free HuggingFace Token
1. Go to [HuggingFace](https://huggingface.co)
2. Click "Sign Up" (it's free!)
3. Verify your email
4. Go to [Settings > Access Tokens](https://huggingface.co/settings/tokens)
5. Click "New token"
6. Give it a name like "Chat with PDF"
7. Select "Read" permission
8. Click "Generate"
9. Copy your token

### Step 2: Add to Your .env File
Open your `.env` file and add:
```
HUGGINGFACEHUB_API_TOKEN=your_token_here
```

### Step 3: Remove OpenAI Key (Optional)
If you want to force the app to use only free models, change your `.env` file:
```
OPENAI_API_KEY=
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
```

## What Changes?

### With HuggingFace Token:
- ✅ Faster responses
- ✅ Better model quality
- ✅ More reliable access

### Without Token (Still Free):
- ⚠️ Slower responses (public inference)
- ⚠️ May have occasional timeouts
- ✅ Still completely free!

## Models Being Used

### For Embeddings (Text Understanding):
- **hkunlp/instructor-xl** - Excellent at understanding document meaning

### For Conversations (Chat):
- **microsoft/DialoGPT-large** - Good at natural conversations
- Alternatives: google/flan-t5-large, facebook/blenderbot-400M-distill

## Restart Your App

After making changes to `.env`:
1. Stop your Streamlit app (Ctrl+C in terminal)
2. Restart it: `streamlit run app.py`
3. The app will now use free HuggingFace models!

## Performance Comparison

| Feature | OpenAI | HuggingFace |
|---------|--------|-------------|
| Cost | $$ (Paid) | 🆓 FREE |
| Speed | Very Fast | Moderate |
| Quality | Excellent | Very Good |
| Privacy | Good | Better |
| Limits | Usage-based | None |

Your app now works completely free! 🎉
