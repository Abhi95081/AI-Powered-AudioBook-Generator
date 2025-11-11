# Text Embeddings Generation

## Overview
This module generates semantic embeddings for extracted text documents and saves them as CSV files for downstream tasks like semantic search, clustering, or similarity analysis.

## Features
- **Automatic text splitting**: Sentences or custom-sized chunks
- **High-quality embeddings**: Uses sentence-transformers (all-MiniLM-L6-v2 by default)
- **CSV export**: Easy-to-use format with text and embedding columns
- **Flexible chunking**: Supports both sentence-based and word-count-based splitting

## Installation

### Required Packages
```bash
pip install sentence-transformers pandas
```

Or install from requirements.txt:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python embeddings.py "path/to/extracted/text.txt"
```

### Advanced Options
```bash
# Use sentence splitting (default)
python embeddings.py "outputs/text/AI AudioBook Generator_extracted.txt"

# Use chunk-based splitting
python embeddings.py "outputs/text/document.txt" --split chunks --chunk-size 150 --overlap 30

# Specify custom output path
python embeddings.py "outputs/text/document.txt" --output "custom/path/embeddings.csv"

# Use different model
python embeddings.py "outputs/text/document.txt" --model "all-mpnet-base-v2"
```

### Command Line Arguments
- `input_file`: Path to the extracted text file (required)
- `--output` / `-o`: Output CSV path (auto-generated if not provided)
- `--model`: Sentence transformer model name (default: `all-MiniLM-L6-v2`)
- `--split`: Text splitting method - `sentences` or `chunks` (default: `sentences`)
- `--chunk-size`: Words per chunk for chunks method (default: 200)
- `--overlap`: Overlapping words between chunks (default: 50)

## Output Format

### CSV Structure
The generated CSV contains two columns:

| text | embedding |
|------|-----------|
| "AudioBook Generator is a web application..." | [0.123, -0.456, 0.789, ...] |
| "Users select and upload documents..." | [-0.234, 0.567, -0.890, ...] |

- **text**: The original text segment (sentence or chunk)
- **embedding**: 384-dimensional vector representation (as Python list format)

### Example Output
```csv
text,embedding
"AudioBook Generator is a web application that allows users to upload documents.","[0.0423, -0.1245, 0.0876, ..., -0.0234]"
"The backend parses uploaded files and extracts text content.","[-0.0567, 0.0982, -0.1123, ..., 0.0445]"
```

## Python API Usage

### Basic Embedding Generation
```python
from embeddings import generate_embeddings, save_embeddings_csv
from pathlib import Path

# Read text
with open("outputs/text/document.txt", 'r', encoding='utf-8') as f:
    text = f.read()

# Generate embeddings
text_segments, embeddings = generate_embeddings(
    text,
    model_name='all-MiniLM-L6-v2',
    split_method='sentences'
)

# Save to CSV
output_path = Path("outputs/embeddings/document_embeddings.csv")
save_embeddings_csv(text_segments, embeddings, output_path)
```

### Complete Pipeline
```python
from embeddings import process_extracted_text

# Process and save in one step
csv_path = process_extracted_text(
    text_file_path="outputs/text/AI AudioBook Generator_extracted.txt",
    output_csv_path="outputs/embeddings/my_embeddings.csv",
    model_name='all-MiniLM-L6-v2',
    split_method='sentences'
)

print(f"Embeddings saved to: {csv_path}")
```

### Using Embeddings for Similarity Search
```python
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

# Load embeddings CSV
df = pd.read_csv("outputs/embeddings/document_embeddings.csv")

# Convert embedding strings back to numpy arrays
embeddings = np.array([eval(emb) for emb in df['embedding']])

# Example: Find similar sentences to a query
query_idx = 0  # First sentence
similarities = cosine_similarity([embeddings[query_idx]], embeddings)[0]

# Get top 5 most similar
top_5_idx = np.argsort(similarities)[-6:-1][::-1]  # Exclude self

