docker build -t catbot .
docker rm -f chatbot-server
docker run -d -v /etc/catbot/misc:/app/misc --name chatbot-server catbot