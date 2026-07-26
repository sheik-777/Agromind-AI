@echo off
cd /d E:\AgroMind_Project_Structure
E:\AgroMind_Project_Structure\.venv\Scripts\python.exe -m uvicorn backend.app:app --host 127.0.0.1 --port 8002
