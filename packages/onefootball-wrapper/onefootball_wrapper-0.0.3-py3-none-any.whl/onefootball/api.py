# api.py
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

class OneFootballAPIClient:
    def __init__(self):

        self.base_urls = {
            "search": "https://search-api.onefootball.com",
            "vintage": "https://vintagemonster.onefootball.com",
            "umka": "https://umka-api.onefootball.com",
            "news": "https://api.onefootball.com",
            "v6news": "https://news.onefootball.com",
            "scores": "https://scores-api.onefootball.com",
            "next_data": "https://onefootball.com/_next/data/8dc075c103ec",
            "scores_mixer": "https://api.onefootball.com/scores-mixer",
            "tv_guide": "https://tv-guide-api.onefootball.com",
            "live_ticker": "https://api.onefootball.com/live-ticker-api",
            "polls": "https://api.onefootball.com/polls-api",
            "betting": "https://api.onefootball.com/betting-api",
            "feedmonster": "https://feedmonster.onefootball.com"
        }
        
        self.headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "origin": "https://onefootball.com",
            "referer": "https://onefootball.com/",
            "sec-ch-ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        self.session = None

    async def _ensure_session(self):
        """Ensure we have an active session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(headers=self.headers)

    async def _request(self, base_url_key: str, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Base request method with dynamic base URL"""
        await self._ensure_session()
        
        if base_url_key not in self.base_urls:
            raise ValueError(f"Unknown base URL key: {base_url_key}")
        
        url = f"{self.base_urls[base_url_key]}{endpoint}"
        
        try:
            async with self.session.get(url, params=params) as response:
                response.raise_for_status()

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return await response.json()
                else:
                    try:
                        return await response.json()
                    except:
                        return {"text": await response.text()}
        except aiohttp.ClientError as e:
            raise Exception(f"API request to {url} failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error with request to {url}: {str(e)}")

    async def close(self):
        """Close the session"""
        if self.session and not self.session.closed:
            await self.session.close()