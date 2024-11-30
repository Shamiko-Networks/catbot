docker build -t catbot .
docker rm -f chatbot-server
docker run -d -v /root/cat/chatbot/misc:/app/misc --name chatbot-server catbot