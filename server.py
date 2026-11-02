from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from io import BytesIO
from pathlib import Path
import json, math, os, time, threading
from collections import defaultdict, deque
from urllib.parse import urlsplit
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
  self.send_header('Referrer-Policy','no-referrer')
  self.send_header('X-Frame-Options','DENY')
  self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
  super().end_headers()
 def do_GET(self):
  path=urlsplit(self.path).path
  if path=='/health':
   body=b'OK';self.send_response(200);self.send_header('Content-Type','text/plain; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body);return
  if path not in ('/','/index.html'):
   self.send_error(404);return
  self.path='/index.html';super().do_GET()

 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def do_POST(self):
  if urlsplit(self.path).path!='/api/relatorio':self.send_error(404);return
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
 ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()
