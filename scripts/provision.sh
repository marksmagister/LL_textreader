#!/usr/bin/env bash
# Build the box from nothing. Run as root on a fresh Debian 13:
#
#     ssh root@<ip> 'bash -s' < scripts/provision.sh
#
# Safe to run again — every step checks before it acts, so a failed download is
# just a re-run. You will need two passes: the first stops to print a deploy key,
# because the repo is private and the box cannot clone it until that key is added
# on GitHub. Everything after that is scripts/deploy.sh.
set -euo pipefail

fqdn="${LL_TEXTREADER_FQDN:-v2202609408983511171.ultrasrv.de}"
repo="${LL_TEXTREADER_REPO:-git@github.com:marksmagister/LL_textreader.git}"
app=/opt/ll-textreader
state=/var/lib/ll-textreader
u=llt

# The maintainer's laptop key, so `ssh llt@box ./scripts/deploy.sh` works after
# this. The private half has never left that laptop; see docs/deploying.md.
admin_key='ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIBK12YUpwWHoOAp8sEczaZfG6qRyzRJcy2UauY5eNF60 ll-textreader deploy'

step() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
as_llt() { su - "$u" -c "$1"; }

[ "$(id -u)" = 0 ] || { echo "run this as root" >&2; exit 1; }

step "Packages"
# nodejs is only ever used to *build* the frontend; the app is served by uvicorn.
# Trixie's 20.19.2 is what Vite 8 asks for (^20.19.0), so no third-party Node repo.
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl ca-certificates gnupg sudo rsync sqlite3 openssl \
  nodejs npm debian-keyring debian-archive-keyring apt-transport-https

step "Caddy"
# Not in Debian's archive, so this is the upstream repo. Caddy terminates TLS and
# is the only thing on the box facing the internet.
if ! command -v caddy >/dev/null; then
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key \
    | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
  curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
    > /etc/apt/sources.list.d/caddy-stable.list
  apt-get update -qq
  apt-get install -y -qq caddy
fi
caddy version

step "User and directories"
id "$u" >/dev/null 2>&1 || adduser --disabled-password --gecos '' "$u"
install -d -o "$u" -g "$u" -m 755 "$state"
install -d -o "$u" -g "$u" -m 700 "/home/$u/.ssh"
touch "/home/$u/.ssh/authorized_keys"
grep -qF "$admin_key" "/home/$u/.ssh/authorized_keys" \
  || echo "$admin_key" >> "/home/$u/.ssh/authorized_keys"
chown -R "$u:$u" "/home/$u/.ssh"
chmod 600 "/home/$u/.ssh/authorized_keys"

# Root gets it too. Once password logins are turned off (docs/deploying.md) a
# root with no key is a root you can only reach through netcup's web console.
install -d -m 700 /root/.ssh
touch /root/.ssh/authorized_keys
grep -qF "$admin_key" /root/.ssh/authorized_keys \
  || echo "$admin_key" >> /root/.ssh/authorized_keys
chmod 600 /root/.ssh/authorized_keys

step "uv"
# uv also supplies Python 3.12: trixie ships 3.13, and spaCy lags it (pyproject
# pins >=3.12,<3.13). One less apt package, and the version is the repo's to say.
[ -x "/home/$u/.local/bin/uv" ] || as_llt 'curl -LsSf https://astral.sh/uv/install.sh | sh'
as_llt "/home/$u/.local/bin/uv python install 3.12"

step "Deploy key"
# The repo is private, so the box needs its own read-only key on GitHub.
key="/home/$u/.ssh/id_ed25519"
[ -f "$key" ] || as_llt "ssh-keygen -t ed25519 -N '' -C 'll-textreader box' -f ~/.ssh/id_ed25519"
export GIT_SSH_COMMAND='ssh -o StrictHostKeyChecking=accept-new'
if ! as_llt "GIT_SSH_COMMAND='$GIT_SSH_COMMAND' git ls-remote '$repo' -q" >/dev/null 2>&1; then
  cat <<MSG

