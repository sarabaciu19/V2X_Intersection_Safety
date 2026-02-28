"""
main.py — Entry point
Rulare: python main.py
       sau: uvicorn api.server:app --reload --port 8000
"""
import uvicorn
if __name__ == "__main__":
    uvicorn.run("api.server:app", host="0.0.0.0", port=8000, reload=False)
