from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from io import BytesIO
from pathlib import Path
import json, math, os, time, threading, sqlite3, secrets, hmac, hashlib, base64, urllib.request, urllib.error, ssl
from datetime import datetime, timezone
from collections import defaultdict, deque
from urllib.parse import urlsplit
from contextlib import contextmanager
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit

ROOT=Path(__file__).resolve().parent
NAVY=HexColor('#0A203B'); BLUE=HexColor('#147EB4'); PALE=HexColor('#EAF3F9'); DARK=HexColor('#24374B'); MUTED=HexColor('#637B91')
W,H=595.28,841.89
PILLARS=[('custos','Gestão de custos',25),('preco','Formação do preço',25),('margem','Margem e rentabilidade',20),('operacao','Produtividade operacional',15),('compliance','Compliance e riscos COMEX',10),('comercial','Governança comercial',5)]
RECS={
'custos':('Ficha de custos por veículo','Levantar custos fixos, variáveis, depreciação e critérios de rateio.','Fichas de custos preenchidas e revisadas.'),
'preco':('Simulador de precificação','Padronizar memória de cálculo, tributos, custos adicionais e margem-alvo.','Cinco cotações recalculadas.'),
'margem':('Painel de margem por frete','Comparar margem projetada e realizada por CT-e, cliente e rota.','Primeiro comparativo previsto x realizado.'),
'operacao':('Controle de produtividade','Medir quilômetros vazios, horas de espera e disponibilidade da frota.','Indicadores operacionais apurados.'),
'compliance':('Checklist regulatório','Verificar enquadramento ANTT, VPO, CIOT, riscos e condições contratuais.','Checklist aplicado a operações recentes.'),
'comercial':('Política comercial','Definir alçadas para descontos, exceções e revisões de propostas.','Política de aprovação documentada.')}
ALERTS={'P2Q1':'Custo não é calculado regularmente antes da cotação.','P2Q4':'Preço de equilíbrio e margem-alvo sem controle consistente.','P3Q1':'Margem projetada não é calculada regularmente.','P5Q1':'Verificação regulatória requer atenção prioritária.'}

def para(c,text,x,y,width=480,size=10,leading=15,color=DARK,maxlines=30):
 c.setFillColor(color);c.setFont('Helvetica',size)
 lines=simpleSplit(str(text), 'Helvetica', size,width)[:maxlines]
 for line in lines: c.drawString(x,y,line);y-=leading
 return y

def box(c,x,y,w,h,color=PALE):c.setFillColor(color);c.roundRect(x,y,w,h,9,stroke=0,fill=1)

def page(c,n,tag,title,subtitle,company):
 c.setFillColor(NAVY);c.rect(0,H-83,W,83,fill=1,stroke=0)
 c.setFillColor(HexColor('#9DD8FA'));c.setFont('Helvetica-Bold',12);c.drawString(42,H-39,'FRETE COMEX PRO')
 c.setFillColor(HexColor('#C7D8E6'));c.setFont('Helvetica',8);c.drawRightString(W-42,H-38,'RAIO-X DA PRECIFICAÇÃO')
 c.setFillColor(BLUE);c.setFont('Helvetica-Bold',9);c.drawString(42,H-117,tag)
 c.setFillColor(NAVY);c.setFont('Helvetica-Bold',22);c.drawString(42,H-147,title)
 para(c,subtitle,42,H-170,510,10,14,MUTED)
 c.setStrokeColor(HexColor('#DDE5EB'));c.line(42,50,W-42,50)
 c.setFillColor(MUTED);c.setFont('Helvetica',8);c.drawString(42,35,'Relatório individual • '+company[:65]);c.drawRightString(W-42,35,f'{n} / 8')

def section(c,heading,body,y):
 c.setFillColor(NAVY);c.setFont('Helvetica-Bold',12);c.drawString(52,y,heading)
 return para(c,body,52,y-21,490,10,15,DARK)-18

