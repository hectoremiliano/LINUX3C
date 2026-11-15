#!/bin/bash

# ==========================================================
# PROYECTO FINAL - ADMINISTRACION DE SERVIDORES LINUX
# Autor: Hector Emiliano Custodio Martinez
# Dominio: clase.local
# Servicios: BIND9, APACHE2 y SSH
# Sistema: Ubuntu Linux
# ==========================================================

set -Eeuo pipefail

DOMINIO="clase.local"
WWW="www.clase.local"
WEBROOT="/var/www/$DOMINIO"
ZONEDIR="/etc/bind/zonas"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FECHA="$(date +%Y%m%d)"
RESPALDO="/root/respaldo_proyecto_${FECHA}"

echo "=============================================="
echo "  PROYECTO FINAL - CONFIGURACION DE SERVIDORES"
echo "=============================================="

if [[ $EUID -ne 0 ]]; then
    echo "Ejecuta el script con sudo:"
    echo "sudo bash proyecto_final.sh"
    exit 1
fi

# ----------------------------------------------------------
# 1. DETECTAR DIRECCION IP
# ----------------------------------------------------------

IP="$(ip -4 route get 1.1.1.1 2>/dev/null |
      awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"

if [[ -z "$IP" ]]; then
    IP="$(hostname -I | awk '{print $1}')"
fi

if [[ -z "$IP" ]]; then
    echo "ERROR: No se pudo detectar la IP del servidor."
    exit 1
fi

IFS='.' read -r A B C D <<< "$IP"

ZONA_INVERSA="${C}.${B}.${A}.in-addr.arpa"
ARCHIVO_ZONA="$ZONEDIR/db.$DOMINIO"
ARCHIVO_INVERSO="$ZONEDIR/db.$ZONA_INVERSA"

echo "[INFO] Dominio: $DOMINIO"
echo "[INFO] Direccion IP: $IP"

# ----------------------------------------------------------
# 2. CREAR RESPALDOS
# ----------------------------------------------------------

mkdir -p "$RESPALDO"

for archivo in \
    /etc/bind/named.conf.options \
    /etc/bind/named.conf.local \
    /etc/apache2/sites-available/clase.local.conf
do
    if [[ -f "$archivo" ]]; then
        cp -a "$archivo" "$RESPALDO/"
    fi
done

echo "[OK] Respaldos guardados en $RESPALDO"

# ----------------------------------------------------------
# 3. INSTALAR SERVICIOS
# ----------------------------------------------------------

echo "[INFO] Instalando BIND9, Apache2 y SSH..."

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y bind9 bind9-utils dnsutils apache2 openssh-server curl

# ----------------------------------------------------------
# 4. CONFIGURAR SERVIDOR DNS
# ----------------------------------------------------------

mkdir -p "$ZONEDIR"

cat > /etc/bind/named.conf.options <<'EOF'
options {
    directory "/var/cache/bind";

    listen-on { any; };
    listen-on-v6 { any; };

    allow-query { any; };
    recursion yes;

    dnssec-validation auto;
};
EOF

# Eliminar únicamente las entradas administradas por este script.
sed -i '/\/\/ INICIO PROYECTO clase.local/,/\/\/ FIN PROYECTO clase.local/d' \
    /etc/bind/named.conf.local

cat >> /etc/bind/named.conf.local <<EOF

// INICIO PROYECTO clase.local
zone "$DOMINIO" {
    type master;
    file "$ARCHIVO_ZONA";
};

zone "$ZONA_INVERSA" {
    type master;
    file "$ARCHIVO_INVERSO";
};
// FIN PROYECTO clase.local
EOF

cat > "$ARCHIVO_ZONA" <<EOF
\$TTL 86400
@   IN  SOA ns1.$DOMINIO. admin.$DOMINIO. (
        ${FECHA}01
        3600
        1800
        604800
        86400
)
@       IN  NS  ns1.$DOMINIO.
ns1     IN  A   $IP
@       IN  A   $IP
www     IN  A   $IP
EOF