print("Query:", df.iloc[query_idx]['text'])
print("\nMost similar sentences:")
for idx in top_5_idx:
    print(f"- {df.iloc[idx]['text']} (similarity: {similarities[idx]:.3f})")
```

## Available Models

### Recommended Models
| Model | Dimension | Speed | Quality | Use Case |
|-------|-----------|-------|---------|----------|
| `all-MiniLM-L6-v2` | 384 | Fast | Good | **Default** - General purpose |
| `all-mpnet-base-v2` | 768 | Medium | Best | High accuracy needed |
| `all-MiniLM-L12-v2` | 384 | Medium | Better | Balance of speed and quality |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | Medium | Good | Multilingual support |

### Changing Models
```bash
# Use highest quality model (slower, larger embeddings)
python embeddings.py "document.txt" --model "all-mpnet-base-v2"

# Use multilingual model
python embeddings.py "document.txt" --model "paraphrase-multilingual-MiniLM-L12-v2"
```

## Text Splitting Methods

### 1. Sentence Splitting (Default)
Splits text by sentence boundaries (`.`, `!`, `?`). Best for:
- Natural language documents
- Semantic coherence
- Question-answering tasks

```bash
python embeddings.py "document.txt" --split sentences
```

### 2. Chunk Splitting
Splits text into fixed-size chunks with overlap. Best for:
- Long documents
- Fixed-size embeddings
- Sliding window analysis

```bash
python embeddings.py "document.txt" --split chunks --chunk-size 200 --overlap 50
```

## Troubleshooting

### Model Download Issues
If the model download is interrupted or slow:

1. **Manual Download**:
   ```python
   from sentence_transformers import SentenceTransformer
   
   # This will download and cache the model
   model = SentenceTransformer('all-MiniLM-L6-v2')
   print("Model downloaded successfully!")
   ```

2. **Check Cache**:
   - Models are cached in: `C:\Users\<USERNAME>\.cache\huggingface\hub\`
   - If partial download, delete the folder and retry

3. **Network Issues**:
   - Ensure stable internet connection
   - Try from a different network
   - Use VPN if corporate firewall blocks HuggingFace

### Memory Issues
For very large documents:
- Use chunk splitting with smaller chunk size
- Process in batches
- Use a smaller model (MiniLM-L6-v2 instead of mpnet)

### Import Errors
```bash
# If sentence-transformers import fails
pip install --upgrade sentence-transformers torch

# If pandas import fails
pip install pandas
```

## Output Location

By default, embeddings are saved to:
```
outputs/embeddings/<source_filename>_embeddings.csv
```

Example:
- Input: `outputs/text/AI AudioBook Generator_extracted_20251111-180528_extracted.txt`
- Output: `outputs/embeddings/AI AudioBook Generator_extracted_20251111-180528_extracted_embeddings.csv`

## Performance

### Processing Times (approximate)
- **500 words**: ~10-15 seconds (first run + model download: 2-3 minutes)
- **1000 words**: ~20-30 seconds
- **5000 words**: ~1-2 minutes

### Model Sizes
- `all-MiniLM-L6-v2`: ~90 MB
- `all-mpnet-base-v2`: ~420 MB
- `all-MiniLM-L12-v2`: ~120 MB

## Integration with Pipeline

### Complete Workflow
```bash
# 1. Extract text from document
python pipeline.py "uploads/document.pdf"

# 2. Generate embeddings
python embeddings.py "outputs/text/document_extracted_*.txt"

# 3. Use embeddings for downstream tasks
python your_analysis_script.py "outputs/embeddings/document_embeddings.csv"
```

## Next Steps

After generating embeddings, you can:
1. **Semantic Search**: Find similar passages
2. **Clustering**: Group related content
3. **Classification**: Train classifiers on embeddings
4. **Similarity Analysis**: Compare documents
5. **Recommendation**: Suggest related content

## Support

For issues or questions:
1. Check the main README.md
2. Review sentence-transformers documentation: https://www.sbert.net/
3. Check HuggingFace model hub: https://huggingface.co/sentence-transformers
