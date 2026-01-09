wget https://raw.githubusercontent.com/chase-roohms/dumpsterr/refs/heads/main/docker-compose/docker-compose.yml -O docker-compose.yml
wget https://raw.githubusercontent.com/chase-roohms/dumpsterr/refs/heads/main/docker-compose/.env.example -O .env
wget https://raw.githubusercontent.com/chase-roohms/dumpsterr/refs/heads/main/data/config.example.yml -O config.yml

echo "Downloaded docker-compose.yml, .env, and config.yml files."
echo "Please review and update the .env and config.yml files as needed before starting the services."
echo "To start the services, run: docker-compose up -d"