def validate(data):
 if not isinstance(data,dict) or not isinstance(data.get('sections'),list) or len(data['sections'])!=6:raise ValueError('Estrutura inválida: seis pilares são obrigatórios.')
 sections=[]
 for i,(key,name,weight) in enumerate(PILLARS):
  s=data['sections'][i]
  if s.get('key')!=key or not isinstance(s.get('responses'),list) or len(s['responses'])!=4:raise ValueError('Pilar ou respostas inconsistentes.')
  vals=[]
  for j,r in enumerate(s['responses']):
   v=r.get('score')
   if type(v)!=int or v<0 or v>4 or r.get('id')!=f'P{i+1}Q{j+1}':raise ValueError('Respostas inválidas.')
   vals.append(v)
  sections.append({'key':key,'name':name,'weight':weight,'values':vals,'pct':sum(vals)/16*100,'points':sum(vals)/16*weight})
 score=sum(s['points'] for s in sections)
 label='Crítico' if score<25 else 'Inicial' if score<50 else 'Em desenvolvimento' if score<70 else 'Estruturado' if score<85 else 'Avançado'
 company=data.get('company') or {}
 if not isinstance(company,dict):company={}
 return sections,score,label,str(company.get('name') or 'Transportadora não identificada')[:90],str(company.get('responsible') or 'Não informado')[:90]

