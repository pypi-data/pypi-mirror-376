from .api import OneFootballAPIClient

from typing import Dict, Any, Optional, List

from datetime import datetime, date

class OneFootball:
    """Main OneFootball API wrapper interface"""

    def __init__(self):
        self._api = OneFootballAPIClient()
    
    async def __aenter__(self):
        """Enter async context manager"""
        await self._api._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager"""
        await self._api.close()

    async def close(self):
        """Close context manager"""
        await self._api.close()

    async def search(self, query: str) -> Dict[str, Any]:
        """Search for players, teams, etc."""
        return await self._api._request("search", f"/v2/en/search?q={query}")
    
    async def search_players(self, query: str) -> Dict[str, Any]:
        """Search for players"""
        request = await self._api._request("search", f"/v2/en/search?q={query}")

        if request:
            return request.get("players", [])
        
        return []
    
    async def search_teams(self, query: str) -> Dict[str, Any]:
        """Search for teams"""
        request = await self._api._request("search", f"/v2/en/search?q={query}")

        if request:
            return request.get("teams", [])
        
        return []
    
    async def search_competitions(self, query: str) -> Dict[str, Any]:
        """Search for competitions"""
        request = await self._api._request("search", f"/v2/en/search?q={query}")

        if request:
            return request.get("competitions", [])
        
        return []
    
    async def search_news(self, query: str) -> Dict[str, Any]:
        """Search for news"""
        request = await self._api._request("search", f"/v2/en/search?q={query}")

        if request:
            return request.get("news", [])
        
        return []

    async def get_team(self, team_id: int) -> Dict[str, Any]:
        """Get team information"""
        return await self._api._request("vintage", f"/api/teams/en/{team_id}.json")

    async def get_team_transfers(self, team_id: int) -> Dict[str, Any]:
        """Get team transfers"""
        return await self._api._request("umka", f"/v3/en/teams/{team_id}/types/transfer")

    async def get_team_relevant_items(self, team_id: int) -> Dict[str, Any]:
        """Get team relevant items"""
        return await self._api._request("news", f"/news/v2/en/relevance/teams/{team_id}/items?personalised=not_set&mediation=iPhone-premiumgeos-team_news")

    async def get_team_news(self, team_id: int) -> Dict[str, Any]:
        """Get team news"""
        return await self._api._request("v6news", f"/v6/en/teams/{team_id}/items?only_verified=true")

    async def get_team_season_stats(self, team_id: int, season_id: int, current_group: int = 1, games_n: int = 5) -> Dict[str, Any]:
        """Get team season stats"""
        return await self._api._request("vintage", f"/api/season-stats/teams/en/{team_id}/{season_id}.json?current_group={current_group}&games_n={games_n}")

    async def get_team_fixtures(self, team_id: int, since_date: Optional[date] = None) -> Dict[str, Any]:
        """Get team fixtures"""
        if since_date is None:
            since_date = datetime.now().date()
        return await self._api._request("scores", f"/v2/en/search/matchdays?since={since_date}&teams={team_id}&utc_offset=+0100")

    async def get_team_next_match(self, team_id: int) -> Dict[str, Any]:
        """Get team's next match"""
        return await self._api._request("scores", f"/v1/en/teams/{team_id}/matches/next")

    async def get_team_previous_match(self, team_id: int, until_date: Optional[str] = None) -> Dict[str, Any]:
        """Get team's previous match"""
        endpoint = f"/v1/en/teams/{team_id}/matches/previous"
        if until_date:
            endpoint += f"?until={until_date}"
        return await self._api._request("scores", endpoint)

    async def get_player_transfers(self, player_id: int) -> Dict[str, Any]:
        """Get player transfers"""
        return await self._api._request("umka", f"/v3/en/players/{player_id}/types/transfer")

    async def get_player_stats(self, player_slug: str) -> Dict[str, Any]:
        """Get player stats by slug"""
        return await self._api._request("next_data", f"/en/player/{player_slug}/stats.json")

    async def get_player_competition_stats(self, player_slug: str, season_id: int) -> Dict[str, Any]:
        """Get player competition stats"""
        return await self._api._request("next_data", f"/en/player/{player_slug}/stats.json?player-id={player_slug}&player-id=stats&seasonId={season_id}")

    async def get_player_news(self, player_slug: str) -> Dict[str, Any]:
        """Get player news by slug"""
        return await self._api._request("next_data", f"/en/player/{player_slug}/news.json?player-id={player_slug}&player-id=news")

    # Match endpoints
    async def get_match(self, match_id: int, country: str = "gb") -> Dict[str, Any]:
        """Get match information"""
        return await self._api._request("scores_mixer", f"/v2/en/{country}/matches/{match_id}/card")

    async def get_match_news(self, match_id: int, country: str = "gb") -> Dict[str, Any]:
        """Get match news"""
        return await self._api._request("scores_mixer", f"/v1/en/{country}/matches/{match_id}/news")

    async def get_match_tv_listings(self, match_id: int, country: str = "gb") -> Dict[str, Any]:
        """Get match TV listings"""
        return await self._api._request("tv_guide", f"/v1/en/{country}/matches/{match_id}/listings")

    async def get_match_widget(self, match_id: int) -> Dict[str, Any]:
        """Get live match widget"""
        return await self._api._request("live_ticker", f"/v1/en/matches/{match_id}/widget")

    async def get_match_predictions(self, match_id: int) -> Dict[str, Any]:
        """Get match prediction votes"""
        return await self._api._request("polls", f"/opinions/threeway/{match_id}")

    async def get_match_odds(self, match_id: int, bookmaker_id: int = 3) -> Dict[str, Any]:
        """Get match odds"""
        return await self._api._request("betting", f"/v2/en/matches/{match_id}/bookmakers/{bookmaker_id}/odds")

    async def get_today_matches(self) -> Dict[str, Any]:
        """Get today's matches"""
        return await self._api._request("next_data", "/en/matches.json")

    async def get_live_matches(self) -> Dict[str, Any]:
        """Get live matches"""
        return await self._api._request("next_data", "/en/matches.json?only_live=true")

    async def get_tomorrow_matches(self) -> Dict[str, Any]:
        """Get tomorrow's matches"""
        return await self._api._request("next_data", "/en/matches/tomorrow.json")

    async def get_matches_by_date(self, match_date: date) -> Dict[str, Any]:
        """Get matches by specific date"""
        return await self._api._request("next_data", f"/en/matches.json?date={match_date}")

    async def get_competition_top_players(self, competition_id: int) -> Dict[str, Any]:
        """Get top players in a competition"""
        return await self._api._request("news", f"/news/v1/en/competition/{competition_id}/players/top")

    async def get_competition_stats(self, competition_id: int, season_id: int) -> Dict[str, Any]:
        """Get competition statistics"""
        return await self._api._request("feedmonster", f"/feeds/il/en/competitions/{competition_id}/{season_id}/league_statistics.json")

    async def get_competition(self, competition_id: int) -> Dict[str, Any]:
        """Get competition information"""
        return await self._api._request("scores", f"/v1/en/competitions/{competition_id}")

    async def get_competition_matches(self, competition_id: int, number_next: int = 1, number_previous: int = 1) -> Dict[str, Any]:
        """Get competition matches"""
        return await self._api._request("scores", f"/v1/en/competitions/{competition_id}/matches?number_next={number_next}&number_previous={number_previous}")

    async def get_competition_standings(self, competition_id: int, season_id: int) -> Dict[str, Any]:
        """Get competition standings"""
        return await self._api._request("feedmonster", f"/feeds/il/en/competitions/{competition_id}/{season_id}/standings.json")

    async def get_competition_video_news(self, competition_id: int) -> Dict[str, Any]:
        """Get competition video news"""
        return await self._api._request("v6news", f"/v6/en/competitions/{competition_id}/items?content_type=jwplayer_video&video_orientation=horizontal")

    async def get_competition_news(self, competition_id: int) -> Dict[str, Any]:
        """Get competition news"""
        return await self._api._request("v6news", f"/v6/en/competitions/{competition_id}/items")

    async def get_competition_transfers(self, competition_id: int) -> Dict[str, Any]:
        """Get competition transfers"""
        return await self._api._request("umka", f"/v3/en/competitions/{competition_id}/types/transfer")

    async def get_competition_matchdays(self, competition_id: int, season_id: int) -> Dict[str, Any]:
        """Get competition matchdays"""
        return await self._api._request("feedmonster", f"/feeds/il/en/competitions/{competition_id}/{season_id}/matchdaysOverview.json")

    async def get_all_competitions(self) -> Dict[str, Any]:
        """Get all competitions"""
        return await self._api._request("next_data", "/en/all-competitions.json?directory-entity=all-competitions")