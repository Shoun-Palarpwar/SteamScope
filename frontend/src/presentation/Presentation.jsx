import React, { useEffect, useRef, useState } from 'react';
import deck from './deck.json';
import evidence from './evidence.json';
import source from './source-audit.json';
import diagrams from './diagrams.json';
import './presentation.css';

const fmt = n => Number(n).toLocaleString('en');
const tableMap = Object.fromEntries(evidence.tables.map(t => [t.name, t]));
const snapshot = new Date(evidence.captured_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' });
const PDF = '/presentation/SteamScope-Database-Presentation.pdf';

function Stat({ value, label }) { return <div className="pres-stat"><strong>{value}</strong><span>{label}</span></div>; }
function MiniTable({ rows }) {
  if (!rows.length) return <p>No saved rows.</p>;
  const columns = Object.keys(rows[0]);
  return <div className="pres-table-scroll"><table><thead><tr>{columns.map(c => <th key={c}>{c.replaceAll('_', ' ')}</th>)}</tr></thead><tbody>{rows.map((row, i) => <tr key={i}>{columns.map(c => <td key={c}>{typeof row[c] === 'number' ? fmt(row[c]) : String(row[c])}</td>)}</tr>)}</tbody></table></div>;
}
function Schema({ kind }) {
  const graph = diagrams[kind];
  const [selected, setSelected] = useState('game');
  const [zoom, setZoom] = useState(1);
  const nodeMap = Object.fromEntries(graph.nodes.map(n => [n.name, n]));
  const table = tableMap[selected];
  const related = evidence.foreign_keys.filter(f => f.parent === selected || f.child === selected);
  return <div className="pres-schema"><div className="pres-schema-toolbar"><span>1 = one parent · 0..N = zero or many linked rows</span><div><button onClick={() => setZoom(z => Math.max(.75, z - .25))} aria-label="Zoom out schema">−</button><span>{Math.round(zoom * 100)}%</span><button onClick={() => setZoom(z => Math.min(2, z + .25))} aria-label="Zoom in schema">+</button><button onClick={() => setZoom(1)}>Reset</button></div></div><div className="pres-schema-scroll"><svg width={`${zoom * 100}%`} viewBox={`0 0 ${graph.width} ${graph.height}`} role="group" aria-label={`${kind} schema: select a table to inspect its fields`} style={{ minWidth: 740 * zoom }}>
    {graph.edges.map(edge => {
      const p = nodeMap[edge.parent], c = nodeMap[edge.child];
      const horizontal = Math.abs(p.x - c.x) > Math.abs(p.y - c.y);
      let a, b, path;
      if (horizontal) {
        a = [p.x + (p.x < c.x ? p.width : 0), p.y + p.height / 2];
        b = [c.x + (p.x < c.x ? 0 : c.width), c.y + c.height / 2];
        const mid = (a[0] + b[0]) / 2;
        path = `M${a} C${mid},${a[1]} ${mid},${b[1]} ${b}`;
      } else {
        a = [p.x + p.width / 2, p.y + p.height]; b = [c.x + c.width / 2, c.y];
        path = `M${a} C${a[0]},${(a[1]+b[1])/2} ${b[0]},${(a[1]+b[1])/2} ${b}`;
      }
      const active = edge.parent === selected || edge.child === selected;
      return <g key={edge.name} className={active ? 'pres-edge active' : 'pres-edge'}><title>{edge.parent}.{edge.parent_key} → {edge.child}.{edge.child_key}; one parent to zero or many child rows</title><path d={path}/><text x={a[0] + (horizontal ? p.x < c.x ? 8 : -12 : 8)} y={a[1]-7}>1</text><text x={b[0] + (horizontal ? p.x < c.x ? -34 : 8 : 8)} y={b[1]-7}>0..N</text></g>;
    })}
    {graph.nodes.map(node => <g key={node.name} className={`pres-node ${selected === node.name ? 'selected' : ''}`} role="button" tabIndex={0} aria-label={`Inspect ${node.name}`} aria-pressed={selected === node.name} onClick={() => setSelected(node.name)} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setSelected(node.name); } }}><rect x={node.x} y={node.y} width={node.width} height={node.height} rx={8}/><text className="pres-node-name" x={node.x+13} y={node.y+23}>{node.name}</text>{node.fields.map((f, i) => <text className="pres-node-field" key={f} x={node.x+13} y={node.y+43+i*16}>{f}</text>)}</g>)}
    </svg></div><div className="pres-inspector"><div><span className="pres-kicker">TABLE INSPECTOR</span><h3>{selected}</h3><p>{fmt(table.count)} saved rows · PK = unique identity · FK = reference to another table</p></div><MiniTable rows={table.columns.map(c => ({field:c.name, type:c.type, keys:[c.key === 'PRI' ? 'PK' : '', evidence.foreign_keys.some(f => f.child === selected && f.child_key === c.name) ? 'FK' : '', c.key === 'UNI' ? 'UNIQUE' : ''].filter(Boolean).join(' + ') || '—', missing_allowed:c.nullable === 'YES' ? 'Yes' : 'No'}))}/><details><summary>Show the connected tables ({related.length})</summary>{related.map(f => <p key={f.name}><code>{f.child}.{f.child_key}</code> → <code>{f.parent}.{f.parent_key}</code> · delete rule: {f.delete_rule}</p>)}</details><details><summary>Show the saved CREATE TABLE statement</summary><pre>{table.ddl}</pre></details></div></div>;
}

