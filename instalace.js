/* Instalace do telefonu – univerzální pomocník (VHOS aplikace: Konference, Florián, Aquakontrol…)
   Vložení:  <script src="instalace.js" data-nazev="Pořadatel" data-barva="#2f6b3c" defer></script>
   Volitelně: data-qr="obrazky/qr.png" (QR pro počítač), data-pozdeji="1" (lišta se ukáže až po 20 s),
   data-lista="0" (žádná lišta – jen návod přes window.instalaceNavod(), např. z vlastního tlačítka v menu).
   Co dělá: když aplikace NENÍ nainstalovaná, ukáže dole malou lištu „📲 Přidat na plochu“.
   - Android/Chrome: tlačítko Nainstalovat (jedno klepnutí, beforeinstallprompt), jinak návod ⋮ → Nainstalovat.
   - iPhone/iPad: návod Safari → Sdílet → Přidat na plochu → Přidat; ve vnitřním prohlížeči (Gmail, Messenger,
     Facebook…) nebo v Chromu na iOS upozorní „jen ze Safari“ a nabídne Zkopírovat odkaz.
   - Počítač: QR kód (pokud je data-qr), jinak nic.
   Lišta jde zavřít (pamatuje si to 14 dní). Funkce window.instalaceNavod() otevře návod odkudkoli (třeba z menu). */
