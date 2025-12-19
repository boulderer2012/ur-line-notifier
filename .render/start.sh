#!/usr/bin/env bash
gunicorn --bind 0.0.0.0:10000 webhook_server:app
