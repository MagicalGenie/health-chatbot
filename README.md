# Health Chatbot POC for Aetna

## Prereq

python = 3.7

## Setup

```bash
# Training and setting up bot server on port 5005
make train-nlu
make train-core
make webchat

# In another terminal
make action-server

# In another terminal
make webserver # This will open up index.html to port 8000


If you want to make it accessible on the internet you can use ngrok to port forward. Just make sure to update the index.html host value to the ngrok address.
# In another terminal
ngrok http 5005 # Copy the url displayed into hostname in index.html. This is the bot server

# In another terminal
ngrok http 8000 # Copy the url displayed. This will be the site page

```