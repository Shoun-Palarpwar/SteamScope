import React, { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import './styles.css';

const paths = {
  compass: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18Zm4 5-2.5 5.5L8 16l2.5-5.5L16 8Z',
  library: 'M4 4v16M8 4v16M12 4v16M16 5l4 14',
  heart: 'M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z',
  bookmark: 'M6 3h12v18l-6-4-6 4V3Z',
  spark: 'm12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5L12 3Z',
  chart: 'M4 20V10m8 10V4m8 16v-7',
  trophy: 'M8 3h8v6a4 4 0 0 1-8 0V3Zm0 2H4v3a4 4 0 0 0 4 4m8-7h4v3a4 4 0 0 1-4 4m-4 1v6m-4 2h8',
  search: 'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Zm5 12 6 6',
  arrow: 'M4 12h16m-6-6 6 6-6 6',
  plus: 'M12 5v14M5 12h14',
  check: 'm5 12 4 4L19 6',
  close: 'm6 6 12 12M6 18 18 6',
  chevron: 'm7 10 5 5 5-5',
  globe: 'M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18ZM3 12h18M12 3c-5 5-5 13 0 18 5-5 5-13 0-18Z',
};
function Icon({ name, size = 19 }) { return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.65" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={paths[name] || paths.compass}/></svg>; }
const number = n => new Intl.NumberFormat('en', { notation: n >= 10000 ? 'compact' : 'standard', maximumFractionDigits: 1 }).format(n || 0);
const price = n => n == null ? 'Price unavailable' : n === 0 ? 'Free to play' : `$${Number(n).toFixed(2)}`;
async function api(path, options = {}) {
  const response = await fetch('/api' + path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  if (!response.ok) {
    let message = 'Could not complete the request. Please try again.';
    try { const body = await response.json(); if (typeof body.detail === 'string') message = body.detail; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}
function useData(path, revision = 0) {
  const [state, setState] = useState({ data: null, loading: true, error: null, key: '' });
  const key = `${path}:${revision}`;
  useEffect(() => {
    if (!path) return;
    const controller = new AbortController();
    setState({ data: null, loading: true, error: null, key });
    api(path, { signal: controller.signal }).then(data => setState({ data, loading: false, error: null, key })).catch(error => {
      if (error.name !== 'AbortError') setState({ data: null, loading: false, error: error.message, key });
    });
    return () => controller.abort();
  }, [path, revision]);
  return state.key === key ? state : { data: null, loading: !!path, error: null };
}
function useDebounce(value) { const [v, set] = useState(value); useEffect(() => { const timer = setTimeout(() => set(value), 300); return () => clearTimeout(timer); }, [value]); return v; }
function Artwork({ src, alt, className = '' }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  return src && !failed ? <img className={className} src={src} alt={alt} loading="lazy" onError={() => setFailed(true)}/> : <div className={`art-placeholder ${className}`}><Icon name="compass" size={36}/><span>{alt}</span></div>;
}
function ErrorState({ message, retry }) { return <div className="empty" role="alert"><Icon name="globe" size={30}/><h3>We couldn’t load this</h3><p>{message}</p><button className="primary" onClick={retry}>Try again</button></div>; }

const navigation = [
  ['discover', 'Discover', 'compass'], ['recommendations', 'For you', 'spark'],
  ['library', 'My library', 'library'], ['wishlist', 'Wishlist', 'bookmark'], ['favorites', 'Favorites', 'heart'],
  ['rankings', 'Rankings', 'trophy'], ['analytics', 'Analytics', 'chart'],
];
const titles = { discover: ['Find your next favorite.', 'A whole world of games. A little closer to your taste.'], recommendations: ['Made for your next obsession.', 'Recommendations shaped by your library and the games you love.'], library: ['Your games. Your world.', 'Every adventure you’ve added to your collection.'], wishlist: ['Something to look forward to.', 'Keep your next adventures close.'], favorites: ['The ones that stay with you.', 'Your favorite owned games help us find what comes next.'], rankings: ['See what’s making waves.', 'Explore recorded Steam popularity and our demo community.'], analytics: ['A different view of gaming.', 'Explore the numbers behind the Steam catalog.'] };

function App() {
  const [section, setSection] = useState('discover');
  const [user, setUser] = useState(() => { try { return Number(localStorage.getItem('steamscope-profile')) || 1; } catch { return 1; } });
  const [revision, setRevision] = useState(0);
  const [search, setSearch] = useState(''); const debounced = useDebounce(search);
  const [genre, setGenre] = useState(''); const [platform, setPlatform] = useState('');
  const [sort, setSort] = useState('positive_reviews'); const [page, setPage] = useState(0);
  const [detail, setDetail] = useState(null); const [toast, setToast] = useState(null);
  const [pending, setPending] = useState(null); const mutationLock = useRef(false);
  const [profileOpen, setProfileOpen] = useState(false); const [profileSearch, setProfileSearch] = useState('');
  const [source, setSource] = useState('steam'); const [metric, setMetric] = useState('peak_ccu');
  const summary = useData(`/users/${user}/summary`, revision);
  const profiles = useData(`/users?limit=30&search=${encodeURIComponent(useDebounce(profileSearch))}`);
  const genres = useData('/filters/genre?limit=100');
  const catalog = useData('/games?limit=1');
  const featured = useData(`/games?limit=1&user_id=${user}`, revision);
  useEffect(() => { setPage(0); }, [debounced, genre, platform, sort]);
  useEffect(() => { if (toast) { const timer = setTimeout(() => setToast(null), 4200); return () => clearTimeout(timer); } }, [toast]);
  const navigate = next => { setSection(next); setSearch(''); setGenre(''); setPlatform(''); setSort('positive_reviews'); setPage(0); };
  const selectUser = id => { setUser(id); setProfileOpen(false); setDetail(null); setPage(0); try { localStorage.setItem('steamscope-profile', id); } catch {} };
  const personal = ['library', 'wishlist', 'favorites'].includes(section);
  const query = new URLSearchParams({ limit: 12, offset: page * 12, user_id: user });
  if (debounced) query.set('search', debounced);
  if (genre) query.set('genre', genre);
  if (platform) query.set('platform', platform);
  query.set('sort_by', personal ? (sort === 'name' ? 'name' : 'added_at') : sort);
  query.set('order', sort === 'name' || sort === 'price' ? 'asc' : 'desc');
  const listPath = section === 'discover' ? `/games?${query}` : personal ? `/users/${user}/${section}?${query}` : section === 'recommendations' ? `/users/${user}/recommendations?limit=24` : section === 'rankings' ? `/analytics/rankings?source=${source}&metric=${metric}&user_id=${user}&limit=20` : null;
  const list = useData(listPath, revision);
  const refresh = () => setRevision(r => r + 1);
  async function mutate(game, action) {
    if (mutationLock.current) return;
    mutationLock.current = true; setPending(game.app_id);
    const currentUser = user;
    try {
      if (action === 'favorite') await api(`/users/${currentUser}/library/${game.app_id}/favorite`, { method: 'PATCH', body: JSON.stringify({ is_favorite: !game.is_favorite }) });
      else {
        const exists = action === 'library' ? game.is_owned : game.is_wishlisted;
        await api(`/users/${currentUser}/${action}/${game.app_id}`, { method: exists ? 'DELETE' : 'PUT' });
      }
      refresh();
      setToast({ text: action === 'favorite' ? (game.is_favorite ? 'Removed from favorites' : 'Added to favorites') : action === 'library' ? (game.is_owned ? 'Removed from your library' : 'Added to your library') : (game.is_wishlisted ? 'Removed from wishlist' : 'Added to wishlist') });
    } catch (error) { setToast({ text: error.message, error: true }); }
    finally { mutationLock.current = false; setPending(null); }
  }
  const gameActions = { mutate, pending, open: setDetail };
  const countKey = { library: 'library_count', wishlist: 'wishlist_count', favorites: 'favorite_count' };
  const hero = featured.data?.results[0];
  return <div className="shell">
    <aside className="sidebar">
      <button className="brand" onClick={() => navigate('discover')} aria-label="SteamScope home"><span className="brand-icon"><Icon name="compass" size={25}/></span>Steam<span>Scope</span><i/></button>
      <div className="sidebar-caption">YOUR NEXT ADVENTURE</div>
      <nav aria-label="Main navigation">{navigation.map(([key, label, icon], index) => <React.Fragment key={key}>{index === 2 && <div className="nav-label">YOUR SPACE</div>}{index === 5 && <div className="nav-label">THE BIG PICTURE</div>}<button className={`nav-item ${section === key ? 'active' : ''}`} onClick={() => navigate(key)} aria-current={section === key ? 'page' : undefined}><Icon name={icon}/><span>{label}</span>{countKey[key] && <small>{summary.data?.[countKey[key]] ?? '—'}</small>}{key === 'recommendations' && <span className="little-dot"/>}</button></React.Fragment>)}</nav>
      <div className="sidebar-bottom"><div className="catalog-status"><span className="little-dot"/> A universe worth exploring</div><p>{catalog.data ? catalog.data.total.toLocaleString() : '…'} games. Endless possibilities.</p><div className="demo-note"><Icon name="globe"/><span>Real catalog.<br/>Simulated community.</span></div></div>
    </aside>
    <div className="workspace">
      <header className="topbar"><div className="breadcrumb">Explore <span>/</span> <strong>{navigation.find(n => n[0] === section)[1]}</strong></div><div className="topbar-right"><span className="demo-pill">DEMO MODE</span><div className="profile-wrap"><button className="profile-button" aria-expanded={profileOpen} onClick={() => setProfileOpen(!profileOpen)}><span className="avatar">P{String(user).slice(-2)}</span><span><strong>{summary.data?.username || `Profile ${user}`}</strong><small>Switch demo profile</small></span><Icon name="chevron" size={15}/></button>{profileOpen && <div className="profile-popover"><label htmlFor="profile-search">Choose your demo profile</label><input id="profile-search" autoFocus placeholder="Search player name…" value={profileSearch} onChange={e => setProfileSearch(e.target.value)}/><div className="profile-options">{profiles.loading && <p>Finding profiles…</p>}{profiles.error && <p role="alert">{profiles.error}</p>}{profiles.data?.results.map(p => <button key={p.user_id} onClick={() => selectUser(p.user_id)}>{p.username}{p.user_id === user && <Icon name="check" size={16}/>}</button>)}{profiles.data?.total === 0 && <p>No matching profiles.</p>}</div><button className="text-button" onClick={() => setProfileOpen(false)}>Close picker</button></div>}</div></div></header>
      <main><div className="page-heading"><div><div className="eyebrow"><span/> {section === 'discover' ? 'CURIOSITY LOOKS GOOD ON YOU' : 'YOUR STEAMSCOPE'}</div><h1>{titles[section][0]}</h1><p>{titles[section][1]}</p></div><span className="edition">PLAY. DISCOVER. REPEAT.</span></div>
      {summary.error && <div className="inline-error">Profile unavailable. Choose another demo profile or <button onClick={refresh}>retry</button>.</div>}
      {section === 'discover' && hero && <section className="hero" aria-label="Featured game"><Artwork src={hero.header_image_url} alt="" className="hero-art"/><div className="hero-shade"/><div className="hero-content"><span className="feature-badge"><Icon name="spark" size={14}/> IN THE SPOTLIGHT</span><h2>{hero.name}</h2><p>A community favorite. Your next great session could start here.</p><div className="hero-meta">{hero.genres.slice(0, 2).map(g => <span key={g}>{g}</span>)}<span>{number(hero.positive_reviews)} positive reviews</span></div><button className="primary" onClick={() => setDetail(hero.app_id)}>Explore game <Icon name="arrow" size={17}/></button></div><div className="hero-index"><span>01</span> / DISCOVER SOMETHING GREAT</div></section>}
      {section === 'recommendations' && <div className="context-banner"><Icon name="spark"/><div><strong>{list.data?.strategy === 'popular_fallback' ? 'Start with a community favorite' : 'A little more of what you love'}</strong><p>{list.data?.strategy === 'popular_fallback' ? 'Add games to your library and favorite the ones you love to shape your recommendations.' : 'Shared tags, genres, and developers guide these picks. Favorites have extra influence.'}</p></div></div>}
      {(section === 'discover' || personal) && <><div className="section-title"><h2>{personal ? navigation.find(n => n[0] === section)[1] : 'Explore the catalog'} <span>{list.data ? number(list.data.total) : '…'}</span></h2>{section === 'discover' && <span className="subtle">Find your kind of game</span>}</div><div className="filters"><label className="search-box"><Icon name="search"/><input aria-label="Search games" placeholder={personal ? 'Search your collection…' : 'Search games…'} value={search} onChange={e => setSearch(e.target.value)}/>{search && <button aria-label="Clear search" onClick={() => setSearch('')}><Icon name="close" size={15}/></button>}</label>{!personal && <><select aria-label="Genre" value={genre} onChange={e => setGenre(e.target.value)}><option value="">All genres</option>{genres.data?.results.map(g => <option key={g.id}>{g.name}</option>)}</select><select aria-label="Platform" value={platform} onChange={e => setPlatform(e.target.value)}><option value="">All platforms</option><option>Windows</option><option>Mac</option><option>Linux</option></select></>}<select aria-label="Sort games" value={sort} onChange={e => setSort(e.target.value)}><option value="positive_reviews">{personal ? 'Recently added' : 'Most popular'}</option><option value="name">Name: A–Z</option>{!personal && <><option value="release_date">Newest releases</option><option value="price">Price: low to high</option></>}</select></div></>}
      {section === 'rankings' && <div className="ranking-controls"><div className="segmented">{['steam', 'community'].map(s => <button key={s} className={source === s ? 'selected' : ''} onClick={() => { setSource(s); setMetric(s === 'steam' ? 'peak_ccu' : 'owners'); }}>{s === 'steam' ? 'Steam popularity' : 'Demo community'}</button>)}</div><select aria-label="Ranking metric" value={metric} onChange={e => setMetric(e.target.value)}>{(source === 'steam' ? [['peak_ccu', 'Recorded peak players'], ['positive_reviews', 'Positive reviews'], ['recommendation_count', 'Recommendations']] : [['owners', 'Most owned'], ['active_players', 'Active demo players'], ['play_minutes', 'Recorded play minutes']]).map(([v, label]) => <option value={v} key={v}>{label}</option>)}</select><p className="subtle">{source === 'steam' ? 'Stored catalog measurements · not live player counts' : 'Simulated activity · all recorded time'}</p></div>}
      {section === 'analytics' ? <Analytics revision={revision} retry={refresh}/> : list.error ? <ErrorState message={list.error} retry={refresh}/> : list.loading ? <div className="game-grid" aria-label="Loading games" aria-busy="true">{Array.from({ length: 6 }, (_, i) => <div className="skeleton" key={i}/>)}</div> : !list.data?.results.length ? <div className="empty"><Icon name={section === 'favorites' ? 'heart' : 'search'} size={35}/><h3>{search || genre || platform ? 'No games found' : 'Your next adventure starts here'}</h3><p>{search || genre || platform ? 'Try a different search or loosen your filters.' : section === 'favorites' ? 'Favorite a game in your library to see it here.' : 'Explore the catalog and add a few games to make this space yours.'}</p><button className="primary" onClick={() => navigate('discover')}>Explore games <Icon name="arrow" size={16}/></button></div> : section === 'rankings' ? <div className="ranking-list">{list.data.results.map((game, i) => <button className="ranking-row" key={game.app_id} onClick={() => setDetail(game.app_id)}><span className={`rank ${i < 3 ? 'top' : ''}`}>{String(i + 1).padStart(2, '0')}</span><Artwork src={game.header_image_url} alt=""/><div><h3>{game.name}</h3><p>{game.genres.slice(0, 2).join(' · ') || 'Game'}</p></div><strong>{number(game.metric_value)}<small>{metric.replaceAll('_', ' ')}</small></strong><Icon name="arrow"/></button>)}</div> : <div className="game-grid">{list.data.results.map(game => <GameCard key={game.app_id} game={game} {...gameActions}/>)}</div>}
      {(section === 'discover' || personal) && list.data?.total > 12 && <div className="pagination"><span>{page * 12 + 1}–{Math.min((page + 1) * 12, list.data.total)} of {list.data.total.toLocaleString()} games</span><div><button disabled={page === 0 || list.loading} onClick={() => setPage(p => p - 1)}>Previous</button><span>{page + 1}</span><button disabled={(page + 1) * 12 >= list.data.total || list.loading} onClick={() => setPage(p => p + 1)}>Next <Icon name="arrow" size={15}/></button></div></div>}
      <footer><span>STEAMSCOPE <i> / </i> BUILT FOR THE LOVE OF GAMES</span><span>Steam catalog data · Demo profiles</span></footer>
      </main>
    </div>
    {detail != null && <GameModal id={detail} user={user} revision={revision} close={() => setDetail(null)} retry={refresh} {...gameActions}/>}
    {toast && <div role={toast.error ? 'alert' : 'status'} className={`toast ${toast.error ? 'error' : ''}`}><Icon name={toast.error ? 'close' : 'check'}/>{toast.text}<button aria-label="Dismiss notification" onClick={() => setToast(null)}><Icon name="close" size={15}/></button></div>}
  </div>;
}

function GameCard({ game, open, mutate, pending }) {
  const total = (game.positive_reviews || 0) + (game.negative_reviews || 0);
  const rating = total ? Math.round(game.positive_reviews / total * 100) : null;
  return <article className="game-card"><button className="card-image" aria-label={`View ${game.name}`} onClick={() => open(game.app_id)}><Artwork src={game.header_image_url} alt={game.name}/>{game.is_owned && <span className="owned-badge"><Icon name="check" size={12}/> IN LIBRARY</span>}</button><div className="card-body"><div className="card-title"><button onClick={() => open(game.app_id)}><h3>{game.name}</h3></button><button className={`icon-button ${game.is_favorite || game.is_wishlisted ? 'marked' : ''}`} disabled={pending != null} aria-label={`${game.is_owned ? game.is_favorite ? 'Unfavorite' : 'Favorite' : game.is_wishlisted ? 'Remove from wishlist' : 'Wishlist'} ${game.name}`} onClick={() => mutate(game, game.is_owned ? 'favorite' : 'wishlist')}><Icon name={game.is_owned ? 'heart' : 'bookmark'} size={18}/></button></div><div className="genre-line">{game.genres.slice(0, 2).join(' · ') || 'Explore this game'}</div>{game.reasons?.length > 0 && <div className="reason"><Icon name="spark" size={12}/><span>Shares {game.reasons[0].attribute} with {game.reasons[0].source_game}</span></div>}<div className="card-bottom"><span className={`rating ${rating == null ? 'unrated' : ''}`}>{rating == null ? 'No reviews yet' : <><span>●</span> {rating}% positive</>}</span><span className={`price ${game.price === 0 ? 'free' : ''}`}>{price(game.price)}</span></div></div></article>;
}

function GameModal({ id, user, revision, close, retry, mutate, pending, open }) {
  const { data: game, loading, error } = useData(`/games/${id}?user_id=${user}`, revision);
  const similar = useData(`/games/${id}/similar?user_id=${user}&limit=3`, revision);
  const dialog = useRef(null);
  useEffect(() => {
    const previous = document.activeElement;
    dialog.current.showModal(); document.body.style.overflow = 'hidden';
    return () => { document.body.style.overflow = ''; previous?.focus(); };
  }, []);
  return <dialog ref={dialog} className="game-modal" aria-label="Game details" onCancel={close} onClick={e => { if (e.target === dialog.current) close(); }}><div className="modal-inner"><button className="modal-close icon-button" aria-label="Close game details" onClick={close}><Icon name="close"/></button>{error ? <ErrorState message={error} retry={retry}/> : loading ? <div className="modal-loading">Loading your next adventure…</div> : <><Artwork className="detail-art" src={game.header_image_url} alt={game.name}/><div className="detail-content"><div className="eyebrow">{game.developers.join(' · ') || 'DISCOVER A NEW WORLD'}</div><h2>{game.name}</h2><div className="detail-tags">{game.genres.map(g => <span key={g}>{g}</span>)}<span>{price(game.price)}</span></div><div className="detail-actions"><button className={game.is_owned ? 'secondary' : 'primary'} disabled={pending != null} onClick={() => mutate(game, 'library')}><Icon name={game.is_owned ? 'check' : 'plus'} size={17}/>{game.is_owned ? 'Remove from library' : 'Add to library'}</button>{game.is_owned ? <button className={`secondary ${game.is_favorite ? 'marked' : ''}`} disabled={pending != null} onClick={() => mutate(game, 'favorite')}><Icon name="heart" size={17}/>{game.is_favorite ? 'Favorited' : 'Favorite'}</button> : <button className="secondary" disabled={pending != null} onClick={() => mutate(game, 'wishlist')}><Icon name="bookmark" size={17}/>{game.is_wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}</button>}</div><div className="detail-stats"><div><span>POSITIVE REVIEWS</span><strong>{number(game.positive_reviews)}</strong></div><div><span>RELEASED</span><strong>{game.release_date ? new Date(game.release_date + 'T00:00:00').toLocaleDateString('en', { year: 'numeric', month: 'short', day: 'numeric' }) : 'Unknown'}</strong></div><div><span>PLATFORMS</span><strong>{game.platforms.join(', ') || 'Not listed'}</strong></div></div><h3>About the game</h3><p className="description">{plainText(game.description) || 'No description is available for this game.'}</p>{game.screenshots.length > 0 && <div className="screenshots">{game.screenshots.slice(0, 4).map(src => <Artwork src={src} alt={`${game.name} screenshot`} key={src}/>)}</div>}<h3>A little more like this</h3>{similar.error ? <p className="subtle">Similar games couldn’t be loaded.</p> : <div className="similar-grid">{similar.data?.results.map(g => <button onClick={() => { open(g.app_id); dialog.current.scrollTop = 0; }} key={g.app_id}><Artwork src={g.header_image_url} alt=""/><span>{g.name}</span></button>)}</div>}<p className="subtle detail-note">Library changes apply to your selected demo profile. Catalog prices and statistics are recorded snapshots.</p></div></>}</div></dialog>;
}
function plainText(html) { if (!html) return ''; const doc = new DOMParser().parseFromString(html, 'text/html'); return doc.body.textContent || ''; }

function Analytics({ revision, retry }) {
  const genres = useData('/analytics/genre-stats', revision);
  const platforms = useData('/analytics/platform-stats', revision);
  const yearly = useData('/analytics/yearly-releases', revision);
  const error = genres.error || platforms.error || yearly.error;
  if (error) return <ErrorState message={error} retry={retry}/>;
  if (genres.loading || platforms.loading || yearly.loading) return <div className="skeleton analytics-loading"/>;
  const years = yearly.data.results.filter(r => r.year <= new Date().getFullYear()).slice(-12);
  const top = genres.data.results.slice(0, 7);
  return <div className="analytics-layout"><section className="panel"><div className="eyebrow">THE SHAPE OF THE CATALOG</div><h2>Genres at a glance</h2><p className="subtle">Game counts · a game can belong to multiple genres</p><div className="bar-chart">{top.map(g => <div className="bar-row" key={g.genre}><div><span>{g.genre}</span><strong>{number(g.game_count)}</strong></div><div className="bar-track"><div style={{ width: `${g.game_count / Math.max(1, top[0].game_count) * 100}%` }}/></div></div>)}</div></section><section className="panel"><div className="eyebrow">WHERE WE PLAY</div><h2>Across platforms</h2><p className="subtle">Platform support in the recorded catalog</p>{platforms.data.results.map(p => <div className="platform-stat" key={p.platform}><span><Icon name="globe"/>{p.platform}</span><strong>{number(p.game_count)}<small>games</small></strong></div>)}<div className="context-banner compact"><Icon name="chart"/><p>These figures describe our dataset, not the entire live Steam store.</p></div></section><section className="panel release-panel"><div className="eyebrow">A GROWING WORLD</div><h2>Releases through the years</h2><div className="year-chart">{years.map(y => <div key={y.year} className="year-column"><span>{number(y.games_released)}</span><div style={{ height: `${Math.max(2, y.games_released / Math.max(1, ...years.map(r => r.games_released)) * 155)}px` }}/><small>{y.year}</small></div>)}</div><p className="subtle">Recorded releases by year · recent years may have incomplete coverage</p></section></div>;
}

createRoot(document.getElementById('root')).render(<App/>);
