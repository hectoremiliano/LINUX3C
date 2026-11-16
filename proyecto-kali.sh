#!/bin/bash
# ==========================================================
# PROYECTO FINAL - ADMINISTRACION DE SERVIDORES LINUX
# Autor: Hector Emiliano Custodio Martinez
# Dominio: proyecto.linux
# Servicios: BIND9, APACHE2 y SSH
# Sistema: Ubuntu/Kali Linux
# ==========================================================
set -Eeuo pipefail

DOMINIO="proyecto.linux"
WWW="www.proyecto.linux"
WEBROOT="/var/www/$DOMINIO"
SITIO_HOME="/home/kali/proyecto-linux/sitio"
ENTREGA="/home/kali/proyecto-linux/entrega-ssh"
ZONEDIR="/etc/bind/zonas"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FECHA="$(date +%Y%m%d)"
RESPALDO="/root/respaldo_proyecto_${FECHA}"

# ---------------- MODO --verificar ----------------
if [[ "${1:-}" == "--verificar" ]]; then
    IP="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"
    echo "== VERIFICACION =="
    echo "IP: $IP"
    echo -n "DNS proyecto.linux -> "; dig @"$IP" "$DOMINIO" A +short || echo "FALLA"
    echo -n "HTTP -> "; curl -s -o /dev/null -w "%{http_code}\n" -H "Host: $DOMINIO" http://127.0.0.1/ || echo "FALLA"
    echo -n "Puerto 22 -> "; (ss -ltn | grep -q ':22 ') && echo "OK" || echo "FALLA"
    echo -n "bind9 -> "; systemctl is-active bind9
    echo -n "apache2 -> "; systemctl is-active apache2
    echo -n "ssh -> "; systemctl is-active ssh
    exit 0
fi

echo "=============================================="
echo "  PROYECTO FINAL - CONFIGURACION DE SERVIDORES"
echo "=============================================="

if [[ $EUID -ne 0 ]]; then
    echo "Ejecuta el script con sudo:"
    echo "sudo bash proyecto-kali.sh"
    exit 1
fi

# ----------------------------------------------------------
# 1. DETECTAR IP
# ----------------------------------------------------------
IP="$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="src"){print $(i+1); exit}}')"
[[ -z "$IP" ]] && IP="$(hostname -I | awk '{print $1}')"
[[ -z "$IP" ]] && { echo "ERROR: No se pudo detectar la IP."; exit 1; }

IFS='.' read -r A B C D <<< "$IP"
ZONA_INVERSA="${C}.${B}.${A}.in-addr.arpa"
ARCHIVO_ZONA="$ZONEDIR/db.$DOMINIO"
ARCHIVO_INVERSO="$ZONEDIR/db.$ZONA_INVERSA"

echo "[INFO] Dominio: $DOMINIO"
echo "[INFO] IP: $IP"

# ----------------------------------------------------------
# 2. RESPALDOS
# ----------------------------------------------------------
mkdir -p "$RESPALDO"
for f in /etc/bind/named.conf.options /etc/bind/named.conf.local \
         /etc/apache2/sites-available/$DOMINIO.conf; do
    [[ -f "$f" ]] && cp -a "$f" "$RESPALDO/"
done
echo "[OK] Respaldos en $RESPALDO"

# ----------------------------------------------------------
# 3. INSTALAR SERVICIOS
# ----------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y bind9 bind9-utils dnsutils apache2 openssh-server curl

# ----------------------------------------------------------
# 4. DNS
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

sed -i '/\/\/ INICIO PROYECTO/,/\/\/ FIN PROYECTO/d' /etc/bind/named.conf.local

cat >> /etc/bind/named.conf.local <<EOF

// INICIO PROYECTO
zone "$DOMINIO" {
    type master;
    file "$ARCHIVO_ZONA";
};
zone "$ZONA_INVERSA" {
    type master;
    file "$ARCHIVO_INVERSO";
};
// FIN PROYECTO
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
$D  IN  PTR $DOMINIO.
EOF

named-checkconf
named-checkzone "$DOMINIO" "$ARCHIVO_ZONA"
named-checkzone "$ZONA_INVERSA" "$ARCHIVO_INVERSO"

systemctl enable bind9
systemctl restart bind9
echo "[OK] DNS configurado."

# ----------------------------------------------------------
# 5. APACHE
# ----------------------------------------------------------
mkdir -p "$WEBROOT"

for unidad in UNIDAD1 UNIDAD2 UNIDAD3 UNIDAD4; do
    if [[ -d "$SCRIPT_DIR/$unidad" ]]; then
        mkdir -p "$WEBROOT/evidencias"
        cp -a "$SCRIPT_DIR/$unidad" "$WEBROOT/evidencias/"
    fi
done

if [[ ! -f "$WEBROOT/index.html" ]]; then
    if [[ -f "$SCRIPT_DIR/index.html" ]]; then
        cp "$SCRIPT_DIR/index.html" "$WEBROOT/index.html"
    else
        cat > "$WEBROOT/index.html" <<EOF
