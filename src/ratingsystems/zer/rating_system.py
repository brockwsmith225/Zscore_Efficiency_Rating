import math
from typing import Optional

from ratingsystems import Rating, RatingSystem, Stat, TeamRating

from ratingsystems.zer.model import Efficiency


class ZscoreEfficiencyRatingSystem(RatingSystem):

    class Meta:
        name: str = "zer"
    
    def __init__(self):
        pass

    def rate(self, games: list, seed: Rating = None) -> Rating:
        if seed is not None:
            seed = Rating.minmax_normalize(seed)

        points = {}
        points_against = {}
        for game in games:
            if isinstance(game, tuple):
                winner = game[0]
                loser = game[1]
                winner_points = game[2]
                loser_points = game[3]
            else:
                # if not game.completed:
                #     continue
                # if game.home_division not in ["fbs"]:
                #     game.home_team = "exclude"
                #     continue
                # if game.away_division not in ["fbs"]:
                #     game.away_team = "exclude"
                #     continue
                if game.home_team not in points:
                    points[game.home_team] = []
                    points_against[game.home_team] = []
                if game.away_team not in points:
                    points[game.away_team] = []
                    points_against[game.away_team] = []
                points[game.home_team].append((game.home_points, game.away_team))
                points_against[game.home_team].append((game.away_points, game.away_team))
                points[game.away_team].append((game.away_points, game.home_team))
                points_against[game.away_team].append((game.home_points, game.home_team))

        global_points = [value[0] for team in points for value in points[team]]
        global_avg_points = self._safe_divide(sum(global_points), len(global_points))
        global_stdev_points = math.sqrt(self._safe_divide(sum([pow(v - global_avg_points, 2) for v in global_points]), len(global_points)))

        avg_points = {t: self._safe_divide(sum([p for p, _ in games]), len(games)) for t, games in points.items()}
        stdev_points = {t: math.sqrt(self._safe_divide(sum([pow(p - avg_points[t], 2) for p, _ in games]), len(games))) for t, games in points.items()}
        avg_points_against = {t: self._safe_divide(sum([p for p, _ in games]), len(games)) for t, games in points_against.items()}
        stdev_points_against = {t: math.sqrt(self._safe_divide(sum([pow(p - avg_points_against[t], 2) for p, _ in games]), len(games))) for t, games in points_against.items()}
        offensive_efficiencies = {t: [(self._calculate_offensive_efficiency(p, avg_points_against[opp], stdev_points_against[opp]), opp) for p, opp in games] for t, games in points.items()}
        defensive_efficiencies = {t: [(self._calculate_defensive_efficiency(p, avg_points[opp], stdev_points[opp]), opp) for p, opp in games] for t, games in points_against.items()}
        if seed is not None:
            offensive_efficiency = Rating({t: Efficiency(self._safe_divide(sum([e * seed.get_rating(opp, 0) for e, opp in games]), sum([seed.get_rating(opp, 0) for _, opp in games]))) for t, games in offensive_efficiencies.items()}, name="_efficiency", games=games, points_mode=PointsMode.FOR)
            defensive_efficiency = Rating({t: Efficiency(self._safe_divide(sum([e * seed.get_rating(opp, 0) for e, opp in games]), sum([seed.get_rating(opp, 0) for _, opp in games]))) for t, games in defensive_efficiencies.items()}, name="_efficiency", games=games, points_mode=PointsMode.AGAINST)
            # offensive_ratings = {t: self._safe_divide(sum([e * (seed.get_rating(opp, 0) if e > 0 else 1 - seed.get_rating(opp, 0)) for e, opp in games]), sum([(seed.get_rating(opp, 0) if e > 0 else 1 - seed.get_rating(opp, 0)) for e, opp in games])) for t, games in offensive_efficiencies.items()}
            # defensive_ratings = {t: self._safe_divide(sum([e * (seed.get_rating(opp, 0) if e > 0 else 1 - seed.get_rating(opp, 0)) for e, opp in games]), sum([(seed.get_rating(opp, 0) if e > 0 else 1 - seed.get_rating(opp, 0)) for e, opp in games])) for t, games in defensive_efficiencies.items()}
        else:
            offensive_efficiency = Rating({t: Efficiency(self._safe_divide(sum([e for e, _ in games]), len(games))) for t, games in offensive_efficiencies.items()}, name="_efficiency", games=games)
            defensive_efficiency = Rating({t: Efficiency(self._safe_divide(sum([e for e, _ in games]), len(games))) for t, games in defensive_efficiencies.items()}, name="_efficiency", games=games)

        offensive_rating = ((global_avg_points + offensive_efficiency * global_stdev_points) | Stat) % "offense"
        defensive_rating = ((global_avg_points - defensive_efficiency * global_stdev_points) | Stat) % "defense"

        return (offensive_rating - defensive_rating) % "zer"

    def _calculate_offensive_efficiency(self, points: float, opp_avg_points_against: float, opp_stdev_points_against: float) -> float:
        return (points - opp_avg_points_against) / opp_stdev_points_against

    def _calculate_defensive_efficiency(self, points: float, opp_avg_points: float, opp_stdev_points: float) -> float:
        return (opp_avg_points - points) / opp_stdev_points

    @classmethod
    def _safe_divide(cls, x: float, y: float, default: float = 0.0) -> float:
        if y == 0:
            return default
        return x / y