def make_pdf(data):
 sections,score,label,company,responsible=validate(data)
 ordered=sorted(sections,key=lambda s:(s['pct'],-s['weight']))
 alerts=[text for i,s in enumerate(sections) for j,v in enumerate(s['values']) if (text:=ALERTS.get(f'P{i+1}Q{j+1}')) and v<=1]
 stream=BytesIO();c=canvas.Canvas(stream,pagesize=(W,H));c.setTitle('Frete COMEX PRO - Raio-X da Precificação')
 # 1
 c.setFillColor(NAVY);c.rect(0,0,W,H,fill=1,stroke=0)
 c.setFillColor(BLUE);c.rect(0,0,18,H,fill=1,stroke=0)
 c.setFillColor(HexColor('#A8DDFB'));c.setFont('Helvetica-Bold',16);c.drawString(54,750,'FRETE COMEX PRO')
 c.setFillColor(HexColor('#FFFFFF'));c.setFont('Helvetica-Bold',34);c.drawString(54,605,'RAIO-X DA');c.drawString(54,561,'PRECIFICAÇÃO')
 para(c,'Diagnóstico de maturidade em precificação e rentabilidade no transporte rodoviário de cargas do comércio exterior.',54,520,480,14,21,HexColor('#C3D8EA'))
 box(c,54,285,486,135,HexColor('#163957'))
 para(c,'RELATÓRIO PERSONALIZADO',75,390,420,10,16,HexColor('#A8DDFB'))
 para(c,company,75,361,420,17,22,HexColor('#FFFFFF'))
 para(c,'Responsável: '+responsible,75,318,420,10,15,HexColor('#D1E4F1'))
 para(c,'Metodologia v1.0 • Exemplo de uso: autoavaliação gerencial',54,110,490,9,14,HexColor('#B7CADD'))
 c.showPage()
 # 2
 page(c,2,'01 / RESULTADO','Diagnóstico executivo','Visão consolidada do índice de maturidade.',company)
 box(c,42,450,511,175)
 c.setFillColor(BLUE);c.setFont('Helvetica-Bold',46);c.drawString(63,548,f'{score:.1f}'.replace('.',','))
 c.setFillColor(MUTED);c.setFont('Helvetica',16);c.drawString(198,551,'/ 100')
 c.setFillColor(NAVY);c.setFont('Helvetica-Bold',18);c.drawString(63,507,label)
 para(c,'Índice de maturidade dos processos, não indicador de lucro financeiro.',63,481,465,10,14,MUTED)
 y=415
 for i,s in enumerate(ordered[:3],1):y=section(c,f'{i:02d}  {s["name"]}',RECS[s['key']][1],y)
 c.showPage()
 # 3
 page(c,3,'02 / DESEMPENHO','Os seis pilares','Maturidade percentual e contribuição de cada dimensão.',company)
 y=600
 for s in sections:
  c.setFillColor(NAVY);c.setFont('Helvetica-Bold',11);c.drawString(50,y,s['name'])
  c.setFillColor(MUTED);c.setFont('Helvetica',10);c.drawRightString(544,y,f'{s["pct"]:.1f}%'.replace('.',','))
  box(c,50,y-29,490,15,HexColor('#E3EDF3'));box(c,50,y-29,490*s['pct']/100,15,BLUE)
  para(c,f'Peso {s["weight"]}%  •  Pontos ponderados: {s["points"]:.2f} / {s["weight"]}',50,y-47,485,9,13,MUTED)
  y-=78
 c.showPage()
 # 4
 page(c,4,'03 / ANÁLISE','Fragilidades e alertas','Pontos de atenção baseados nas respostas registradas.',company)
 y=603
 for i,s in enumerate(ordered[:3],1):
  box(c,43,y-101,509,112)
  c.setFillColor(NAVY);c.setFont('Helvetica-Bold',12);c.drawString(57,y-13,f'{i}. {s["name"]} — {s["pct"]:.1f}%')
  para(c,RECS[s['key']][1],57,y-38,475,10,15,DARK)
  y-=133
 c.setFillColor(NAVY);c.setFont('Helvetica-Bold',12);c.drawString(49,y-4,'Alertas críticos')
 y-=29
 for a in (alerts or ['Nenhum alerta crítico nas quatro questões monitoradas. Isso não comprova ausência de riscos.'])[:5]:y=para(c,'• '+a,51,y,490,10,16,DARK)-8
 c.showPage()
 # 5
 page(c,5,'04 / IMPLEMENTAÇÃO','Plano de ação de 30 dias','Prioridades gerenciais e evidências sugeridas.',company)
 y=602
 for i,s in enumerate(ordered[:3]):
  box(c,43,y-127,509,137)
  c.setFillColor(BLUE);c.setFont('Helvetica-Bold',11);c.drawString(57,y-12,['DIAS 1–7','DIAS 8–17','DIAS 18–30'][i])
  c.setFillColor(NAVY);c.setFont('Helvetica-Bold',13);c.drawString(57,y-34,s['name'])
  yy=para(c,RECS[s['key']][1],57,y-56,472,10,15,DARK)
  para(c,'Evidência: '+RECS[s['key']][2],57,yy-7,472,9,14,MUTED)
  y-=158
 c.showPage()
 # 6
 page(c,6,'05 / CONTROLE','Indicadores de gestão','Métricas sugeridas para acompanhamento operacional e financeiro.',company)
 metrics=[('Custo operacional por km','Custos operacionais elegíveis divididos pelos quilômetros totais.'),('Margem de contribuição por frete','Receita líquida aplicável menos custos e despesas variáveis atribuíveis.'),('Desvio previsto x realizado','Diferença entre custo orçado e custo realizado por viagem.'),('Percentual de retorno vazio','Quilômetros vazios divididos pelos quilômetros totais.'),('Tempo de espera','Horas de imobilização em terminais e clientes.'),('Resultado por cliente e rota','Margem consolidada por cliente, corredor e modalidade.')]
 y=608
 for title,desc in metrics:y=section(c,title,desc,y)
 para(c,'Este relatório não estima valores financeiros sem dados suficientes.',50,135,490,10,14,MUTED)
 c.showPage()
 # 7
 page(c,7,'06 / APLICAÇÃO','Ferramentas recomendadas','Recursos do ecossistema Frete COMEX PRO alinhados às prioridades.',company)
 y=610
 for i,s in enumerate(ordered[:3],1):
  box(c,43,y-125,509,136)
  c.setFillColor(BLUE);c.setFont('Helvetica-Bold',11);c.drawString(57,y-13,f'FERRAMENTA {i:02d}')
  c.setFillColor(NAVY);c.setFont('Helvetica-Bold',14);c.drawString(57,y-39,RECS[s['key']][0])
  para(c,RECS[s['key']][1],57,y-64,469,10,15,DARK)
  y-=160
 c.showPage()
 # 8
 page(c,8,'07 / TRANSPARÊNCIA','Metodologia e limites','Critérios, pesos e ressalvas de interpretação.',company)
 y=610
 for s in sections:
  c.setFillColor(DARK);c.setFont('Helvetica',10);c.drawString(52,y,s['name']);c.drawRightString(535,y,f'{s["weight"]}%');y-=27
 y-=19
 y=section(c,'Cálculo','Cada resposta recebe de 0 a 4 pontos. Em cada pilar, a soma das quatro respostas é dividida por 16 e multiplicada pelo peso. A nota global é a soma dos seis resultados ponderados.',y)
 y=section(c,'Classificações','Crítico: 0 a 24,9; Inicial: 25 a 49,9; Em desenvolvimento: 50 a 69,9; Estruturado: 70 a 84,9; Avançado: 85 a 100.',y)
 y=section(c,'Limitações','Autoavaliação gerencial. Os pesos e níveis são metodologia proposta, ainda não validada estatisticamente. Não é auditoria, certificação, apuração de lucro ou verificação de conformidade legal.',y)
 para(c,'Referências de consulta regulatória: www.gov.br/antt e www.gov.br/anpd',52,max(y,95),490,9,14,MUTED)
 c.showPage();c.save();return stream.getvalue()