<!DOCTYPE html>
<html lang="es"><head><meta charset="UTF-8"><title>Linux Lab</title></head>
<body><h1>Portafolio Linux</h1>
<p>Servidor web funcionando.</p>
<p>Dominio: $DOMINIO</p><p>IP: $IP</p></body></html>
EOF
    fi
fi

cat > /etc/apache2/sites-available/$DOMINIO.conf <<EOF
<VirtualHost *:80>
    ServerName $DOMINIO
    ServerAlias $WWW
    DocumentRoot $WEBROOT
    <Directory $WEBROOT>
        Options FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
    ErrorLog \${APACHE_LOG_DIR}/${DOMINIO}_error.log
    CustomLog \${APACHE_LOG_DIR}/${DOMINIO}_access.log combined
</VirtualHost>
EOF

chown -R www-data:www-data "$WEBROOT"
chmod -R a+rX "$WEBROOT"
a2ensite $DOMINIO.conf
a2dissite 000-default.conf 2>/dev/null || true
apache2ctl configtest
systemctl enable apache2
systemctl restart apache2
echo "[OK] Apache configurado."

# ----------------------------------------------------------
# 6. SSH
# ----------------------------------------------------------
systemctl enable ssh
systemctl restart ssh
echo "[OK] SSH configurado."

# ----------------------------------------------------------
# 7. CARPETA ~/proyecto-linux/sitio (lo que el profe verá por SSH)
# ----------------------------------------------------------
mkdir -p "$SITIO_HOME"
cp -a "$WEBROOT/." "$SITIO_HOME/" 2>/dev/null || true
chown -R kali:kali /home/kali/proyecto-linux 2>/dev/null || true

# ----------------------------------------------------------
# 8. LEEME-PROFESOR.txt + scripts conectar-ssh
# ----------------------------------------------------------
mkdir -p "$ENTREGA"
cat > "$ENTREGA/LEEME-PROFESOR.txt" <<EOF
=========================================================
  PROYECTO LINUX - GUIA PARA EL PROFESOR
  Dominio: $DOMINIO
  IP del servidor: $IP
  Usuario SSH: kali
=========================================================

1) En su laptop Windows (PowerShell como administrador):
   Get-NetAdapter
   Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses "$IP"
   Clear-DnsClientCache
   nslookup $DOMINIO          # debe devolver $IP

2) Abra en el navegador:
   http://$DOMINIO

3) SSH:
   ssh kali@$IP
   ls -la ~/proyecto-linux
   ls -la ~/proyecto-linux/sitio
   exit

4) Al terminar, devuelva su DNS:
   Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ResetServerAddresses

NOTA: Si su adaptador no se llama "Wi-Fi", use el nombre que
muestre Get-NetAdapter (por ejemplo Ethernet).
EOF

cat > "$ENTREGA/conectar-ssh.ps1" <<EOF
# Ejecutar en PowerShell como administrador
Set-DnsClientServerAddress -InterfaceAlias "Wi-Fi" -ServerAddresses "$IP"
Clear-DnsClientCache
nslookup $DOMINIO
ssh kali@$IP
EOF

cat > "$ENTREGA/conectar-ssh.sh" <<EOF
#!/bin/bash
# Desde una VM Ubuntu en Adaptador puente
ssh kali@$IP
EOF
chmod +x "$ENTREGA/conectar-ssh.sh"
chown -R kali:kali "$ENTREGA" 2>/dev/null || true

# ----------------------------------------------------------
# 9. VERIFICACIONES
# ----------------------------------------------------------
echo
echo "=============================================="
echo "          VERIFICACION DE SERVICIOS"
echo "=============================================="
echo "[DNS]"; dig @"$IP" "$DOMINIO" A +short; dig @"$IP" "$WWW" A +short; dig @"$IP" -x "$IP" +short
echo "[APACHE]"; curl -s -o /dev/null -w "HTTP: %{http_code}\n" -H "Host: $DOMINIO" http://127.0.0.1/
echo "[SSH]"; systemctl is-active ssh
echo "[SERVICIOS]"; systemctl is-active bind9; systemctl is-active apache2; systemctl is-active ssh

# ----------------------------------------------------------
# 10. CUADRO LISTO
# ----------------------------------------------------------
echo
echo "=============================================="
echo "                  LISTO"
echo "=============================================="
echo "  Dominio : http://$DOMINIO"
echo "  IP      : $IP"
echo "  SSH     : ssh kali@$IP"
echo "  Web     : $WEBROOT"
echo "  Sitio   : $SITIO_HOME"
echo "  LEEME   : $ENTREGA/LEEME-PROFESOR.txt"
echo "  Respaldos: $RESPALDO"
echo "=============================================="
echo "NO vuelvas a ejecutar el script mientras el"
echo "profesor revisa: la IP puede cambiar y su DNS"
echo "manual dejaría de servir."
echo "=============================================="
