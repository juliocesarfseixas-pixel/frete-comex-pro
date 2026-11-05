/* Raio-X V5.9: adaptador opcional para gerar PDF preliminar via backend.
   Somente envia dados após clique. Não armazena nem envia e-mail. */
(function(){
  'use strict';
  const btn=document.getElementById('pdfServer');
  const status=document.getElementById('pdfServerStatus');
  if(!btn||!status)return;
  btn.addEventListener('click',async function(){
    if(typeof fictitious!=='undefined'&&fictitious){
      status.textContent='Modo demonstração: PDF do servidor desativado.';return;
    }
    const company=document.getElementById('company').value.trim();
    const emailElement=document.getElementById('email');
    const email=emailElement.value.trim();
    if(!company||!emailElement.checkValidity()){
      status.textContent='Nome e e-mail válidos são obrigatórios.';return;
    }
    if(typeof answers==='undefined'||!Array.isArray(answers)||answers.length!==35){
      status.textContent='Respostas indisponíveis.';return;
    }
    const responses=answers.map(x=>Number.isInteger(x)&&x>=0&&x<=4?x:null);
    const payload={company:{
      name:company,email:email,
      responsible:document.getElementById('owner').value.trim()
    },responses};
    btn.disabled=true;status.textContent='Gerando PDF preliminar…';
    try{
      const response=await fetch('/api/v59/relatorio',{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify(payload),credentials:'same-origin'
      });
      if(!response.ok){
        let message='Erro HTTP '+response.status;
        try{const data=await response.json();message=data.error||message;}catch(e){}
        throw new Error(message);
      }
      const pdf=await response.blob();
      if(pdf.type!=='application/pdf')throw new Error('Resposta inesperada.');
      const url=URL.createObjectURL(pdf);
      const a=document.createElement('a');
      a.href=url;a.download='raio-x-v59-preliminar.pdf';
      document.body.appendChild(a);a.click();a.remove();
      setTimeout(()=>URL.revokeObjectURL(url),10000);
      status.textContent='PDF preliminar gerado; nenhum dado foi armazenado ou enviado por e-mail.';
    }catch(e){
      status.textContent='Erro ao gerar PDF: '+e.message+
        '. Utilize a opção de salvar PDF executivo pelo navegador.';
    }finally{btn.disabled=false;}
  });
})();
