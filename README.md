# ghost-me.ai

<p align="center">
  <img src="assets/ghostimg.jpg" alt="ghost logo">
</p>

## Goal
The main goal of this project is to combat ghosting i.e. 
not getting a reply after applying to a job opening. The idea is
to use a llm to generate an email providing course recommendations for the user to improve in the future.

### Tech Stack
* FastAPI (Main API)
* Flask (Sends emails to the user)
* RabbitMQ (Handles communication between api and llm service)
* Postgres (Stores user data and scraped courses from etl service)
* ChromaDB (Stores vectores from text)
* Langchain (Generates the email)
* Docker
* Kubernetes & Monitoring (possibly in the future)

### Architecture
![alt text](assets/ghost-me.ai.png)

### To run
Follow the link to the model: https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGML/tree/main and download it into the llmservice's model folder or modify the compose file (name in compose has to match the downloaded model name) as it uses mounting to load the model into memory.

Then

``` bash
cd backend
docker-compose up -d --scale app=3
```

Note: Known issue is that the llm makes 1 recommendation and throws an error (will look into further after a short break). 
Might need to restart a couple of containers as some boot faster than others (double check nginx and llmservice especially).





