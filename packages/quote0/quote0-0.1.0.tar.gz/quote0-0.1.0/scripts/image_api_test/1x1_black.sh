#!/bin/bash
curl -X POST \
  https://dot.mindreset.tech/api/open/image \
  -H "Authorization: Bearer $DOT_API_KEY" \
  -H 'Content-Type: application/json' \
  --data-raw "{
    \"refreshNow\": true,
    \"deviceId\": \"$DOT_DEVICE_ID\",
    \"image\": \"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mNgYGAAAAAEAAHI6uv5AAAAAElFTkSuQmCC\",
    \"border\": 0
  }"
