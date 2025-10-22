SHELL := pwsh

.PHONY: help up down build backend frontend

help:
@echo "Available targets: up, down, build, backend, frontend"

up:
docker compose up -d
docker compose logs -f

down:
docker compose down -v

build:
docker compose build --no-cache

backend:
cd backend; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
cd frontend; npm run dev -- --host