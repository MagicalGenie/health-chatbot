# Health Chatbot POC for Aetna

```bash
# Training and setting up bot server on port 5005
make train-nlu
make train-core
make webchat

# In another terminal
make webserver # This will open up index.html to port 8000

# In another terminal
ngrok http 5005 # Copy the url displayed into hostname in index.html. This is the bot server

# In another terminal
ngrok http 8000 # Copy the url displayed. This will be the site page

```