This box cannot read the repository yet. Add this as a deploy key —
read-only is enough, it never pushes:

  https://github.com/marksmagister/LL_textreader/settings/keys/new

$(cat "$key.pub")

Then run this script again. Everything above is already done.
MSG
  exit 0
fi

step "Clone"
if [ -d "$app/.git" ]; then
  as_llt "cd $app && GIT_SSH_COMMAND='$GIT_SSH_COMMAND' git pull --ff-only"
else
  install -d -o "$u" -g "$u" "$app"
  as_llt "GIT_SSH_COMMAND='$GIT_SSH_COMMAND' git clone -q '$repo' $app"
fi

step "Configuration"
# Written once and never overwritten: regenerating the password on a re-run would
# lock the reader out of their own lexicon.
if [ ! -f "$app/.env" ]; then
  pw=$(openssl rand -hex 24)
  cat > "$app/.env" <<ENV
LL_TEXTREADER_DB_PATH=$state/ll_textreader.db
LL_TEXTREADER_DATA_DIR=$state
LL_TEXTREADER_USERNAME=read
LL_TEXTREADER_PASSWORD=$pw
ENV
  chown "$u:$u" "$app/.env"
  chmod 600 "$app/.env"
  new_password=$pw
fi

step "Python, model and dictionary"
as_llt "cd $app && ~/.local/bin/uv sync --extra nlp --extra translate --no-dev"
as_llt "cd $app && ~/.local/bin/uv run python -c 'import fr_core_news_md' 2>/dev/null" \
  || as_llt "cd $app && ./scripts/setup-models.sh fr"
# 573MB down the wire to leave 12MB of glosses behind, so only once.
glosses=$(sqlite3 "$state/ll_textreader.db" 'SELECT COUNT(*) FROM hint' 2>/dev/null || echo 0)
if [ "${glosses:-0}" -lt 1 ]; then
  as_llt "cd $app && ./scripts/setup-dictionary.sh fr"
fi

step "Frontend"
as_llt "cd $app && npm --prefix frontend ci --silent && npm --prefix frontend run build"

step "Services"
install -m 644 "$app/deploy/ll-textreader.service" /etc/systemd/system/
install -m 644 "$app/deploy/ll-textreader-backup.service" /etc/systemd/system/
install -m 644 "$app/deploy/ll-textreader-backup.timer" /etc/systemd/system/
# deploy.sh restarts the service as llt; this is the only thing it may do as root.
echo "$u ALL=(root) NOPASSWD: /usr/bin/systemctl restart ll-textreader" \
  > /etc/sudoers.d/ll-textreader
chmod 440 /etc/sudoers.d/ll-textreader
visudo -cf /etc/sudoers.d/ll-textreader >/dev/null
systemctl daemon-reload
systemctl enable --now ll-textreader
systemctl enable --now ll-textreader-backup.timer

step "Caddy site"
sed "s/read\.example\.com/$fqdn/" "$app/deploy/Caddyfile" > /etc/caddy/Caddyfile
install -d -o caddy -g caddy /var/log/caddy
systemctl enable caddy
systemctl reload caddy || systemctl restart caddy

step "Check"
sleep 3
set -a; . "$app/.env"; set +a
curl -fsS -u "${LL_TEXTREADER_USERNAME:-read}:${LL_TEXTREADER_PASSWORD:-}" \
  -o /dev/null localhost:8000/api/health \
  && echo "  backend up" \
  || { echo "  backend down — journalctl -u ll-textreader -n 50" >&2; exit 1; }

cat <<DONE

Done. https://$fqdn  (user: ${LL_TEXTREADER_USERNAME:-read})
DONE
if [ -n "${new_password:-}" ]; then
  cat <<DONE
The password was generated just now and is printed once:

  $new_password

It lives in $app/.env. Change it there and restart if you would rather pick one.
DONE
fi