# Dados persistentes: configure DATABASE_URL (PostgreSQL) no Render.
# SQLite é somente para desenvolvimento local; o disco do Render gratuito é efêmero.
DATABASE_URL=os.environ.get('DATABASE_URL','').strip()
DB_PATH=os.environ.get('SQLITE_PATH',str(ROOT/'local_diagnostics.sqlite3'))
ADMIN_PASSWORD=os.environ.get('ADMIN_PASSWORD','')
ADMIN_USER=os.environ.get('ADMIN_USER','admin')
RESEND_API_KEY=os.environ.get('RESEND_API_KEY','')
EMAIL_FROM=os.environ.get('EMAIL_FROM','')
PUBLIC_URL=os.environ.get('PUBLIC_URL','').rstrip('/')
RETENTION_DAYS=int(os.environ.get('RETENTION_DAYS','180'))
DB_READY=False

@contextmanager
def db():
 if DATABASE_URL:
  import psycopg
  with psycopg.connect(DATABASE_URL,connect_timeout=8) as con:
   yield con
 else:
  con=sqlite3.connect(DB_PATH,timeout=8)
  try:yield con;con.commit()
  finally:con.close()

def sql(con,query,args=()):
 if DATABASE_URL:query=query.replace('?','%s')
 return con.execute(query,args)

def initialize_db():
 global DB_READY
 with db() as con:
  sql(con,"""CREATE TABLE IF NOT EXISTS diagnostics (
    id TEXT PRIMARY KEY, created_at TEXT NOT NULL, company TEXT NOT NULL,
    responsible TEXT NOT NULL, email TEXT NOT NULL, fleet TEXT NOT NULL,
    operation TEXT NOT NULL, score REAL NOT NULL, classification TEXT NOT NULL,
    marketing INTEGER NOT NULL, email_status TEXT NOT NULL, payload TEXT NOT NULL)""")
 DB_READY=True

