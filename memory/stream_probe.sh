#!/bin/bash
curl -s -N -m 400 -X POST "https://scalable-ai-forge.preview.emergentagent.com/api/blueprints/stream" -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJmZTViZGI4YS05YTdmLTQ3MzYtOThjZC1iMzc5NGJhZTcwZWQiLCJlbWFpbCI6ImRlbW9AYXJjaGl0ZWN0LmlvIiwiZXhwIjoxNzkwMTM2MTA2LCJ0eXBlIjoiYWNjZXNzIn0.U1lylzsp33t-y9Pj4ya8G5RKmpFQQfk-aSJt1xeKT88" -H "Content-Type: application/json" -d '{"idea":"A tiny CLI that converts CSV exports into clean SQLite databases with inferred schemas."}' > /app/memory/stream3.txt 2>&1
echo "EXIT $?" >> /app/memory/stream3.txt