const cleaningExamples = [
  {name:'Trim text', before:'"  Counter-Strike 2  "', after:'"Counter-Strike 2"', note:'Illustrative whitespace example. The title stays the same; only surrounding spaces disappear.'},
  {name:'Missing values', before:'"   " or an unreadable number', after:'NULL (unknown)', note:'The cleaner/loader leaves unknown values missing. It does not replace them with invented zeros.'},
  {name:'A date', before:'"Aug 21, 2012"', after:'2012-08-21', note:'This date comes from the JSON record for app_id 730. The loader recognizes this date format.'},
  {name:'A list', before:'genres: ["Action", "Free To Play"]', after:'Two game_genre relationships', note:'These genres come from the same source record. Each name is matched to a genre ID when loaded.'},
];
function Cleaning() { const [index, setIndex] = useState(0); const e = cleaningExamples[index]; return <><div className="pres-tabs" aria-label="Cleaning examples">{cleaningExamples.map((e,i) => <button key={e.name} aria-pressed={i===index} onClick={() => setIndex(i)}>{e.name}</button>)}</div><div className="pres-before-after"><div><span>BEFORE</span><code>{e.before}</code></div><b>→</b><div><span>AFTER</span><code>{e.after}</code></div></div><p className="pres-caption">{e.note}</p></>; }
function Score() { const [tags,setTags]=useState(2); const [genres,setGenres]=useState(1); const [dev,setDev]=useState(0); const [fav,setFav]=useState(false); const base=tags*3+genres+dev*2; return <div className="pres-calculator"><div><span className="pres-kicker">TRY A SINGLE-SOURCE EXAMPLE</span>{[['Shared tags',tags,setTags,5],['Shared genres',genres,setGenres,3],['Shared developers',dev,setDev,2]].map(([label,value,set,max]) => <label key={label}>{label} <strong>{value}</strong><input aria-label={label} type="range" min="0" max={max} value={value} onChange={e => set(Number(e.target.value))}/></label>)}<label className="pres-check"><input type="checkbox" checked={fav} onChange={e => setFav(e.target.checked)}/> This source game is a favorite</label></div><div className="pres-score"><span>ILLUSTRATIVE MATCH SCORE</span><strong>{base*(fav?3:1)}</strong><p>({tags} × 3 + {genres} × 1 + {dev} × 2) × {fav?3:1}</p><small>No database writes. This illustrates the rule, not an actual recommended game.</small></div></div>; }
function Transaction() { const [step,setStep]=useState(0); const [fail,setFail]=useState(false); const finished=step===3; const owned=finished?!fail:step>=1; const wished=finished?fail:step<2; return <div className="pres-transaction"><span className="pres-kicker">SAFE SIMULATION · NO DATABASE CHANGES</span><div className="pres-steps">{['Start','Add library row','Remove wishlist row',fail?'Rollback':'Commit'].map((label,i)=><span className={i===step?'current':''} key={i}>{i+1}. {label}</span>)}</div><div className="pres-transaction-state"><Stat value={owned?'Present':'Absent'} label="Library row"/><Stat value={wished?'Present':'Absent'} label="Wishlist row"/></div><p>{finished ? fail?'A simulated error restored the original state.':'Both changes are saved together.' : step===0?'The game starts on the wishlist.':'These changes are pending inside the transaction.'}</p><label className="pres-check"><input type="checkbox" checked={fail} disabled={step>0} onChange={e=>setFail(e.target.checked)}/> Simulate an error before commit</label><div className="pres-inline-actions"><button onClick={()=>setStep(s=>Math.min(3,s+1))} disabled={finished}>Next step →</button><button onClick={()=>setStep(0)}>Reset demo</button></div></div>; }
function Queries() { const [index,setIndex]=useState(0); const q=evidence.query_examples[index]; return <><div className="pres-tabs">{evidence.query_examples.map((q,i)=><button key={q.title} onClick={()=>setIndex(i)} aria-pressed={i===index}>{q.title}</button>)}</div><div className="pres-query"><pre>{q.sql}</pre><div><span className="pres-kicker">SAVED RESULT · {snapshot} IST</span><MiniTable rows={q.rows}/><p className="pres-caption">{index===0?'Demo ownership counts, not real Steam owners.':'Games may belong to more than one genre.'}</p></div></div></>; }

