# ghost-me.ai
#### To Run
    cd ghostme
    
    docker-compose up -d
or 
    docker-compose up -d --scale app=3
to recreate the image below

Demo is also located on: https://ghost-me-api.onrender.com

![alt text](ghost-me.ai.png)

Class is located in wrapper.py 
uses requests to simplify interactions with the API through python

```python
from wrapper import GhostWrapper
# GhostWrapper expects an email and password
# you can set local = True for the docker setup or leave it (default = False)
# to interact with https://ghost-me-api.onrender.com
ghost_service = GhostWrapper(email="random@email", password="random-password")

# simple registration
ghost_service.register()

# logs in and accesses the jwt token
jwt_token = ghost_service.get_access_token()

# sends data to the service
ghost_service.upload_data(
    jwt_token=jwt_token, file_path="path/to/file", job_description="random description"
)
# returns all data that was uploaded for that user
ghost_service.retrieve_uploaded_data(jwt_token=jwt_token)

# deletes the user and all of their uploaded data
ghost_service.delete(jwt_token=jwt_token)
```