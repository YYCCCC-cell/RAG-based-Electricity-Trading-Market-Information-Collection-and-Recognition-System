const labels={transaction_action:'交易行动',rules_policy:'规则政策',results_settlement:'结果结算',service_other:'服务其他'};
let notices=[];
let staticMode=false;
let searchIndex=null;

function cell(text,className=''){
  const td=document.createElement('td');
  td.textContent=text??'—';
  if(className)td.className=className;
  return td;
}

function badge(text,alert=false){
  const span=document.createElement('span');
  span.className='tag'+(alert?' alert':'');
  span.textContent=text;
  return span;
}

function render(filter='all'){
  const body=document.querySelector('#rows');
  body.replaceChildren();
  notices.filter(n=>filter==='all'||n.prediction.category===filter).forEach(n=>{
    const tr=document.createElement('tr');
    const rules=(n.prediction.matched_rules||[]).slice(0,3).join('、')||'兜底规则';
    tr.appendChild(cell(n.published_date));

    const titleCell=cell('');
    const link=document.createElement('a');
    link.href=n.url;
    link.target='_blank';
    link.rel='noreferrer';
    link.textContent=n.title;
    titleCell.appendChild(link);
    tr.appendChild(titleCell);

    const categoryCell=cell('');
    categoryCell.appendChild(badge(labels[n.prediction.category]||n.prediction.category));
    tr.appendChild(categoryCell);

    const alertCell=cell('');
    alertCell.appendChild(n.prediction.market_impacting?badge('需复核',true):document.createTextNode('常规'));
    tr.appendChild(alertCell);
    tr.appendChild(cell(`${rules} · ${(n.prediction.confidence*100).toFixed(0)}%`,'reason'));
    body.appendChild(tr);
  });
}

function tokenize(text){
  const tokens=(text.match(/[A-Za-z0-9_]+/g)||[]).map(token=>token.toLowerCase());
  for(const run of text.match(/[\u4e00-\u9fff]+/g)||[]){
    if(run.length===1)tokens.push(run);
    for(let i=0;i<run.length-1;i++)tokens.push(run.slice(i,i+2));
    for(const char of run){
      if('年月日时前后交易结算规则申报绿电绿证'.includes(char))tokens.push(char);
    }
  }
  return tokens;
}

function counts(tokens){
  const result=new Map();
  for(const token of tokens)result.set(token,(result.get(token)||0)+1);
  return result;
}

function buildSearchIndex(rows){
  const docs=rows.map(row=>counts(tokenize(`${row.title}\n${row.body||''}`)));
  const lengths=docs.map(doc=>[...doc.values()].reduce((a,b)=>a+b,0));
  const average=lengths.reduce((a,b)=>a+b,0)/Math.max(1,lengths.length);
  const documentFrequency=new Map();
  docs.forEach(doc=>doc.forEach((_,term)=>documentFrequency.set(term,(documentFrequency.get(term)||0)+1)));
  const idf=new Map();
  documentFrequency.forEach((frequency,term)=>idf.set(term,Math.log(1+(rows.length-frequency+.5)/(frequency+.5))));
  return {docs,lengths,average,idf};
}

function excerpt(row,query){
  const terms=new Set(tokenize(query));
  const sentences=(row.body||row.title).split(/[。！？\n]+/).map(text=>text.trim()).filter(Boolean);
  sentences.sort((a,b)=>{
    const overlap=text=>[...new Set(tokenize(text))].filter(term=>terms.has(term)).length;
    return overlap(b)-overlap(a);
  });
  const best=sentences[0]||row.title;
  return best.length>180?best.slice(0,180)+'…':best;
}

function localAnswer(query){
  const queryCounts=counts(tokenize(query));
  const hits=notices.map((row,index)=>{
    let score=0;
    queryCounts.forEach((queryFrequency,term)=>{
      const frequency=searchIndex.docs[index].get(term)||0;
      if(!frequency)return;
      const denominator=frequency+1.5*(1-.75+.75*searchIndex.lengths[index]/Math.max(1,searchIndex.average));
      score+=(searchIndex.idf.get(term)||0)*frequency*2.5/denominator*Math.min(queryFrequency,2);
    });
    return {row,score};
  }).filter(hit=>hit.score>0).sort((a,b)=>b.score-a.score||b.row.published_date.localeCompare(a.row.published_date)).slice(0,3);
  if(!hits.length)return {answer:'在当前快照中没有检索到足够相关的公开通知。请换用通知标题中的关键词。',citations:[]};
  return {
    answer:'根据检索到的公开通知：\n'+hits.map(hit=>`- ${excerpt(hit.row,query)} [${hit.row.notice_id}]`).join('\n'),
    citations:hits.map(hit=>({notice_id:hit.row.notice_id,title:hit.row.title,url:hit.row.url}))
  };
}

async function loadNotices(){
  try{
    const response=await fetch('/api/notices');
    if(!response.ok)throw new Error('API unavailable');
    return await response.json();
  }catch(_error){
    const response=await fetch('./notices.json');
    if(!response.ok)throw new Error('snapshot unavailable');
    staticMode=true;
    return await response.json();
  }
}

loadNotices()
  .then(data=>{
    notices=data;
    searchIndex=buildSearchIndex(data);
    document.querySelector('#total').textContent=data.length;
    document.querySelector('#impact').textContent=data.filter(n=>n.prediction.market_impacting).length;
    document.querySelector('#review').textContent=data.filter(n=>n.prediction.risk_flags.includes('human_review')).length;
    render();
  })
  .catch(()=>{document.querySelector('#rows').textContent='无法载入通知快照，请稍后重试。';});

document.querySelector('#filter').addEventListener('change',event=>render(event.target.value));

document.querySelector('#ask-form').addEventListener('submit',async event=>{
  event.preventDefault();
  const question=document.querySelector('#question').value.trim();
  const box=document.querySelector('#answer');
  if(!question||question.length>300){
    box.textContent='请输入 1–300 个字符的问题。';
    return;
  }
  box.textContent='检索中…';
  try{
    let result;
    if(staticMode){
      result=localAnswer(question);
    }else{
      const response=await fetch('/api/ask?q='+encodeURIComponent(question));
      result=await response.json();
      if(!response.ok)throw new Error(result.error||'request failed');
    }
    box.textContent=result.answer+'\n';
    result.citations.forEach(citation=>{
      const source=document.createElement('a');
      source.href=citation.url;
      source.target='_blank';
      source.rel='noreferrer';
      source.textContent=`${citation.notice_id} · ${citation.title}`;
      box.appendChild(source);
    });
  }catch(error){
    box.replaceChildren();
    const message=document.createElement('span');
    message.className='error';
    message.textContent='无法完成检索：'+error.message;
    box.appendChild(message);
  }
});