def store_diagnostic(payload, email, marketing):
 sections,score,label,company,responsible=validate(payload)
 identifier=secrets.token_urlsafe(18)
 created=datetime.now(timezone.utc).isoformat()
 with db() as con:
  sql(con,"""INSERT INTO diagnostics (id,created_at,company,responsible,email,fleet,operation,score,classification,marketing,email_status,payload)
   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (identifier,created,company,responsible,email,str(payload.get('company',{}).get('fleet',''))[:80],str(payload.get('company',{}).get('operation',''))[:80],score,label,int(marketing),'pending' if email else 'not_requested',json.dumps(payload,ensure_ascii=False)))
 return identifier

def email_pdf(email, pdf):
 if not RESEND_API_KEY or not EMAIL_FROM:return 'not_configured'
 data=json.dumps({'from':EMAIL_FROM,'to':[email],'subject':'Seu Raio-X da Precificação | Frete COMEX PRO',
  'html':'<p>Seu diagnóstico gratuito Frete COMEX PRO está pronto.</p><p>O relatório personalizado segue em anexo.</p><p>Esta mensagem é operacional, referente ao diagnóstico solicitado.</p>',
  'attachments':[{'filename':'Raio-X-Frete-COMEX-PRO.pdf','content':base64.b64encode(pdf).decode('ascii')}] }).encode()
 request=urllib.request.Request('https://api.resend.com/emails',data=data,headers={'Authorization':'Bearer '+RESEND_API_KEY,'Content-Type':'application/json'},method='POST')
 try:
  with urllib.request.urlopen(request,timeout=15) as resp:return 'sent' if resp.status in (200,201,202) else 'failed'
 except (urllib.error.URLError,TimeoutError):return 'failed'

def cleanup():
 cutoff=datetime.fromtimestamp(time.time()-RETENTION_DAYS*86400,timezone.utc).isoformat()
 with db() as con:sql(con,'DELETE FROM diagnostics WHERE created_at < ?', (cutoff,))

def admin_auth(handler):
 if not ADMIN_PASSWORD:return False
 value=handler.headers.get('Authorization','')
 if not value.startswith('Basic '):return False
 try:
  userpass=base64.b64decode(value[6:],validate=True).decode('utf-8')
  user,passwd=userpass.split(':',1)
  return hmac.compare_digest(user,ADMIN_USER) and hmac.compare_digest(passwd,ADMIN_PASSWORD)
 except (ValueError,UnicodeDecodeError):return False

def dashboard():
 with db() as con:
  rows=sql(con,'SELECT score,classification,created_at,marketing FROM diagnostics ORDER BY created_at DESC').fetchall()
  counts=sql(con,'SELECT classification,COUNT(*) FROM diagnostics GROUP BY classification').fetchall()
  pillar_totals=[0.0]*6
  for (raw,) in sql(con,'SELECT payload FROM diagnostics').fetchall():
   try:
    sections,_,_,_,_=validate(json.loads(raw))
    for i,sec in enumerate(sections):pillar_totals[i]+=sec['pct']
   except (ValueError,TypeError,KeyError):continue
 n=len(rows)
 return {'total':n,'average':round(sum(r[0] for r in rows)/n,1) if n else 0,
  'classification':dict(counts),'marketing_opt_in':sum(r[3] for r in rows),
  'pillars':[{'name':p[1],'average':round(pillar_totals[i]/n,1) if n else 0} for i,p in enumerate(PILLARS)],
  'recent':[{'date':r[2][:10],'score':round(r[0],1),'classification':r[1]} for r in rows[:15]]}

def json_reply(handler,code,obj):
 body=json.dumps(obj,ensure_ascii=False).encode('utf-8')
 handler.send_response(code);handler.send_header('Content-Type','application/json; charset=utf-8');handler.send_header('Content-Length',str(len(body)));handler.send_header('Cache-Control','no-store');handler.end_headers();handler.wfile.write(body)

def read_json(handler):
 if handler.headers.get('Content-Type','').split(';')[0].strip()!='application/json':raise ValueError('Envie application/json')
 length=int(handler.headers.get('Content-Length','0'))
 if length<1 or length>100000:raise ValueError('Tamanho de requisição inválido')
 return json.loads(handler.rfile.read(length))

# Limitação básica por instância (não substitui proteção de borda/WAF).
RATE_LOCK=threading.Lock()
RATE=defaultdict(deque)
MAX_REQUESTS=int(os.environ.get('MAX_PDF_PER_HOUR','15'))

def permitted(ip):
 now=time.monotonic()
 with RATE_LOCK:
  entries=RATE[ip]
  while entries and entries[0]<now-3600:entries.popleft()
  if len(entries)>=MAX_REQUESTS:return False
  entries.append(now)
  if len(RATE)>10000:
   for k in list(RATE)[:1000]:
    if not RATE[k] or RATE[k][-1]<now-3600:RATE.pop(k,None)
  return True

class Handler(SimpleHTTPRequestHandler):
 def log_message(self,format,*args):
  # Não registrar nomes, payloads ou endereços IP de participantes.
  print('%s %s' % (self.command, self.path.split('?')[0]),flush=True)
 def end_headers(self):
  self.send_header('X-Content-Type-Options','nosniff')
  self.send_header('Strict-Transport-Security','max-age=31536000; includeSubDomains')
  self.send_header('Referrer-Policy','no-referrer')
  self.send_header('X-Frame-Options','DENY')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
  super().end_headers()
 def do_GET(self):
  path=urlsplit(self.path).path
  if path in ('/v59-preview','/v59-preview/','/v59-preview/index.html','/v59-preview/privacidade.html','/v59-preview/termos.html'):
   if os.environ.get('ENABLE_V59_PREVIEW','0')!='1':
    self.send_error(404);return
   target='index.html' if path in ('/v59-preview','/v59-preview/') else path.rsplit('/',1)[-1]
   candidate=ROOT/'v59_preview'/target
   if not candidate.is_file():
    self.send_error(404,'Prévia visual ainda não instalada');return
   data=candidate.read_bytes()
   self.send_response(200)
   self.send_header('Content-Type','text/html; charset=utf-8')
   self.send_header('Content-Length',str(len(data)))
   self.send_header('Cache-Control','no-store')
   self.send_header('X-Robots-Tag','noindex, nofollow, noarchive')
   self.end_headers()
   self.wfile.write(data)
   return
  if path=='/admin':
   if not admin_auth(self):
    self.send_response(401);self.send_header('WWW-Authenticate','Basic realm=Frete COMEX PRO Admin');self.end_headers();return
   self.path='/admin.html';super().do_GET();return
  if path=='/api/admin/stats':
   if not admin_auth(self):json_reply(self,401,{'error':'Acesso negado'});return
   try:json_reply(self,200,dashboard())
   except Exception:json_reply(self,503,{'error':'Banco indisponível'})
   return
  if path=='/api/v59/capabilities':
   if os.environ.get('ENABLE_V59_PREVIEW')!='1':
    self.send_error(404);return
   storage=os.environ.get('ENABLE_V59_STORAGE')=='1' and bool(DATABASE_URL)
   email=storage and os.environ.get('ENABLE_V59_EMAIL')=='1' and bool(RESEND_API_KEY) and bool(EMAIL_FROM)
   json_reply(self,200,{'preview':True,'storage':storage,'email':email})
   return
  if path=='/health':
   body=b'OK';self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body);return
  if path not in ('/','/index.html'):
   self.send_error(404);return
  self.path='/index.html';super().do_GET()

 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_POST(self):
  route=urlsplit(self.path).path
  if route=='/api/v59/diagnosticos':
   # Rota de persistência isolada, bloqueada até migração e homologação.
   if os.environ.get('ENABLE_V59_PREVIEW')!='1' or os.environ.get('ENABLE_V59_STORAGE')!='1' or not DATABASE_URL:
    self.send_error(404);return
   if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
    self.send_error(415,'Content-Type deve ser application/json');return
   if not permitted(self.client_address[0]):
    json_reply(self,429,{'error':'Limite de solicitações atingido'});return
   try:
    from v59_api import validate_submission
    from v59_storage import save_v59
    request=read_json(self)
    validated=validate_submission(request)
    with db() as connection:
     identifier=save_v59(connection,request)
    status='not_requested'
    if os.environ.get('ENABLE_V59_EMAIL')=='1':
     try:
      from v59_email import send_v59_pdf
      from v59_report import make_v59_full_report
      pdf=make_v59_full_report(validated)
      status=send_v59_pdf(validated['company']['email'],pdf,identifier)
     except Exception:
      status='failed'
     try:
      with db() as con:
       sql(con,'UPDATE raiox_v59.diagnostics SET email_status=? WHERE id=?',(status,identifier))
     except Exception:
      # Registro original já foi confirmado; não repetir envio.
      pass
    json_reply(self,201,{'id':identifier,'result':validated['result'],'stored':True,'emailSent':status=='accepted','emailStatus':status})
   except (ValueError,TypeError,KeyError,UnicodeDecodeError,json.JSONDecodeError) as exc:
    json_reply(self,400,{'error':str(exc)[:160]})
   except Exception:
    json_reply(self,503,{'error':'Não foi possível registrar o diagnóstico.'})
   return
  if route in ('/api/v59/preview','/api/v59/relatorio'):
   if os.environ.get('ENABLE_V59_PREVIEW','0')!='1':
    self.send_error(404);return
   if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':
    self.send_error(415,'Content-Type deve ser application/json');return
   if not permitted(self.client_address[0]):
    json_reply(self,429,{'error':'Limite de solicitações atingido'});return
   try:
    from v59_api import validate_submission
    from v59_report import make_v59_full_report
    request=read_json(self)
    validated=validate_submission(request)
    if route=='/api/v59/preview':
     json_reply(self,200,{'result':validated['result'],'status':'preview_only','stored':False,'emailSent':False})
    else:
     pdf=make_v59_full_report(validated)
     self.send_response(200)
     self.send_header('Content-Type','application/pdf')
     self.send_header('Content-Disposition','attachment; filename="raio-x-transportador-v59-relatorio-executivo.pdf"')
     self.send_header('Content-Length',str(len(pdf)))
     self.send_header('Cache-Control','no-store')
     self.end_headers()
     self.wfile.write(pdf)
   except (ValueError,TypeError,KeyError,UnicodeDecodeError,json.JSONDecodeError) as exc:
    json_reply(self,400,{'error':str(exc)[:160]})
   except Exception:
    json_reply(self,503,{'error':'Serviço de prévia temporariamente indisponível'})
   return
  if route not in ('/api/relatorio','/api/diagnosticos'):self.send_error(404);return
  if route=='/api/diagnosticos':
   if not permitted(self.client_address[0]):json_reply(self,429,{'error':'Limite de solicitações atingido'});return
   try:
    request=read_json(self);payload=request.get('diagnostic');email=str(request.get('email') or '').strip().lower()
    if not isinstance(payload,dict):raise ValueError('Diagnóstico inválido')
    if email and (len(email)>254 or '@' not in email or '.' not in email.split('@')[-1] or any(c.isspace() for c in email)):raise ValueError('E-mail inválido')
    if request.get('privacyAccepted') is not True:raise ValueError('Confirme ciência do aviso de privacidade')
    marketing=request.get('marketingOptIn') is True
    validate(payload)
    pdf=make_pdf(payload)
    identifier=store_diagnostic(payload,email,marketing)
    status=email_pdf(email,pdf) if email else 'not_requested'
    with db() as con:sql(con,'UPDATE diagnostics SET email_status=? WHERE id=?',(status,identifier))
    json_reply(self,201,{'id':identifier,'score':round(validate(payload)[1],2),'emailStatus':status,'pdfAvailable':True})
   except (ValueError,KeyError,TypeError) as exc:json_reply(self,400,{'error':str(exc)[:150]})
   except Exception:json_reply(self,503,{'error':'Não foi possível registrar o diagnóstico; tente novamente.'})
   return
  if self.headers.get('Content-Type','').split(';')[0].strip()!='application/json':self.send_error(415,'Content-Type deve ser application/json');return
  if not permitted(self.client_address[0]):self.send_error(429,'Limite de relatórios atingido; tente mais tarde');return
  try:
   length=int(self.headers.get('Content-Length','0'))
   if length<1 or length>100000:self.send_error(413,'Tamanho inválido');return
   data=json.loads(self.rfile.read(length));pdf=make_pdf(data)
   self.send_response(200);self.send_header('Content-Type','application/pdf');self.send_header('Content-Disposition','attachment; filename="frete-comex-pro-raio-x.pdf"');self.send_header('Content-Length',str(len(pdf)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(pdf)
  except (ValueError,KeyError,TypeError,UnicodeDecodeError) as e:self.send_error(400,'Dados inválidos para o relatório')

if __name__=='__main__':
 port=int(os.environ.get('PORT','8000'))
 print(f'Frete COMEX PRO: http://localhost:{port}',flush=True)
 initialize_db()
 ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
