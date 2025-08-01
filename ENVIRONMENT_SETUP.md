# Environment Setup Instructions

## Quick Setup with Conda Environment File

To recreate the exact same environment in the future, use the provided `environment.yml` file:

```bash
# Create environment from the yml file
conda env create -f environment.yml

# Activate the environment
conda activate chat_with_pdf

# Run the application
streamlit run app.py
```

## Manual Setup (Alternative Method)

If you prefer to set up manually:

```bash
# Create new conda environment
conda create -n chat_with_pdf python=3.9 -y

# Activate environment
conda activate chat_with_pdf

# Install packages from requirements.txt
pip install -r requirements.txt
```

## Environment Variables

Don't forget to create a `.env` file based on `example.env` with your API keys:

```
OPENAI_API_KEY=your_openai_api_key_here
HUGGINGFACEHUB_API_TOKEN=your_huggingface_token_here
```

## Running the Application

```bash
conda activate chat_with_pdf
streamlit run app.py
```

The app will be available at: http://localhost:8502
