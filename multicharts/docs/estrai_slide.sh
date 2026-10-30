#!/bin/bash
# Estrae le slide proiettate nei video del protocollo.
#
# Usa il rilevamento di cambio scena di ffmpeg: ogni volta che l'immagine cambia
# abbastanza (soglia SOGLIA), salva un fotogramma. I file sono nominati col
# TIMESTAMP del video, cosi da un'immagine si risale al punto del filmato.
#
# Uso:  bash mc/docs/estrai_slide.sh [cartella_video] [cartella_output] [soglia]

SRC="${1:-education/protocollo}"
OUT="${2:-education/protocollo/_slide}"
SOGLIA="${3:-0.20}"

mkdir -p "$OUT"
echo "sorgente: $SRC   output: $OUT   soglia: $SOGLIA"
echo

find "$SRC" -type f -name "*.mp4" -print0 | sort -z | while IFS= read -r -d '' f; do
    nome=$(basename "$f" .mp4)
    cart=$(dirname "$f" | sed "s|^$SRC/*||" | tr '/' '_' | sed 's/\.$//')
    dest="$OUT/${cart:+${cart}__}${nome}"
    if [ -d "$dest" ] && [ -n "$(ls -A "$dest" 2>/dev/null)" ]; then
        echo "salto (gia' fatto): $nome"
        continue
    fi
    mkdir -p "$dest"
    printf '%-62s ' "${nome:0:62}"

    # un solo passaggio: estrae i fotogrammi e stampa i loro tempi
    ffmpeg -nostdin -loglevel info -i "$f" \
        -vf "select='gt(scene,$SOGLIA)',showinfo,scale=1280:-2" \
        -fps_mode passthrough -q:v 4 -an "$dest/tmp_%04d.jpg" 2>"$dest/.info"

    # rinomina ogni fotogramma col suo minuto:secondo
    grep -o 'pts_time:[0-9.]*' "$dest/.info" | cut -d: -f2 > "$dest/.tempi"
    i=1
    while IFS= read -r t; do
        src=$(printf "%s/tmp_%04d.jpg" "$dest" "$i")
        [ -f "$src" ] || { i=$((i+1)); continue; }
        hh=$(printf "%02d" $(echo "$t/3600" | bc))
        mm=$(printf "%02d" $(echo "($t%3600)/60" | bc))
        ss=$(printf "%02d" $(echo "$t%60/1" | bc))
        mv "$src" "$dest/${hh}-${mm}-${ss}.jpg" 2>/dev/null
        i=$((i+1))
    done < "$dest/.tempi"
    rm -f "$dest"/tmp_*.jpg "$dest/.info" "$dest/.tempi"

    n=$(ls -1 "$dest"/*.jpg 2>/dev/null | wc -l | tr -d ' ')
    echo "$n slide"
done

echo
echo "TOTALE: $(find "$OUT" -name '*.jpg' | wc -l | tr -d ' ') slide in $(du -sh "$OUT" | cut -f1)"
