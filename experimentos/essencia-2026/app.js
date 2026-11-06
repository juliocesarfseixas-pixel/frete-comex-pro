/* Raio-X do Transportador · Estudo visual de restauração, não conectado à produção.
   O conteúdo das 35 perguntas e das 175 alternativas vem do catálogo V5.9 original. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const catalog = JSON.parse($('questionCatalog').textContent);
  const qs = catalog.questions;
  const dimensions = [...new Set(qs.map(q => q.dimension))];
  const UNKNOWN = null;
  const state = { answers: Array(35).fill(undefined), index: 0, company: '', email: '', responsible: '', demo: false, reportId: '' };
  const classes = ['Não executado','Execução inicial','Execução parcial','Execução regular','Execução acompanhada'];
  const esc = s => String(s ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const isValid = v => Number.isInteger(v) && v >= 0 && v <= 4;
  const isAnswered = v => v !== undefined;
  const fmt = v => v === null ? 'N/D' : `${v}%`;
  const classify = v => v === null ? 'Nota indisponível' : v < 25 ? 'Crítico' : v < 50 ? 'Inicial' : v < 70 ? 'Em desenvolvimento' : v < 85 ? 'Estruturado' : 'Avançado';
  const byDimension = d => qs.map((q,i)=>({q,i,v:state.answers[i]})).filter(x=>x.q.dimension===d);
  const scoreDimension = rows => {
    const valid = rows.filter(x=>isValid(x.v));
    const enough = valid.length >= Math.ceil(rows.length * .80);
    return {valid: valid.length,total:rows.length,score:enough?Math.round(valid.reduce((a,x)=>a+x.v,0)/valid.length*25):null,enough};
  };
  const summarize = () => {
    const dims = dimensions.map(name=>({name,...scoreDimension(byDimension(name))}));
    const governance = dims[0];
    const departments = dims.slice(1);
    const knownDept = qs.slice(10).map((q,i)=>state.answers[i+10]).filter(isValid);
    const departmentScore = departments.every(d=>d.enough) ? Math.round(knownDept.reduce((a,b)=>a+b,0)/knownDept.length*25) : null;
    return {governance,departments,departmentScore,
      valid:state.answers.filter(isValid).length,
      unknown:state.answers.filter(v=>v===null).length,
      answered:state.answers.filter(isAnswered).length};
  };
  const viewport = () => window.scrollTo({top:0,behavior:'instant'});
  const show = id => { ['landing','questionnaire','reportScreen'].forEach(k=>$(k).classList.toggle('hidden',k!==id)); viewport(); };
  const newId = () => {
    const d=new Date();
    return `RX-${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}-${Math.random().toString(36).slice(2,8).toUpperCase()}`;
  };

  function renderQuestion(){
    const i = state.index, question=qs[i];
    const group = dimensions.indexOf(question.dimension);
    const completed = state.answers.filter(isAnswered).length;
    $('stepLabel').textContent=`Etapa ${group+1} de 6 · ${i<10?'Governo Empresarial':'Gestão departamental'}`;
    $('stepHeading').textContent=question.dimension;
    $('qBadge').textContent=`${String(i+1).padStart(2,'0')} / 35`;
    $('qProgressText').textContent=`Questão ${i+1} de 35`;
    $('qCoverage').textContent=`${completed} de 35 respondidas`;
    $('qProgress').style.width=`${completed/35*100}%`;
    $('progressContainer').setAttribute('aria-valuenow', String(completed));
    $('qTheme').textContent=`Dimensão ${group+1} · ${question.dimension}`;
    $('qText').textContent=question.question;
    const selected = state.answers[i];
    const choices = question.options.map((op,n)=>`<button type="button" class="choice ${selected===n?'selected':''}" data-score="${n}" aria-pressed="${selected===n}"><span class="score">${n}</span><span class="opttext">${esc(op)}</span></button>`);
    choices.push(`<button type="button" class="choice unknown ${selected===null?'selected':''}" data-score="unknown" aria-pressed="${selected===null}"><span class="score">?</span><span class="opttext">Não sei informar <small>— sem pontuação</small></span></button>`);
    $('choices').innerHTML=choices.join('');
    $('choices').querySelectorAll('button').forEach(btn=>btn.addEventListener('click',()=>{
      state.answers[i] = btn.dataset.score === 'unknown' ? UNKNOWN : Number(btn.dataset.score);
      renderQuestion();
    }));
    $('qBack').textContent=i===0?'← Voltar ao início':'← Pergunta anterior';
    $('qNext').textContent=i===34?'Ver meu diagnóstico →':'Próxima questão →';
    $('qNext').disabled=!isAnswered(selected);
  }

  function begin(event){
    event.preventDefault();
    const form=$('startForm');
    if(!form.reportValidity())return;
    state.company=$('company').value.trim();
    state.email=$('email').value.trim();
    state.responsible=$('responsible').value.trim();
    if(state.company.length < 2 || !state.email){return;}
    state.demo=false;state.reportId=newId();state.index=0;
    state.answers=Array(35).fill(undefined);
    renderQuestion();show('questionnaire');
  }

  function showDemo(){
    state.company='TRANSPORTADORA EXEMPLO LTDA. (DADOS FICTÍCIOS)';
    state.email='demonstracao@example.invalid';
    state.responsible='Equipe de demonstração';
    state.demo=true;
    state.reportId='RX-DEMONSTRACAO';
    state.answers=Array.from({length:35},(_,i)=>i%9===0?1:i%7===0?2:i%5===0?4:3);
    renderReport();show('reportScreen');
  }

  function priorities(){
    return qs.map((q,i)=>({q,i,value:state.answers[i]}))
      .filter(x=>isValid(x.value)&&x.value<4)
      .sort((a,b)=>a.value-b.value||a.i-b.i).slice(0,3);
  }

  function radar(departments){
    const names=['Tesouro','Estratégia','Frota','Operações','Comércio'];
    const center=153,rad=104;
    const point=(index,percentage)=>{
      const a=(index*72-90)*Math.PI/180, rr=rad*(percentage/100);
      return [center+rr*Math.cos(a),center+rr*Math.sin(a)];
    };
    const pts=values=>values.map((v,i)=>point(i,v).map(n=>n.toFixed(1)).join(',')).join(' ');
    let svg='<svg xmlns="http://www.w3.org/2000/svg" class="analysis-svg" viewBox="0 0 340 328" role="img" aria-label="Gráfico radar com pontuação dos cinco departamentos">';
    for(const p of [20,40,60,80,100]) svg+=`<polygon points="${pts(Array(5).fill(p))}" fill="none" stroke="#365873" stroke-width="1"/>`;
    for(let i=0;i<5;i++){
      const [x,y]=point(i,100);
      svg+=`<line x1="${center}" y1="${center}" x2="${x}" y2="${y}" stroke="#365873"/>`;
    }
    const scores=departments.map(d=>d.score===null?0:d.score);
    svg+=`<polygon points="${pts(scores)}" fill="#53b6d3" fill-opacity=".23" stroke="#67cae8" stroke-width="3"/>`;
    for(let i=0;i<5;i++){
      const [x,y]=point(i,scores[i]);
      svg+=`<circle cx="${x}" cy="${y}" r="4" fill="#ecc075"/>`;
      const [tx,ty]=point(i,125);
      svg+=`<text x="${tx}" y="${ty}" text-anchor="middle" fill="#c9dce9" font-size="10">${names[i]}</text>`;
    }
    svg+='</svg>';
    return svg;
  }

  function renderReport(){
    const r=summarize(),now=new Date().toLocaleDateString('pt-BR');
    const p=priorities();
    $('reportCompany').textContent=state.company;
    $('reportDate').textContent=`Avaliação: ${now}`;
    $('reportIdentification').textContent=state.reportId;
    $('reportFoot').textContent=`${state.company} · ${now} · ${state.reportId}`;
    $('reportStatus').textContent=state.demo?'Demonstração com dados fictícios':'Relatório gerencial individualizado';
    $('demoNotice').textContent=state.demo?
      'DEMONSTRAÇÃO · Todos os resultados e dados desta avaliação são fictícios. Não representam uma transportadora real.':
      'AUTOAVALIAÇÃO · Resultados declarados pelo respondente. Não representam auditoria, certificação ou verificação independente.';
    $('govValue').textContent=fmt(r.governance.score);
    $('govDial').style.background=`conic-gradient(#ecc075 ${r.governance.score??0}%,#38536a 0)`;
    $('govClass').textContent=`${classify(r.governance.score)} · ${r.governance.valid}/10 respostas válidas`;
    $('deptValue').textContent=fmt(r.departmentScore);
    $('deptDial').style.background=`conic-gradient(#58b5d3 ${r.departmentScore??0}%,#38536a 0)`;
    $('deptClass').textContent=`${classify(r.departmentScore)} · ${r.departments.reduce((a,d)=>a+d.valid,0)}/25 respostas válidas`;
    $('quality').innerHTML=`<span>${r.valid}/35 válidas</span><span>${r.unknown} “Não sei informar”</span><span>${r.answered-r.valid-r.unknown} não respondidas</span><span>Regras mínimas: 8/10 e 4/5 por departamento</span>`;
    $('deptBars').innerHTML=r.departments.map(d=>`<div class="dept-row"><label>${esc(d.name)}</label><div class="bar" aria-hidden="true"><div style="width:${d.score??0}%"></div></div><strong>${fmt(d.score)}</strong></div>`).join('');
    $('radar').innerHTML=radar(r.departments);
    $('priorities').innerHTML=p.length ? p.map((x,i)=>`<div class="priority"><strong>${i+1}ª prioridade · ${esc(x.q.dimension)} · ${x.value}/4</strong><p>${esc(x.q.question)}</p><p><b>Ação recomendada:</b> ${esc(x.q.action)}</p></div>`).join(''):
      '<p class="detail-empty">Nenhuma prioridade por baixa pontuação identificada. Validar evidências e manter a melhoria contínua.</p>';
    const plan=p.length ? [
      `Definir responsável e prazo para ${p[0].q.action.toLowerCase()}`,
      p[1]?p[1].q.action:'Revisar controles críticos e evidências existentes.',
      p[2]?p[2].q.action:'Planejar acompanhamento dos controles prioritários.',
      'Registrar ações, prazos e evidências de execução e conferir seus resultados com a liderança.'
    ]:['Revisar a consistência das respostas e selecionar um controle para aprimoramento.','Conferir evidências documentais das práticas declaradas.','Estabelecer uma rotina de revisão das metas e das decisões.'];
    $('actionPlan').innerHTML=plan.map(x=>`<li>${esc(x)}</li>`).join('');
    const available=r.departments.filter(d=>d.score!==null);
    const weakest=[...available].sort((a,b)=>a.score-b.score)[0];
    const strongest=[...available].sort((a,b)=>b.score-a.score)[0];
    const bullet=[
      `Governança empresarial: <strong>${fmt(r.governance.score)}</strong> — ${classify(r.governance.score).toLowerCase()}.`,
      `Maturidade departamental: <strong>${fmt(r.departmentScore)}</strong> — ${classify(r.departmentScore).toLowerCase()}.`,
      weakest?`Principal oportunidade departamental: <strong>${esc(weakest.name)}</strong> (${fmt(weakest.score)}).`:'A maturidade departamental requer mais respostas válidas para análise.',
      strongest?`Área com maior pontuação declarada: <strong>${esc(strongest.name)}</strong> (${fmt(strongest.score)}).`:'Ainda não há dados suficientes para comparar os departamentos.',
      'Priorize evidências reais antes de decidir sobre investimentos, conformidade e certificações.'
    ];
    $('conclusions').innerHTML=`<ul class="points">${bullet.map(x=>`<li>${x}</li>`).join('')}</ul>`;
    $('answerList').innerHTML=qs.map((q,i)=>{
      const v=state.answers[i],known=isValid(v);
      const response=known?q.options[v]:v===null?'Não sei informar':'Sem resposta';
      return `<div class="answer-card"><strong>${String(i+1).padStart(2,'0')}</strong><div><b>${esc(q.question)}</b><p>${esc(q.dimension)} · ${esc(response)}</p></div><span class="answer-score">${known?v+'/4':'Sem nota'}</span></div>`;
    }).join('');
  }

  $('startForm').addEventListener('submit', begin);
  $('demoLanding').addEventListener('click',showDemo);
  $('qBack').addEventListener('click',()=>{if(state.index===0){show('landing');return;}state.index--;renderQuestion();viewport();});
  $('qNext').addEventListener('click',()=>{
    if(!isAnswered(state.answers[state.index]))return;
    if(state.index===34){renderReport();show('reportScreen');return;}
    state.index++;renderQuestion();viewport();
  });
  $('printReport').addEventListener('click',()=>window.print());
  $('restart').addEventListener('click',()=>{
    state.answers=Array(35).fill(undefined);state.demo=false;
    $('startForm').reset();show('landing');
  });
  if(qs.length!==35||dimensions.length!==6||qs.some(q=>q.options.length!==5)){
    throw new Error('Catálogo inválido: esperado 35 perguntas, seis dimensões e cinco alternativas por pergunta.');
  }
  // Somente prévia local: sem localStorage, cookies, API ou envio de e-mail.
})();