# Roleplay AI App

This app is the heart of the roleplay AI project. It handles authentication, distribution of trequests to databases and llms - pretty much everything but the actual LLM call happens in here.

## Organisation

### app.py

This is pure setup code for the fastapi backend.

### chat_active.py

These are helper functions to handle the chat active check, that prevents users from sending another request in a chat they already sent one to while it is being processed.

### chat_auth_wrapper.py

The chat auth wrapper handles basic authentication and wraps the business logic so exceptions to create issues or leak information.

### chat_endpoint_handlers.py

These are the actual chat related endpoints with very few exceptions. This file is pure business logic.

### databases.py

This file handles the initialisation of all used databases, from redis for caching to qdrant for the world and story vector search.

### functions.py

A catch-all file, that will be removed as quickly as possible. Right now it contains unrelated helper functions.

### llm_wrapper.py

This file handles any direct communication with the LLM(s), including prewarming and actually sending messages and retrieving their results.

### main.py

This file is intended as purely endpoint definitions for fastapi. Right now a few business logic functions remain as well.

### models.py

This file contains the request-models used to handle requests to the fastapi, so the json communication is directly decoded.
