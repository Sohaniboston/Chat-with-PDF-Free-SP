# 🚀 Get Your Free HuggingFace Token (Optional but Recommended)

## Step 1: Sign Up (Free!)
1. Go to https://huggingface.co
2. Click "Sign Up" 
3. Use your email (no credit card needed!)

## Step 2: Get Your Token
1. After signing up, go to: https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it: "Chat with PDF"
4. Permission: Select "Read"
5. Click "Generate"
6. Copy your token

## Step 3: Add to Your .env File
Open your `.env` file and add:
```
HUGGINGFACEHUB_API_TOKEN=hf_your_token_here
```

## Step 4: Restart Your App
```bash
# Stop your app (Ctrl+C in terminal)
conda activate chat_with_pdf
streamlit run app.py
```

## ✅ Without Token (Still Works!)
- The app works fine without a token
- Just might be a bit slower on public inference
- Still completely free!

## ✅ With Token (Better Performance!)
- Faster responses
- More reliable access
- Better model quality
- Still completely free!
