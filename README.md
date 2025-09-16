# StatDig: Anti-malware Engine & Copilot for the Agentic Era

## Watch the video: https://m.youtube.com/watch?v=supLuqfNA-Y

![](https://i.imgur.com/o9cpnrZ.jpeg)

[Setup Instructions](#setup)

LLMs like ChatGPT and Gemini are increasingly used by cyberattackers to generate malware (https://www.hp.com/us-en/newsroom/press-releases/2024/ai-generate-malware.html). This creates novel strains of **malware which evade detection by many anti-malware engines** which rely on **having seen a malware before to detect it**. This leaves businesses and even states vulnerable to advanced generative malware.

Furthermore, Advanced Persistent Threats (APTs) often create novel malware strains using new techniques themselves, targeting specific organisations and posing an existential threat.

Therefore, StatDig was born. **StatDig uses agentic AI and TiDB vector search to do what many anti-malware engines can't**: analyse novel, unknown suspected malware samples and deliver a verdict in minutes, not weeks. it indexes all its findings in **StatDig SuperSearch Copilot, powered by TiDB vector and full text search and auto-embeddings**. This gives cybersecurity professionals access to easy and efficient knowledge management, as StatDig automatically chooses whether to use semantic or exact search, with access to all previously analysed artefacts.

**StatDig - detects what others can't**

## Features

- Analysis agent automatically extracts functions and analyses uploaded binaries (Linux ELF, shared object, Windows DLL / EXE, .NET not supported for now)
- works even with stripped malwares
- delivers a Malicious / Benign verdict in minutes + initial report + guidance on next steps for malware mitigation and stores in TiDB
- tree of significant functions helps cybersecurity professionals validate StatDig's results
- Organiser agent uses report to do relevant web searches to obtain web information to enrich its analysis (e.g. correlating threat actor or tactics with online reports)
- function-level analysis and summaries of each individual functions (stored in TiDB), unprecedented granularity

![](https://i.imgur.com/XS9mB32.jpeg)

- intelligent search engine (SuperSearch Copilot) to take a user's search term and decide whether to use TiDB full text search for exact match (e.g. IP address, URL, file path, process name) or semantic search using TiDB vector search (e.g. malware tactic)
- search engine for knowledge management across thousands of binaries
- uses TiDB auto embedding and HNSW vector index for fast results
- **Chat2Query** would allow user to free-form query the database (planned)

## Data Flow and Integrations

- on upload, StatDig processes the file using Ghidra to get rough decompilations of each function (.NET not supported)
- the functions are passed to **Kimi K2 with chain of thought prompting** to deliver a comprehensive report and highlight functions of interest
- the report is stored in **TiDB with Amazon Titan Embed v2 auto-embedding and HNSW index for fast vector search**
- Organiser agent uses report and code of significant functions to do web searches for further threat intelligence
- Organiser agent enriches the initial report with new insights from **Kimi K2 web search** tool and updates the list of malware indicators and tags the report.
- Organiser agent stores summaries for individual significant functions in the malware in **TiDB with auto embeddings**
- **SuperSearch Copilot** - has access to all the malware sample overviews and function summaries in TiDB
- given user's search term, uses Kimi K2 Turbo to decide if it should use exact or semantic search for best results
- searches across all entities (individual functions and entire malware samples) and ranks by similarity / distance score
- TiDB vector and full text search allow for extremely fast querying and searching

## Setup

### Backend

Please set appropriate LLM API keys and secrets in the backend/.env file. We used Kimi K2 from the Moonshot AI API.

You also need to set the TiDB username, password, database, endpoint and download the relevant certificate from your TiDB control panel.

To set up StatDig, we recommend creating a Python virtual environment. Then, pip install:

```
pip install fastapi openai PyMySQL requests python-dotenv uvicorn argon2-cffi itsdangerous
```

You also need Docker and need to pull the Docker image for Ghidra:

```
docker pull blacktop/ghidra:10
```

Then, `cd backend` and run `sudo python3 statdig.py`. The StatDig backend should be up and running.

### Frontend

To run the StatDig frontend:

```
cd frontend/
npm i
npm run dev
```

## Limitations

Obfuscated files may pose issues. Do not upload text or non-application files, as StatDig is built for analysing malware like Linux ELFs, shared objects and Windows EXEs or DLLs. .NET and packed files may not be fully supported.

## Next steps

- TiDB Chat2Query to enable complex, unforeseen insights on an existing StatDig installation
- TiDB Data Service could enable a global-scale, large deployment of StatDig to collect malware samples