function Visual({ slide }) {
  switch(slide.kind) {
    case 'intro': return <div className="pres-stats"><Stat value={fmt(tableMap.game.count)} label="catalog games"/><Stat value={evidence.tables.length} label="connected tables"/><Stat value={fmt(tableMap.user.count)} label="demo profiles"/></div>;
    case 'source': return <div className="pres-source-grid"><div><span className="pres-kicker">EARLY CSV SAMPLE</span><MiniTable rows={[{heading:'About the game',observed:'Numeric values',expected:'Description text'},{heading:'Metacritic score',observed:'Boolean values',expected:'A numeric score'},{heading:'Website',observed:'Image URLs',expected:'Website URLs'}]}/></div><div className="pres-source-json"><span className="pres-kicker">REAL JSON EXCERPT · APP 730</span><pre>{JSON.stringify(source.samples.find(s=>s.app_id===730),null,2)}</pre></div></div>;
    case 'pipeline': return <><div className="pres-stats"><Stat value={fmt(source.counts.records)} label="JSON records read"/><Stat value={source.counts.missing_names} label="missing name: skipped"/><Stat value={fmt(source.counts.retained)} label="records retained"/></div><div className="pres-flow">{['Read JSON','Clean values','Extract names','Load games','Load links','Validate'].map((p,i)=><div key={p}><b>{String(i+1).padStart(2,'0')}</b>{p}</div>)}</div><p className="pres-caption">Source size: {(source.bytes/1e6).toFixed(1)} MB. This pass found {source.counts.duplicate_ids} duplicate IDs and {source.counts.invalid_ids} invalid IDs.</p></>;
    case 'cleaning': return <Cleaning/>;
    case 'normalization': return <div className="pres-normalization"><MiniTable rows={[{game:'Counter-Strike',app_id:10},{game:'Counter-Strike 2',app_id:730}]}/><span>connect through</span><MiniTable rows={[{app_id:10,genre:'Action'},{app_id:730,genre:'Action'},{app_id:730,genre:'Free To Play'}]}/><span>to</span><MiniTable rows={[{genre:'Action'},{genre:'Free To Play'}]}/><p className="pres-caption">Simplified teaching view: real source titles and genres; the stored linking table uses genre_id instead of the genre name.</p></div>;
    case 'inventory': return <><div className="pres-inventory">{evidence.tables.map(t=><div key={t.name}><code>{t.name}</code><strong>{fmt(t.count)}</strong><small>rows</small></div>)}</div><p className="pres-caption">The review table has {fmt(tableMap.review.count)} rows. Review totals used by the app are game-level catalog fields, not imported review text.</p></>;
    case 'catalog-schema': return <Schema kind="catalog"/>;
    case 'player-schema': return <Schema kind="player"/>;
    case 'integrity': return <><div className="pres-stats"><Stat value={evidence.foreign_keys.length} label="declared links checked"/><Stat value={evidence.foreign_keys.reduce((sum,f)=>sum+f.orphans,0)} label="orphan rows found"/><Stat value={fmt(evidence.quality.unique_ids)} label="distinct game IDs"/></div><MiniTable rows={[{check:'Missing or blank game names',count:Number(evidence.quality.missing_names)},{check:'NULL prices',count:Number(evidence.quality.unknown_prices)},{check:'NULL release dates',count:Number(evidence.quality.unknown_dates)}]}/><p className="pres-caption">A zero NULL count does not verify source accuracy or rule out placeholder values. Delete behavior and exact keys are available in the schema inspector.</p></>;
    case 'queries': return <Queries/>;
    case 'recommendations': return <Score/>;
    case 'transactions': return <Transaction/>;
    case 'stack': return <div className="pres-flow pres-stack">{[['01','REACT','Shows the interface'],['02','FASTAPI','Checks the request'],['03','RAW SQL','Asks the question'],['04','MYSQL','Stores the facts']].map(([n,title,text])=><div key={title}><b>{n}</b><strong>{title}</strong><span>{text}</span></div>)}</div>;
    case 'conclusion': return <div className="pres-closing"><span>THE DATABASE IS THE STORY.</span><h3>Clean it.<br/>Connect it.<br/><em>Build on it.</em></h3></div>;
    case 'evidence': return <div className="pres-evidence"><p><strong>Database capture:</strong> {snapshot} IST</p><p><strong>JSON audit:</strong> {fmt(source.counts.records)} records inspected from games.json.</p><p><strong>Diagram coverage:</strong> all {evidence.tables.length} tables and {evidence.foreign_keys.length} declared foreign keys, across two diagrams.</p><p><strong>Snapshot privacy:</strong> schema, aggregate counts, and public game results only. No profile rows, emails, or passwords.</p><a href={PDF} download>Download the matching PDF ↗</a></div>;
    default: return null;
  }
}

