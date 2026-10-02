"""Public response contracts shared by the frontend and OpenAPI documentation."""
from datetime import date, datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar('T')


class Page(BaseModel, Generic[T]):
    total: int
    limit: int
    offset: int
    results: list[T]


class GameCard(BaseModel):
    app_id: int
    name: str
    header_image_url: str | None
    release_date: date | None
    price: float | None
    genres: list[str]
    positive_reviews: int | None
    negative_reviews: int | None
    metacritic_score: int | None
    recommendation_count: int | None
    peak_ccu: int | None
    # null means no profile selected; false means checked and absent.
    is_owned: bool | None
    is_wishlisted: bool | None
    is_favorite: bool | None


class CollectionCard(GameCard):
    added_at: datetime


class LanguageSupport(BaseModel):
    language: str
    support_type: str


class GameDetail(GameCard):
    estimated_owners: str | None
    required_age: int | None
    discount_dlc_count: int | None
    description: str | None
    website_url: str | None
    support_url: str | None
    support_email: str | None
    metacritic_url: str | None
    user_score: float | None
    score_rank: int | None
    achievement_count: int | None
    notes: str | None
    avg_playtime_forever: int | None
    avg_playtime_2weeks: int | None
    median_playtime_forever: int | None
    median_playtime_2weeks: int | None
    developers: list[str]
    publishers: list[str]
    tags: list[str]
    categories: list[str]
    platforms: list[str]
    screenshots: list[str]
    languages: list[LanguageSupport]


class ProfileChoice(BaseModel):
    user_id: int
    username: str


class Profiles(Page[ProfileChoice]):
    data_source: Literal['simulated']


class Profile(ProfileChoice):
    created_at: datetime


class ProfileSummary(Profile):
    library_count: int
    wishlist_count: int
    favorite_count: int
    data_source: Literal['simulated']


class FavoriteState(BaseModel):
    user_id: int
    app_id: int
    is_favorite: bool


class MatchReason(BaseModel):
    type: Literal['tag', 'genre', 'developer']
    attribute: str
    source_app_id: int
    source_game: str
    source_weight: int


class RecommendedCard(GameCard):
    match_score: int
    reasons: list[MatchReason]


class Scoring(BaseModel):
    tag: int
    genre: int
    developer: int
    favorite_multiplier: int
    popularity: str


class Recommendations(BaseModel):
    strategy: Literal['popular_fallback', 'attribute_overlap']
    scoring: Scoring
    results: list[RecommendedCard]


class FilterOption(BaseModel):
    id: int
    name: str


class Achievement(BaseModel):
    app_id: int
    game_name: str
    achievement_name: str
    unlocked_at: datetime | None


class Activity(BaseModel):
    app_id: int
    game_name: str
    activity_type: Literal['PLAY', 'SESSION', 'LAUNCH']
    activity_time: datetime
    duration_minutes: int | None


class RankedCard(GameCard):
    metric_value: int


class ActivityRange(BaseModel):
    first_event: datetime | None
    last_event: datetime | None


class Rankings(BaseModel):
    source: Literal['steam', 'community']
    simulated: bool
    live: bool
    metric: str
    definition: str
    start_date: date | None
    end_date: date | None
    date_semantics: str
    activity_range: ActivityRange | None
    results: list[RankedCard]


class Results(BaseModel, Generic[T]):
    results: list[T]


class TopGames(Results[RankedCard]):
    metric: str


class GenreStats(BaseModel):
    genre: str
    game_count: int
    avg_price: float | None
    avg_metacritic_score: float | None
    avg_positive_reviews: float | None


class PlatformStats(BaseModel):
    platform: str
    game_count: int
    avg_price: float | None


class YearlyRelease(BaseModel):
    year: int
    games_released: int


class Health(BaseModel):
    status: Literal['ok']
    service: str
    demo_mode: bool


class Ready(BaseModel):
    status: Literal['ready']
    database: Literal['connected']