cat > "$ARCHIVO_INVERSO" <<EOF
\$TTL 86400
@   IN  SOA ns1.$DOMINIO. admin.$DOMINIO. (
        ${FECHA}01
        3600
        1800
        604800
        86400
)
@   IN  NS  ns1.$DOMINIO.
$D   IN  PTR $DOMINIO.
EOF

echo "[INFO] Validando configuracion DNS..."

named-checkconf
named-checkzone "$DOMINIO" "$ARCHIVO_ZONA"
named-checkzone "$ZONA_INVERSA" "$ARCHIVO_INVERSO"

systemctl enable bind9
systemctl restart bind9

echo "[OK] Servidor DNS configurado."

# ----------------------------------------------------------
# 5. CONFIGURAR APACHE2
# ----------------------------------------------------------

mkdir -p "$WEBROOT"

# Copiar las evidencias reales del repositorio.
for unidad in UNIDAD1 UNIDAD2 UNIDAD3 UNIDAD4; do
    if [[ -d "$SCRIPT_DIR/$unidad" ]]; then
        mkdir -p "$WEBROOT/evidencias"
        cp -a "$SCRIPT_DIR/$unidad" "$WEBROOT/evidencias/"
    fi
done

# Conservar la página existente; usar una página básica
# solamente si todavía no existe index.html.
if [[ ! -f "$WEBROOT/index.html" ]]; then
    if [[ -f "$SCRIPT_DIR/index.html" ]]; then
        cp "$SCRIPT_DIR/index.html" "$WEBROOT/index.html"
    else
        cat > "$WEBROOT/index.html" <<EOF
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Linux Lab</title>
</head>
<body>
<h1>Portafolio Linux</h1>
<p>Servidor web funcionando correctamente.</p>
<p>Dominio: $DOMINIO</p>
<p>IP: $IP</p>
</body>
</html>
EOF
    fi
fi

cat > /etc/apache2/sites-available/clase.local.conf <<EOF
<VirtualHost *:80>
    ServerName $DOMINIO
    ServerAlias $WWW
    DocumentRoot $WEBROOT

    <Directory $WEBROOT>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorLog \${APACHE_LOG_DIR}/clase_error.log
    CustomLog \${APACHE_LOG_DIR}/clase_access.log combined
</VirtualHost>
EOF

chown -R www-data:www-data "$WEBROOT"
chmod -R a+rX "$WEBROOT"

a2ensite clase.local.conf
a2dissite 000-default.conf 2>/dev/null || true

apache2ctl configtest
systemctl enable apache2
systemctl restart apache2

echo "[OK] Servidor web configurado."

# ----------------------------------------------------------
# 6. CONFIGURAR SSH
# ----------------------------------------------------------

systemctl enable ssh
systemctl restart ssh

echo "[OK] Servicio SSH configurado."

# ----------------------------------------------------------
# 7. VERIFICACIONES
# ----------------------------------------------------------

echo
echo "=============================================="
echo "          VERIFICACION DE SERVICIOS"
echo "=============================================="

echo
echo "[DNS]"
dig @"$IP" "$DOMINIO" A +short
dig @"$IP" "$WWW" A +short
dig @"$IP" -x "$IP" +short

echo
echo "[APACHE]"
curl -s -o /dev/null -w "HTTP: %{http_code}\n" \
    -H "Host: $DOMINIO" http://127.0.0.1/

echo
echo "[SSH]"
systemctl is-active ssh

echo
echo "[SERVICIOS]"
systemctl is-active bind9
systemctl is-active apache2
systemctl is-active ssh

echo
echo "=============================================="
echo " CONFIGURACION FINALIZADA"
echo " Dominio: http://$DOMINIO"
echo " IP: $IP"
echo " Web: $WEBROOT"
echo " Respaldos: $RESPALDO"
echo "=============================================="
echo
echo "NOTA: Para acceder desde Windows, configura la"
echo "resolucion del dominio en el archivo hosts."
