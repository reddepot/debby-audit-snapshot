#!/bin/bash
# Launcher + watchdog anti-OOM pour l'embed OR. 4 streams (nstreams=4 couvre TOUT via remote_has skip).
# Recycle les process si free<1200MB (RSS non rendu à l'OS → restart = reset, skip instantané via prefetch).
# S'arrête quand les streams finissent naturellement (partitions épuisées) avec vec>=869.
REMOTE=meddata:meddata-lake/debby_embed/vectors
RELAUNCH() {
  pkill -9 -f embed_or.py 2>/dev/null; sleep 4
  cd /root
  for s in 0 1 2 3; do
    nohup python3 /root/embed_or.py --nstreams 4 --stream-id "$s" --workers 28 > /root/or_$s.log 2>&1 &
  done
  echo "$(date -u +%H:%M:%S) RELAUNCH 4 streams" >> /root/watchdog.log
}
RELAUNCH
while true; do
  sleep 60
  n=$(pgrep -fc "[e]mbed_or.py")
  vec=$(rclone lsf "$REMOTE" 2>/dev/null | wc -l)
  free=$(free -m | awk '/Mem/{print $4}')
  echo "$(date -u +%H:%M:%S) n=$n vec=$vec/871 free=${free}MB" >> /root/watchdog.log
  if [ "$n" -eq 0 ]; then
    if [ "$vec" -ge 869 ]; then echo "$(date -u +%H:%M:%S) [EMBED_COMPLETE] vec=$vec" >> /root/watchdog.log; break
    else echo "$(date -u +%H:%M:%S) streams finis mais vec=$vec<869 → relance résiduels" >> /root/watchdog.log; RELAUNCH; fi
  elif [ "${free:-9999}" -lt 1200 ]; then
    echo "$(date -u +%H:%M:%S) RECYCLE (free=$free<1200)" >> /root/watchdog.log; RELAUNCH
  fi
done
