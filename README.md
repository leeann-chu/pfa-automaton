# 🐀 Watchrat
### A Discord bot that bridges your Minecraft server and Discord server.

- Chat flows both ways — messages sent in Discord appear in Minecraft and vice versa
- Start and stop the Minecraft server remotely from Discord
- Server status checks, player list, weather commands, and more
- Built for a containerized Minecraft server running via Docker

---

## Commands

| Command | Description |
|---|---|
| `p!help` | Brings up the help menu |
| `p!say <message>` | Send a message to the Minecraft server |
| `p!list` | List currently online players |
| `p!wc` | Clear the weather |
| `p!start` | Start the Minecraft server |
| `p!stop` | Stop the Minecraft server |
| `p!check` | Check if the server is online |
| `p!ping` | Check bot latency |

---

## Architecture

Watchrat runs as a Docker container alongside the Minecraft server container. They share a Docker network so the bot can reach the server via RCON using the container name as a hostname. Server logs are read via a shared volume mount.

Start/stop commands work via a restricted SSH connection to the host machine — the bot can only run `docker start` and `docker stop` for the Minecraft container and nothing else.

```
Discord
   ↓
Watchrat container
   ├── RCON → mceternal2026 container (say, list, stop, check)
   ├── SSH  → host machine (start, stop)
   └── logs → /data/logs/latest.log (read via shared volume)
```

---

## Setup from scratch

### 1. Clone the repo

```bash
git clone https://github.com/leeann-chu/pfa-automaton.git
cd pfa-automaton
```

### 2. Generate an SSH keypair for the bot

```bash
ssh-keygen -t ed25519 -f bot_ssh_key -N "" -C "watchrat"
```

### 3. Add the public key to authorized_keys with restrictions

```bash
cat bot_ssh_key.pub
```

Copy the output and add this line to `~/.ssh/authorized_keys` on the host — **it must be one single line**:

```
command="case \"$SSH_ORIGINAL_COMMAND\" in 'docker start mceternal2026') docker start mceternal2026 ;; 'docker stop mceternal2026') docker stop mceternal2026 ;; *) echo 'Not allowed' ;; esac",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 YOUR_PUBLIC_KEY_HERE watchrat
```

### 4. Set correct permissions on the private key

```bash
chmod 600 bot_ssh_key
chmod +x lunch_server.sh
```

### 5. Test the SSH connection before starting the bot

```bash
# Find your SSH port
cat /etc/ssh/sshd_config | grep Port

# Test start (safe — does nothing if already running)
ssh -i bot_ssh_key -p YOUR_SSH_PORT -o StrictHostKeyChecking=no <YOURNAME>@localhost 'docker start mceternal2026'
```

### 6. Create the .env file

```bash
cp .env.template .env
nano .env
```

Fill in your values:

```
DISCORD_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_channel_id
MINECRAFT_IP=mceternal2026
RCON_PASS=your_rcon_password
RCON_PORT=25575
MC_LOG_PATH=/logs/latest.log
```

**Note:** `MINECRAFT_IP` should be the container name, not an IP address. Both containers share a Docker network so the name resolves automatically.

### 7. Create the root-level .env for Docker Compose

In the parent directory alongside `docker-compose.yml`:

```bash
echo "RCON_PASSWORD=your_rcon_password" > ../.env
```

This must match `RCON_PASS` in `bot/.env`.

### 8. Verify server.properties has RCON enabled

```bash
grep rcon /path/to/minecraft/data/server.properties
```

Should show:
```
enable-rcon=true
rcon.password=your_rcon_password
rcon.port=25575
```

### 9. Start everything

```bash
cd ..  # back to the directory with docker-compose.yml
docker compose up -d --build
docker compose logs -f
```

### 10. Verify in Discord

Head to your Discord server and run `p!check` — it should return the server status.

---

## Making code changes

Since the bot code is mounted as a volume, changes take effect immediately on restart with no rebuild needed:

```bash
docker restart watchrat
```

Only rebuild if you change `Dockerfile` or `requirements.txt`:

```bash
docker compose up -d --build watchrat
```

---

## File structure

```
pfa-automaton/
├── Dockerfile
├── requirements.txt
├── .env                  ← create from .env.template, never commit
├── .env.template         ← safe to commit, no real values
├── .gitignore
├── bot_ssh_key           ← never commit
├── bot_ssh_key.pub       ← never commit
├── lunch_server.sh       ← SSH wrapper for docker start/stop
├── main.py               ← bot commands
├── rcon.py               ← RCON client
└── cogs/
    └── watchlog.py       ← log watcher task
```


*Original RCON implementation based on [mconBot](https://github.com/RayNieport/mconBot) by Ray Nieport.*