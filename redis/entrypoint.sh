#!/bin/sh
set -e # Выходить немедленно, если команда завершается с ненулевым статусом

# Пути к файлам
CONF_DIR="/usr/local/etc/redis"
TEMPLATE_DIR="/mnt/redis_templates" # Директория, куда монтируются шаблоны

REDIS_CONF_TEMPLATE="${TEMPLATE_DIR}/redis.conf.template"
REDIS_CONF_TARGET="${CONF_DIR}/redis.conf"

USERS_ACL_TEMPLATE="${TEMPLATE_DIR}/users.acl.template"
USERS_ACL_TARGET="${CONF_DIR}/users.acl"

echo "INFO: Configuring Redis..."

# Создаем целевую директорию для конфигураций, если она не существует
mkdir -p "$CONF_DIR"

# Проверяем, что переменные окружения установлены
: "${REDIS_PASSWORD?REDIS_PASSWORD not set or empty}"
: "${REDIS_USER?REDIS_USER not set or empty}"
: "${REDIS_USER_PASSWORD?REDIS_USER_PASSWORD not set or empty}"

# Заменяем плейсхолдеры на значения переменных окружения с помощью sed
# Использование ~ в качестве разделителя в sed, чтобы избежать проблем, если пароли содержат /
sed "s~\${REDIS_PASSWORD}~$REDIS_PASSWORD~g" "$REDIS_CONF_TEMPLATE" > "$REDIS_CONF_TARGET"
sed -e "s~\${REDIS_USER}~$REDIS_USER~g" \
    -e "s~\${REDIS_USER_PASSWORD}~$REDIS_USER_PASSWORD~g" \
    "$USERS_ACL_TEMPLATE" > "$USERS_ACL_TARGET"

# Проверка, что файлы конфигурации созданы (базовая)
if [ ! -s "$REDIS_CONF_TARGET" ]; then
    echo "ERROR: Failed to create $REDIS_CONF_TARGET from template."
    exit 1
fi
if [ ! -s "$USERS_ACL_TARGET" ]; then
    echo "ERROR: Failed to create $USERS_ACL_TARGET from template."
    exit 1
fi

echo "INFO: Redis configuration generated successfully."
echo "INFO: Starting Redis server..."

# Выполняем команду, переданную Docker-контейнеру (т.е. redis-server ...)
exec "$@"
