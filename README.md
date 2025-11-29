# Luxis
Luxis — a local embedding, indexing, and semantic search tool.  
It scans files, extracts text, embeds content via OpenAI or Azure OpenAI, and enables fast local semantic queries powered by FAISS.

## Usage
### Ingest
Performs scanning, embedding, and indexing of files:
```bash
$ luxis index --config .luxis.toml
25-11-29 11:53:15|ℹ️|...s/core/indexing.py:20 | Vector index initialized at /tmp/luxis/data/vector_index.faiss (dim=1536)
25-11-29 11:53:15|ℹ️|...s/core/indexing.py:21 | Meta index initialized at /tmp/luxis/data/meta_index.db
25-11-29 11:53:15|ℹ️|...services/update.py:52 | Updating index...
25-11-29 11:53:15|ℹ️|...services/update.py:16 | Scanning ., found 31 files
25-11-29 11:53:16|ℹ️|...services/update.py:40 | Falling back to single embeddings.
25-11-29 11:53:19|ℹ️|...s/core/indexing.py:32 | Index updated and saved (2 entries).
25-11-29 11:53:19|✅|...services/update.py:60 | Index updated with 2 files.
25-11-29 11:53:19|ℹ️|...s/core/indexing.py:50 | No missing files to prune.
25-11-29 11:53:19|ℹ️|...services/update.py:63 | Index update complete. (Elapsed 3.48s)
```

### Query
Executes a semantic search query over the indexed embeddings:
```bash
$ luxis query "pydantic settings" --config .luxis.toml
25-11-29 11:53:39|ℹ️|...s/services/query.py:9 | Running query...
25-11-29 11:53:40|ℹ️|...s/core/indexing.py:20 | Vector index initialized at /tmp/luxis/data/vector_index.faiss (dim=1536)
25-11-29 11:53:40|ℹ️|...s/core/indexing.py:21 | Meta index initialized at /tmp/luxis/data/meta_index.db
25-11-29 11:53:41|ℹ️|.../services/query.py:24 | Top 10 similar files:
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  1. luxis/__init__.py  (hash=91447944015cec709e8aa7655f7e9d64e1e4508e7023a57fe3746911c0fc6fed)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  2. luxis/core/schemas.py  (hash=e5433449c6067c4ab2cf602b8966998132abc8332a50932e82535ded771e9840)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  3. .luxis.template.toml  (hash=d2699e4ad7db98728d2de04f898b9a8e3b4662f9825170ec6c61656a7f03fdfe)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  4. .luxis.toml  (hash=f3eaf7063f11467cc8fd1710d98975464296c23ef059ecbffcd87bc5527c6cba)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  5. .flake8  (hash=a36b443c5090742093ca6ab3ff208f61395362b34cc0ca7e975e07d29dc0ae4e)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  6. .gitignore  (hash=630feca53a8532eea145c09598f9147ebf134d27e8b6f01e6f9c73a238769a17)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  7. .ruff_cache/CACHEDIR.TAG  (hash=5953156d7e0c564a427251316eaf26f8870e6483ae2197f916b630e4f93e31ae)
25-11-29 11:53:41|ℹ️|.../services/query.py:27 |  8. pyproject.toml  (hash=dfbaefe008eb1df2deb9ba9f9c85778da3117bbaee3dfa18de2ab9e2a3f56f9c)
25-11-29 11:53:41|✅|.../services/query.py:28 | Query completed.
```

### Daemon
Runs the Luxis HTTP service daemon for remote operations:
```bash
$ luxis daemon start --config .luxis.toml
25-11-29 13:59:45|ℹ️|...luxis/luxis/daemon.py:97 | Luxis daemon running on 127.0.0.1:8765
INFO:     Started server process [54457]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

To stop the service:
```bash
$ luxis daemon stop --config .luxis.toml
```

## Features
- Configurable through `.toml` configuration file (`luxis.toml`)
- Supports both **OpenAI** and **Azure OpenAI** via the `openai` Python package
- Asynchronous batching of text embeddings
- Automatic token count management and batching fallback
- Text extraction through Apache Tika
- Robust file scanning with include/ignore patterns
- Vector index using **FAISS**, metadata index using **SQLite**
- Automatic pruning of missing files from index
- CLI interface built with **Click**
- Runs as a local HTTP daemon for background indexing and querying
- Structured logging via **Loguru**
- Pydantic-based configuration models:
  - `IngestConfig` (embedding dimension)
  - `QueryConfig` (top_k)
  - `GeneralSettings` (index paths, log level, provider type)

## License
MIT License  
Copyright (c) 2024  
Permission is hereby granted, free of charge, to any person obtaining a copy  
of this software and associated documentation files, to deal in the Software  
without restriction, including without limitation the rights to use, copy,  
modify, merge, publish, distribute, sublicense, and/or sell copies of the  
Software, and to permit persons to whom the Software is furnished to do so,  
subject to the following conditions:  
The above copyright notice and this permission notice shall be included in  
all copies or substantial portions of the Software.  
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR  
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,  
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE  
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER  
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING  
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER  
DEALINGS IN THE SOFTWARE.