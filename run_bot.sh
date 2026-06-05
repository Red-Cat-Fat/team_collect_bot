#!/bin/bash

set -e

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$REPO_DIR/.env"
COMPOSE_FILE="$REPO_DIR/docker-compose.yml"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

prompt_input() {
    local prompt="$1"
    local var_name="$2"
    local default="$3"
    local is_secret="$4"
    local value=""

    while [[ -z "$value" ]]; do
        if [[ -n "$default" ]]; then
            read -rp "$prompt [$default]: " value
            value="${value:-$default}"
        else
            read -rp "$prompt: " value
        fi

        if [[ -z "$value" && -z "$default" ]]; then
            log_error "Это поле обязательно!"
        fi
    done

    eval "$var_name=\"$value\""
}

prompt_secret() {
    local prompt="$1"
    local var_name="$2"
    local value=""

    while [[ -z "$value" ]]; do
        read -rsp "$prompt: " value
        echo
        if [[ -z "$value" ]]; then
            log_error "Это поле обязательно!"
        fi
    done

    eval "$var_name=\"$value\""
}

load_existing_env() {
    if [[ -f "$ENV_FILE" ]]; then
        log_info "Найден существующий .env, загружаю значения..."
        set -a
        source "$ENV_FILE"
        set +a
    fi
}

create_env_file() {
    log_info "Создаю .env файл..."
    cat > "$ENV_FILE" <<EOF
BOT_TOKEN=$BOT_TOKEN
ADMIN_IDS=$ADMIN_IDS
TOPIC_ID=$TOPIC_ID
DB_PATH=./data/bot.db
TIMEZONE=$TIMEZONE
EOF
    chmod 600 "$ENV_FILE"
    log_info ".env создан: $ENV_FILE"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker не установлен. Установите Docker и попробуйте снова."
        exit 1
    fi

    if ! command -v docker compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose не найден. Установите Docker Compose v2."
        exit 1
    fi

    log_info "Docker и Docker Compose найдены"
}

build_and_run() {
    log_info "Сборка и запуск контейнера..."
    cd "$REPO_DIR"
    docker compose up -d --build --remove-orphans
    log_info "Контейнер запущен в фоновом режиме"
}

show_logs() {
    log_info "Логи бота (Ctrl+C для выхода, контейнер продолжит работу):"
    cd "$REPO_DIR"
    docker compose logs -f bot
}

main() {
    clear
    echo "========================================"
    echo "  Telegram Poll Bot - Настройка и запуск"
    echo "========================================"
    echo

    check_docker
    load_existing_env

    echo
    log_info "Настройка параметров бота:"
    echo

    prompt_secret "Введите BOT_TOKEN (от @BotFather)" BOT_TOKEN

    if [[ -z "$ADMIN_IDS" ]]; then
        prompt_input "Введите ADMIN_IDS (через запятую, например: 123456789,987654321)" ADMIN_IDS
    else
        prompt_input "Введите ADMIN_IDS (через запятую)" ADMIN_IDS "$ADMIN_IDS"
    fi

    if [[ -z "$TOPIC_ID" ]]; then
        prompt_input "Введите TOPIC_ID (ID топика/темы в группе)" TOPIC_ID
    else
        prompt_input "Введите TOPIC_ID" TOPIC_ID "$TOPIC_ID"
    fi

    if [[ -z "$TIMEZONE" ]]; then
        prompt_input "Введите TIMEZONE" TIMEZONE "Europe/Moscow"
    else
        prompt_input "Введите TIMEZONE" TIMEZONE "$TIMEZONE"
    fi

    echo
    create_env_file

    mkdir -p "$REPO_DIR/data"

    build_and_run

    echo
    log_info "Бот успешно запущен!"
    echo
    echo "Полезные команды:"
    echo "  docker compose logs -f bot    # Просмотр логов"
    echo "  docker compose restart bot    # Перезапуск"
    echo "  docker compose down           # Остановка"
    echo "  docker compose up -d          # Запуск в фоне"
    echo
    echo "Конфигурация сохранена в: $ENV_FILE"
    echo

    read -rp "Показать логи сейчас? (y/N): " show_logs_now
    if [[ "$show_logs_now" =~ ^[Yy]$ ]]; then
        show_logs
    fi
}

main "$@"