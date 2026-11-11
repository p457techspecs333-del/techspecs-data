(() => {
  const CATALOGUE_URL = "https://data.techspecs.dev/catalogue.json";
  const API_ROOT = "https://data.techspecs.dev";
  const state = { records: [], filtered: [], selected: [], filter: "all", query: "", visible: 12, loaded: new Map() };
  const $ = (id) => document.getElementById(id);
  const grid = $("product-grid"), status = $("catalogue-status"), search = $("search-input");
  const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const categoryLabel = (value) => ({smartphone:"Smartphones",computer:"Computers",tablet:"Tablets",audio:"Audio",wearable:"Wearables",display:"Displays",speaker:"Audio",headphones:"Audio",earphones:"Audio",keyboard:"Accessories",mouse:"Accessories", "item-tracker":"Accessories"}[value] || String(value || "Technology").replace(/[-_]/g," ").replace(/\b\w/g,c=>c.toUpperCase()));
  const visualClass = (r) => /mac|imac|macbook|computer|laptop/i.test(r.family+" "+r.model) ? "laptop" : /airpods|homepod|speaker|headphone|earphone/i.test(r.family+" "+r.model) ? "audio" : "phone";
  const modelYear = r => r.model_year || r.year_introduced || "";
  function buildFilters() {
    const categories = [...new Set(state.records.map(r=>r.category).filter(Boolean))].sort();
    const row = $("filter-row");
    row.innerHTML = '<button class="filter-chip active" data-filter="all">All products</button>' + categories.map(c=>'<button class="filter-chip" data-filter="'+escapeHtml(c)+'">'+escapeHtml(categoryLabel(c))+'</button>').join("");
    row.addEventListener("click", e => {
      const b=e.target.closest("[data-filter]"); if(!b)return;
      state.filter=b.dataset.filter; row.querySelectorAll("button").forEach(x=>x.classList.toggle("active",x===b)); applyFilters();
    });
  }
  function applyFilters() {
    const q=state.query.trim().toLowerCase();
    state.filtered=state.records.filter(r=>{
      const matchesFilter=state.filter==="all" || r.category===state.filter;
      const text=[r.brand,r.model,r.family,r.category,r.variant,r.model_slug].join(" ").toLowerCase();
      return matchesFilter && (!q || text.includes(q));
    });
    state.visible=12; renderCards();
  }
  function renderCards() {
    const items=state.filtered.slice(0,state.visible);
    grid.innerHTML=items.map(r=>{
      const key=escapeHtml(r.record_id), chosen=state.selected.includes(r.record_id);
      return '<article class="product-card"><div class="product-visual"><div class="visual-device '+visualClass(r)+'"></div></div><div class="product-card-body"><div class="product-brand">'+escapeHtml(r.brand||"")+' · '+escapeHtml(categoryLabel(r.category))+'</div><h3 class="product-name">'+escapeHtml(r.model||r.record_id)+'</h3><div class="product-meta">'+(modelYear(r)?'<span>'+escapeHtml(modelYear(r))+'</span>':'<span>Year not specified</span>')+(r.variant?'<span>· '+escapeHtml(r.variant)+'</span>':'')+'</div><div class="product-status">Source information available</div><div class="card-actions"><a class="card-link" href="?product='+encodeURIComponent(r.record_id)+'">View details ↗</a><button class="compare-toggle '+(chosen?'selected':'')+'" data-compare="'+key+'" aria-pressed="'+chosen+'">'+(chosen?'✓ Added':'+ Compare')+'</button></div></div></article>';
    }).join("");
    $("empty-state").hidden=state.filtered.length!==0;
    $("show-more").hidden=state.visible>=state.filtered.length;
    $("catalogue-status").textContent=state.filtered.length ? "Showing "+items.length+" of "+state.filtered.length+" matching products." : "";
    grid.querySelectorAll("[data-compare]").forEach(b=>b.addEventListener("click",()=>toggleCompare(b.dataset.compare)));
  }
  function toggleCompare(id) {
    if(state.selected.includes(id)) state.selected=state.selected.filter(x=>x!==id);
    else if(state.selected.length<3) state.selected.push(id);
    else return;
    updateCompareBar(); renderCards();
  }
  function updateCompareBar() {
    const bar=$("compare-bar"); bar.hidden=!state.selected.length;
    $("compare-count").textContent=state.selected.length+" selected";
    $("compare-selected").innerHTML=state.selected.map(id=>{const r=state.records.find(x=>x.record_id===id);return '<span class="compare-pill">'+escapeHtml(r?.model||id)+'</span>'}).join("");
    $("compare-button").disabled=state.selected.length<2;
  }
  async function getRecord(r) {
    if(state.loaded.has(r.record_id))return state.loaded.get(r.record_id);
    const response=await fetch(r.url,{headers:{"Accept":"application/json"}});
    if(!response.ok)throw new Error("Could not load "+r.model);
    const record=await response.json(); state.loaded.set(r.record_id,record); return record;
  }
  const pretty = key => String(key).replace(/_/g," ").replace(/\b\w/g,c=>c.toUpperCase());
  function normalizedFields(record) {
    const p=record.product||{}, output=[];
    for(const [k,v] of Object.entries(p)) if(!["brand","category","family","model","model_slug","model_year","year_introduced","variant"].includes(k) && v!==null && v!=="" && (!Array.isArray(v)||v.length)) output.push([pretty(k),Array.isArray(v)?v.join(", "):String(v)]);
    for(const [k,v] of Object.entries(record.specifications||record.normalized_specifications||{})) if(v!==null && v!=="" ) output.push([pretty(k),typeof v==="object"?JSON.stringify(v):String(v)]);
    return output;
  }
  async function openComparison() {
    const dialog=$("compare-dialog"), content=$("comparison-content");
    dialog.showModal(); content.innerHTML='<p class="comparison-empty">Loading product records…</p>';
    try {
      const records=await Promise.all(state.selected.map(id=>getRecord(state.records.find(r=>r.record_id===id))));
      const rows=new Map();
      records.forEach((r,i)=>normalizedFields(r).forEach(([k,v])=>{if(!rows.has(k))rows.set(k,Array(records.length).fill("—"));rows.get(k)[i]=v}));
      content.innerHTML='<table class="comparison-table"><thead><tr><th>Specification</th>'+records.map(r=>'<th>'+escapeHtml(r.product?.model||"Product")+'</th>').join("")+'</tr></thead><tbody>'+[...rows].map(([k,values])=>'<tr><td>'+escapeHtml(k)+'</td>'+values.map(v=>'<td>'+escapeHtml(v)+'</td>').join("")+'</tr>').join("")+'</tbody></table><p class="comparison-note">Only fields present in the selected records are shown. A dash means the record does not provide that value. Original source wording and verification status remain available in each product record.</p>';
    } catch(e) {content.innerHTML='<p class="comparison-empty">We could not retrieve one of the product records. Please try again.</p>'}
  }
  async function openProductFromUrl() {
    const id=new URLSearchParams(location.search).get("product"); if(!id)return;
    const recordIndex=state.records.findIndex(r=>r.record_id===id); if(recordIndex<0)return;
    const r=state.records[recordIndex];
    try {
      const data=await getRecord(r), fields=normalizedFields(data);
      const dialog=$("compare-dialog");
      $("comparison-content").innerHTML='<div class="product-detail"><div class="section-kicker">'+escapeHtml(data.product?.brand||r.brand)+' · '+escapeHtml(categoryLabel(data.product?.category||r.category))+'</div><h2>'+escapeHtml(data.product?.model||r.model)+'</h2><p>'+escapeHtml(data.extraction?.note||"Product information retained from the cited manufacturer source.")+'</p><h3>Product details</h3><table class="comparison-table"><tbody>'+fields.map(([k,v])=>'<tr><td>'+escapeHtml(k)+'</td><td>'+escapeHtml(v)+'</td></tr>').join("")+'</tbody></table><h3>Original source</h3><p><a class="card-link" href="'+escapeHtml(data.source?.source_url||r.source?.source_url||"#")+'" target="_blank" rel="noreferrer">'+escapeHtml(data.source?.source_title||"Manufacturer documentation")+' ↗</a></p><p class="comparison-note">Source status: '+escapeHtml(data.source?.verification_status||"not specified")+' · Last checked: '+escapeHtml(data.source?.checked_at||"not specified")+'</p></div>';
      dialog.showModal();
    } catch(e) { status.textContent="We couldn't load that product's detail record.";status.classList.add("error");}
  }
  async function init() {
    try {
      const res=await fetch(CATALOGUE_URL,{headers:{"Accept":"application/json"}});
      if(!res.ok)throw new Error("Catalogue request returned "+res.status);
      const catalogue=await res.json();
      state.records=(catalogue.records||[]).filter(r=>r&&r.record_id&&r.url).sort((a,b)=>(a.brand||"").localeCompare(b.brand||"")||(a.category||"").localeCompare(b.category||"")||(a.model||"").localeCompare(b.model||""));
      $("catalogue-count").textContent=(catalogue.record_count||state.records.length)+" product records";
      status.textContent="Catalogue connected. Explore the available products below.";
      buildFilters();applyFilters();openProductFromUrl();
    } catch(e) {
      status.classList.add("error");
      status.textContent="The product catalogue could not be reached. The website needs the data host to allow browser requests from techspecs.ie (CORS). The catalogue itself remains available at data.techspecs.dev.";
      $("catalogue-count").textContent="Catalogue connection pending";
    }
  }
  search.addEventListener("input",()=>{state.query=search.value;applyFilters()});
  search.addEventListener("keydown",e=>{if((e.metaKey||e.ctrlKey)&&e.key==="k"){e.preventDefault();search.focus()}});
  $("show-more").addEventListener("click",()=>{state.visible+=12;renderCards()});
  $("compare-button").addEventListener("click",openComparison);
  $("clear-compare").addEventListener("click",()=>{state.selected=[];updateCompareBar();renderCards()});
  $("close-dialog").addEventListener("click",()=>$("compare-dialog").close());
  $("menu-toggle").addEventListener("click",()=>{const nav=document.querySelector(".main-nav"),open=nav.classList.toggle("open");$("menu-toggle").setAttribute("aria-expanded",String(open))});
  document.querySelectorAll("[data-jump]").forEach(a=>a.addEventListener("click",()=>{const target=a.dataset.jump;state.filter=state.records.some(r=>r.category===target)?target:"all";document.querySelectorAll(".filter-chip").forEach(b=>b.classList.toggle("active",b.dataset.filter===state.filter));applyFilters()}));
  init();
})();