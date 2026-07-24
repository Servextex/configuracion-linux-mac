#!/usr/bin/env bash
#
# reconfigurar-disco.sh
# Reconfigura el disco externo P3-512 (ext4) como disco de trabajo + descargas:
#   - montaje permanente en /mnt/disco1 (fstab)
#   - disco a nombre del usuario (ext4 tiene dueños reales)
#   - carpeta /mnt/disco1/Descargas
#   - Google Chrome y Firefox descargando ahi
#
# Uso:  sudo bash reconfigurar-disco.sh
# Documentado: 2026-07-21  (equipo Mac Mini + CachyOS, usuario ermesbatista)

set -euo pipefail

# ---- Ajusta estos 3 valores si cambian ----
ETIQUETA_DISCO="P3-512"
PUNTO_MONTAJE="/mnt/disco1"
USUARIO="ermesbatista"
# -------------------------------------------

if [[ $EUID -ne 0 ]]; then
  echo "Este script necesita sudo:  sudo bash $0" >&2
  exit 1
fi

CARPETA_DESCARGAS="$PUNTO_MONTAJE/Descargas"

echo "==> 1/6  Buscando el disco por etiqueta '$ETIQUETA_DISCO'..."
DEV=$(blkid -L "$ETIQUETA_DISCO" || true)
if [[ -z "$DEV" ]]; then
  echo "ERROR: no encuentro ningun disco con etiqueta '$ETIQUETA_DISCO'." >&2
  echo "Conectalo y vuelve a correr. (Ver discos: lsblk -f)" >&2
  exit 1
fi
UUID=$(blkid -s UUID -o value "$DEV")
echo "    Encontrado: $DEV   UUID=$UUID"

echo "==> 2/6  Punto de montaje $PUNTO_MONTAJE"
mkdir -p "$PUNTO_MONTAJE"

echo "==> 3/6  Actualizando /etc/fstab (ext4)"
# quita cualquier linea previa de este punto de montaje y agrega la nueva
sed -i "\| $PUNTO_MONTAJE |d" /etc/fstab
echo "UUID=$UUID $PUNTO_MONTAJE ext4 defaults,nofail,x-gvfs-show,x-gvfs-name=Disco%20P3-512 0 2" >> /etc/fstab
systemctl daemon-reload
mountpoint -q "$PUNTO_MONTAJE" || mount "$PUNTO_MONTAJE"
# ext4 tiene dueños reales: el disco a nombre del usuario
chown "$USUARIO:$USUARIO" "$PUNTO_MONTAJE"
echo "    Montado y a nombre de $USUARIO."

echo "==> 4/6  Carpeta de descargas"
mkdir -p "$CARPETA_DESCARGAS"
chown "$USUARIO:$USUARIO" "$CARPETA_DESCARGAS"

echo "==> 5/6  Google Chrome (politica de descargas)"
mkdir -p /etc/opt/chrome/policies/managed
cat > /etc/opt/chrome/policies/managed/descargas.json <<JSON
{
  "DownloadDirectory": "$CARPETA_DESCARGAS",
  "PromptForDownloadLocation": false
}
JSON

echo "==> 6/6  Firefox (autoconfig)"
FFDIR=""
for d in /usr/lib/firefox /usr/lib64/firefox /opt/firefox; do
  [[ -d "$d/defaults/pref" ]] && FFDIR="$d" && break
done
if [[ -n "$FFDIR" ]]; then
  cat > "$FFDIR/defaults/pref/autoconfig.js" <<'JS'
pref("general.config.filename", "firefox.cfg");
pref("general.config.obscure_value", 0);
JS
  cat > "$FFDIR/firefox.cfg" <<CFG
// Config Servex: descargas al disco externo
defaultPref("browser.download.folderList", 2);
defaultPref("browser.download.dir", "$CARPETA_DESCARGAS");
defaultPref("browser.download.useDownloadDir", true);
CFG
  echo "    Firefox configurado en $FFDIR"
else
  echo "    (Firefox no encontrado; se omite)"
fi

echo ""
echo "LISTO. Reinicia Chrome y Firefox para que tomen la carpeta de descargas."
echo "Disco montado en: $PUNTO_MONTAJE   Descargas: $CARPETA_DESCARGAS"