export default function Presentation({ onExit }) {
  const initial = deck.slides.findIndex(s=>s.id===window.location.hash.split('/')[1]);
  const [index,setIndex]=useState(initial<0?0:initial);
  const [notes,setNotes]=useState(false);
  const [full,setFull]=useState(false);
  const [message,setMessage]=useState('');
  const root=useRef(null); const slideTop=useRef(null);
  const slide=deck.slides[index];
  const go = n => setIndex(Math.max(0,Math.min(deck.slides.length-1,n)));
  useEffect(()=>{ history.replaceState(null,'',`#presentation/${slide.id}`); slideTop.current?.scrollIntoView({block:'start'}); },[slide.id]);
  useEffect(()=>{
    const key=e=>{
      if(e.target.closest('input,select,textarea,button,a,[role="button"]') || e.altKey || e.ctrlKey || e.metaKey) return;
      if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();setIndex(i=>Math.min(deck.slides.length-1,i+1));}
      if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();setIndex(i=>Math.max(0,i-1));}
      if(e.key==='Home'){e.preventDefault();setIndex(0);}
      if(e.key==='End'){e.preventDefault();setIndex(deck.slides.length-1);}
    };
    const changed=()=>setFull(document.fullscreenElement===root.current);
    window.addEventListener('keydown',key);document.addEventListener('fullscreenchange',changed);
    return()=>{window.removeEventListener('keydown',key);document.removeEventListener('fullscreenchange',changed);};
  },[]);
  async function fullscreen(){try{if(document.fullscreenElement)await document.exitFullscreen();else await root.current.requestFullscreen();setMessage('');}catch{setMessage('Fullscreen is unavailable in this browser. The presentation still works in this view.');}}
  return <section className="presentation" ref={root} aria-label="Behind SteamScope presentation"><header className="pres-header"><div><span className="pres-kicker">DATABASE PROJECT / PRESENTATION</span><h2>Behind SteamScope<span>.</span></h2></div><div className="pres-tools"><a href={PDF} download>Download PDF ↓</a><button onClick={()=>setNotes(!notes)} aria-pressed={notes}>Speaker notes</button><button onClick={fullscreen}>{full?'Exit fullscreen':'Present fullscreen'}</button><button onClick={onExit}>Back to app ↗</button></div></header>{message&&<p role="status">{message}</p>}<div className="pres-outline" aria-label="Presentation chapters">{deck.slides.map((s,i)=><button key={s.id} aria-current={i===index?'step':undefined} title={s.title} onClick={()=>go(i)}><span>{String(i+1).padStart(2,'0')}</span>{s.chapter.split(' / ')[1]}</button>)}</div><article className={`pres-slide pres-kind-${slide.kind}`} ref={slideTop} tabIndex={-1}><div className="pres-slide-heading"><span className="pres-kicker">{slide.chapter}</span><span className="pres-snapshot">Saved evidence · {new Date(evidence.captured_at).toLocaleDateString('en-IN',{timeZone:'Asia/Kolkata'})}</span><h1>{slide.title}</h1><p>{slide.lead}</p></div><div className="pres-visual" key={slide.id}><Visual slide={slide}/></div><div className="pres-points">{slide.points.map(([title,text],i)=><div key={title}><span>{String(i+1).padStart(2,'0')}</span><h3>{title}</h3><p>{text}</p></div>)}</div><div className="pres-takeaway"><span>THE TAKEAWAY</span><p>{slide.takeaway}</p></div>{notes&&<aside className="pres-notes"><h3>Presenter notes</h3><p>{slide.notes}</p><h4>Evidence behind this slide</h4><ul>{slide.sources.map(s=><li key={s}><code>{s}</code></li>)}</ul></aside>}</article><footer className="pres-footer"><button onClick={()=>go(index-1)} disabled={index===0}>← Previous</button><div><strong>{String(index+1).padStart(2,'0')} / {deck.slides.length}</strong><span>Arrow keys to navigate · interactive controls use their own keys</span></div><button onClick={()=>go(index+1)} disabled={index===deck.slides.length-1}>Next →</button></footer></section>;
}
