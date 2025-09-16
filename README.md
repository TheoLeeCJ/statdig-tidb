# StatDig: Anti-malware for the Agentic Era

## Watch the video: 

![](https://i.imgur.com/o9cpnrZ.jpeg)

ChatGPT and Gemini are increasingly used by cyber attackers to generate malware. This creates novel strains of malware which evade detection by many anti-malware engines which rely on having seen a malware before to detect it. This leaves businesses and even states vulnerable to advanced generative malware.

Therefore, StatDig was born. StatDig uses agentic AI and TiDB vector search to analyse novel, unknown suspected malware samples and deliver a verdict in minutes, and indexes all its findings in StatDig SuperSearch, allowing cybersecurity professionals to easy knowledge management.

## Setting Up

Please set appropriate LLM API keys and secrets in the backend/.env file. We used Kimi K2 from the Moonshot AI API.

You also need to set the TiDB username, password, database, endpoint and download the relevant certificate from your TiDB control panel.

To set up StatDig, we recommend creating a Python virtual environment. Then, pip install:

```
pip install fastapi openai PyMySQL requests
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

Obfuscated files may pose issues. Do not upload text or non-application files, as StatDig is built for analysing malware like Linux ELFs, shared objects and Windows EXEs or DLLs.

## Next steps

- TiDB Chat2Query to enable complex, unforeseen insights on an existing StatDig installation
- TiDB Data Service could enable a global-scale, large deployment of StatDig to collect malware samples