(function(){
  var sc=document.currentScript||{dataset:{}}, D=sc.dataset||{}, NAZEV=D.nazev||document.title, BARVA=D.barva||"#2f6b3c", QR=D.qr||"";
  var BEZLISTY=D.lista==="0";
  var UA=navigator.userAgent, ios=/iPad|iPhone|iPod/.test(UA)||(navigator.platform==="MacIntel"&&navigator.maxTouchPoints>1), android=/Android/i.test(UA);
  var inapp=/FBAN|FBAV|FB_IAB|Instagram|Messenger|WhatsApp|GSA\/|LinkedInApp|Line\/|Twitter|MicroMessenger|Snapchat|SznProhlizec/i.test(UA), jinyIos=/CriOS|FxiOS|EdgiOS|OPiOS/.test(UA);
  function nainst(){try{return matchMedia("(display-mode: standalone)").matches||navigator.standalone===true}catch(e){return false}}
  var VYZVA=null, KLIC="instalace_pryc_"+location.pathname;
  function pryc(){try{var t=+localStorage.getItem(KLIC)||0;return Date.now()-t<14*864e5}catch(e){return false}}
  window.addEventListener("beforeinstallprompt",function(e){e.preventDefault();VYZVA=e;lista();});
  window.addEventListener("appinstalled",function(){VYZVA=null;var l=document.getElementById("inst-lista");if(l)l.remove();});
  var css=".inst-l{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:9998;display:flex;align-items:center;gap:10px;background:#fff;color:#222;border-radius:14px;box-shadow:0 10px 30px rgba(0,0,0,.25);padding:10px 12px;font:14px/1.3 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-width:520px;margin:0 auto}"+
    ".inst-l b{display:block}.inst-l small{color:#666}.inst-l .i{font-size:24px}.inst-l .t{flex:1;min-width:0}.inst-b{border:0;border-radius:10px;padding:9px 12px;font:700 14px system-ui,sans-serif;color:#fff;background:"+BARVA+";white-space:nowrap}.inst-x{border:0;background:none;font-size:22px;color:#888;padding:0 4px}"+
    ".inst-m{position:fixed;inset:0;z-index:9999;background:rgba(0,0,0,.45);display:flex;align-items:flex-end;justify-content:center}.inst-k{background:#fff;color:#222;width:100%;max-width:520px;border-radius:18px 18px 0 0;padding:18px 16px calc(18px + env(safe-area-inset-bottom));font:15px/1.4 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;max-height:90vh;overflow:auto}"+
    ".inst-k h3{margin:0 0 4px;font-size:19px}.inst-k .s{color:#666;font-size:13px;margin:0 0 12px}.inst-k ol{list-style:none;padding:0;margin:0 0 10px}.inst-k li{display:flex;align-items:center;gap:12px;background:#f4f4f2;border-radius:12px;padding:12px;margin-bottom:8px}"+
    ".inst-k .n{flex:none;width:28px;height:28px;border-radius:99px;background:"+BARVA+";color:#fff;display:grid;place-items:center;font-weight:800}.inst-k .tx{flex:1}.inst-k .ik{flex:none;width:36px;height:36px;border-radius:10px;background:#fff;display:grid;place-items:center}"+
    ".inst-k .w{border:2px dashed #e08a2e;border-radius:12px;padding:10px;margin:0 0 10px;background:#fff8ef}.inst-k .p{color:#666;font-size:13px;margin:6px 0 0}.inst-k img{display:block;margin:8px auto;width:220px;max-width:70%;border-radius:10px;border:1px solid #ddd}"+
    "@media (prefers-color-scheme:dark){.inst-l,.inst-k{background:#232228;color:#eee}.inst-k li{background:#2e2d34}.inst-k .ik{background:#232228}.inst-k .w{background:#3a2c1c}}";
  var SHARE='<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#0a84ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 15V3"/><path d="m7 8 5-5 5 5"/><path d="M5 12v7a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-7"/></svg>';
  var PLUS='<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="4"/><path d="M12 8v8M8 12h8"/></svg>';
  function styl(){if(document.getElementById("inst-css"))return;var s=document.createElement("style");s.id="inst-css";s.textContent=css;document.head.appendChild(s);}
  function krok(n,t,i){return '<li><span class="n">'+n+'</span><span class="tx">'+t+'</span>'+(i?'<span class="ik">'+i+'</span>':'')+'</li>';}
  function navod(){
    styl();if(VYZVA){VYZVA.prompt();VYZVA.userChoice.then(function(){VYZVA=null;var l=document.getElementById("inst-lista");if(l)l.remove();});return;}
    var h;
    if(ios){h=(inapp||jinyIos?'<div class="w">Máte aplikaci otevřenou '+(inapp?'uvnitř jiné aplikace (e-mail, Messenger, Facebook…)':'v jiném prohlížeči než Safari')+'. Na plochu ji jde přidat <b>jen ze Safari</b>. Zkopírujte odkaz, otevřete Safari a vložte ho do adresy.<br><button class="inst-b" id="inst-kop" style="margin-top:8px">📋 Zkopírovat odkaz</button></div>':'')+
      '<ol>'+krok(1,'Dole klepněte na <b>Sdílet</b>'+(/iPad/.test(UA)?' (na iPadu nahoře vpravo)':''),SHARE)+krok(2,'Sjeďte níž a vyberte <b>Přidat na plochu</b>',PLUS)+krok(3,'Vpravo nahoře klepněte na <b>Přidat</b>','')+'</ol>'+
      '<p class="p">Nevidíte dole lištu? Klepněte nahoře doprostřed stránky, nebo na ikonu kompasu / „Otevřít v Safari“.</p>';}
    else if(/SamsungBrowser/.test(UA)){h='<ol>'+krok(1,'Klepněte na menu <b>☰</b> (dole vpravo)','')+krok(2,'Vyberte <b>Přidat stránku do</b> → <b>Domovská obrazovka</b>','')+'</ol>';}
    else if(android&&/Firefox/.test(UA)){h='<ol>'+krok(1,'Klepněte na menu <b>⋮</b>','')+krok(2,'Vyberte <b>Nainstalovat</b> nebo <b>Přidat na plochu</b>','')+'</ol><p class="p">Když tam volba není, otevřete stránku v Chromu – tam instalace funguje nejspolehlivěji.</p>';}
    else if(android){h='<ol>'+krok(1,'V Chromu klepněte vpravo nahoře na <b>⋮</b>','')+krok(2,'Vyberte <b>Nainstalovat aplikaci</b> nebo <b>Přidat na plochu</b>','')+krok(3,'Potvrďte <b>Nainstalovat</b>','')+'</ol><p class="p">Otevřeli jste odkaz v jiné aplikaci (Gmail, Messenger)? Klepněte na ⋮ a zvolte <b>Otevřít v Chromu</b>.</p>';}
    else{h=QR?'<p>Naskenujte QR kód fotoaparátem telefonu – aplikace se otevře v prohlížeči a pak si ji přidáte na plochu.</p><img src="'+QR+'" alt="QR kód">':'<p>Otevřete tuto stránku v telefonu a přidejte si ji na plochu. V Chromu/Edge na počítači můžete kliknout na ikonu instalace v adresním řádku.</p>';}
    var m=document.createElement("div");m.className="inst-m";m.innerHTML='<div class="inst-k" role="dialog" aria-label="Přidat na plochu"><h3>📲 '+NAZEV+' do telefonu</h3><p class="s">'+(ios?'iPhone / iPad – Safari':android?'Android – Chrome':'Počítač')+'</p>'+h+'<button class="inst-b" id="inst-ok" style="width:100%;margin-top:6px">Rozumím</button></div>';
    document.body.appendChild(m);
    m.addEventListener("click",function(e){if(e.target===m||e.target.id==="inst-ok")m.remove();});
    var k=document.getElementById("inst-kop");if(k)k.addEventListener("click",function(){var u=location.href;(navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){k.textContent="✔ Zkopírováno";},function(){prompt("Zkopírujte odkaz:",u);});});
  }
  window.instalaceNavod=navod;
  function lista(){
    if(BEZLISTY||nainst()||pryc()||document.getElementById("inst-lista"))return;
    if(!ios&&!android&&!VYZVA&&!QR)return;       // počítač bez QR: nic neotravovat
    styl();var l=document.createElement("div");l.id="inst-lista";l.className="inst-l";
    l.innerHTML='<span class="i">📲</span><span class="t"><b>'+NAZEV+' na plochu</b><small>'+(VYZVA?'Nainstalujete jedním klepnutím.':ios?'Na iPhonu 3 klepnutí v Safari – ukážeme kde.':'Otevře se jako aplikace.')+'</small></span><button class="inst-b">'+(VYZVA?'Nainstalovat':'Jak na to')+'</button><button class="inst-x" aria-label="Skrýt">×</button>';
    l.querySelector(".inst-b").addEventListener("click",navod);
    l.querySelector(".inst-x").addEventListener("click",function(){try{localStorage.setItem(KLIC,Date.now())}catch(e){}l.remove();});
    document.body.appendChild(l);
  }
  function start(){setTimeout(lista,D.pozdeji?20000:1500);}
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();
