"""
main.py — Entry point pentru V2X Intersection Safety
Rulează: python main.py
"""

import asyncio
from backend.models.simulator import main

if __name__ == "__main__":
    asyncio.run(main())
