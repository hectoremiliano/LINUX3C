from pathlib import Path
from html import escape
from urllib.parse import quote
from datetime import datetime
import shutil

AUTOR = "Héctor Emiliano"
ROOT = Path("/var/www/proyecto.linux")
REPO = Path("/home/kali/LINUX3C")
EVIDENCIAS = ROOT / "evidencias"

UNIDADES = [
 {"key":"UNIDAD1","titulo":"Terminal y archivos","color":"#55e6c1",
  "desc":"Primeros pasos en la terminal: moverse entre carpetas, crear archivos y directorios, y atajos con alias.",
  "comandos":[
   ("ls","Lista el contenido de la carpeta actual"),
   ("ls -la","Lista con detalle, incluidos archivos ocultos"),
   ("ls -lah","Igual, con tamaños legibles"),
   ("cd ruta","Cambia de directorio"),
   ("cd ..","Sube un nivel"),
   ("mkdir -p ruta","Crea carpetas (y las intermedias)"),
   ("touch archivo","Crea un archivo vacío"),
   ("nano archivo","Edita un archivo de texto"),
   ("printf 'texto' > archivo","Escribe texto dentro de un archivo"),
   ("alias ll='ls -lah'","Crea un atajo para un comando"),
   ("type ll","Muestra qué tipo de comando es (alias, programa...)"),
  ]},
 {"key":"UNIDAD2","titulo":"Scripts en Bash y respaldos","color":"#65a9ff",
  "desc":"Scripts con permisos, entrada de datos y menús; respaldos con tar y rsync; y pruebas de rotación de logs.",
  "comandos":[
   ("nano script.sh","Crea o edita un script"),
   ("sh script.sh","Ejecuta un script con sh"),
   ("chmod +x script.sh","Da permiso de ejecución"),
   ("./script.sh","Ejecuta un script"),
   ("./script.sh directorio","Ejecuta un script pasándole un argumento"),
   ("chmod 400 archivo","Solo lectura para el dueño"),
   ("chmod 111 archivo","Solo ejecución, sin lectura"),
   ("sudo -v","Renueva las credenciales de sudo"),
   ("read -p 'texto' variable","Pide un dato al usuario dentro de un script"),
   ("case ... esac","Estructura de menú de opciones en un script"),
   ("tar -czvf respaldo.tar carpeta","Crea un respaldo comprimido"),
   ("tar -tf respaldo.tar","Lista el contenido de un tar"),
   ("rsync --dry-run origen destino","Simula una copia sin hacerla"),
   ("logrotate -d archivo.conf","Prueba la rotación de logs en modo debug"),
  ]},
 {"key":"UNIDAD3","titulo":"Seguridad y acceso remoto","color":"#b794ff",
  "desc":"Auditoría de seguridad del sistema con Lynis y conexión remota segura por SSH.",
  "comandos":[
   ("sudo lynis audit system","Auditoría de seguridad del sistema"),
   ("ssh usuario@ip","Conexión remota segura"),
  ]},
 {"key":"UNIDAD4","titulo":"Servidor web, DNS y SSH","color":"#ffb454",
  "desc":"Sitio web propio con Apache, dominio local con BIND9 y verificación del contenido por SSH.",
  "comandos":[
   ("sudo systemctl status apache2","Estado de Apache"),
   ("sudo systemctl restart apache2","Reinicia Apache"),
   ("sudo a2ensite sitio.conf","Habilita un sitio virtual"),
   ("sudo apache2ctl configtest","Verifica la configuración de Apache"),
   ("sudo named-checkconf","Verifica la configuración de BIND"),
   ("dig @127.0.0.1 proyecto.linux","Consulta al servidor DNS propio"),
   ("curl -H 'Host: proyecto.linux' http://127.0.0.1/","Prueba la web por nombre"),
   ("ssh kali@10.0.2.15 \"ls -la /var/www/proyecto.linux\"","Verifica la carpeta del sitio por SSH"),
  ]},
]

if EVIDENCIAS.exists():
    shutil.rmtree(EVIDENCIAS)

for u in UNIDADES:
    if not REPO.exists():
        break
    origen = next((p for p in REPO.iterdir() if p.is_dir() and p.name.upper() == u["key"]), None)
    if not origen:
        continue
    for img in sorted(origen.rglob("*")):
        if img.is_file() and img.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}:
            destino = EVIDENCIAS / u["key"] / img.relative_to(origen)
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(img, destino)

def tarjeta(cmd, desc, etiqueta):
    busca = escape((cmd + " " + desc + " " + etiqueta).lower(), quote=True)
    return (f'<article class="cmd" data-search="{busca}">'
            f'<span class="tag">{escape(etiqueta)}</span>'
            f'<code>{escape(cmd)}</code><p>{escape(desc)}</p>'
            f'<button type="button" data-command="{escape(cmd, quote=True)}">Copiar comando</button>'
            f'</article>')

def galeria(u):
    base = EVIDENCIAS / u["key"]
    imagenes = sorted([p for p in base.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]) if base.exists() else []
    tarjetas = []
    for img in imagenes:
        url = "/" + quote(img.relative_to(ROOT).as_posix(), safe="/")
        nombre = escape(img.relative_to(base).as_posix())
        tarjetas.append(f'<a class="evidence" href="{url}" data-caption="{nombre}">'
                        f'<img src="{url}" loading="lazy" alt="{nombre}"><span>{nombre}</span></a>')
    return tarjetas

total_caps = 0
total_cmds = 0
secciones = []
for i, u in enumerate(UNIDADES, 1):
    caps = galeria(u)
    total_caps += len(caps)
    total_cmds += len(u["comandos"])
    cards = "".join(tarjeta(c, d, f"Unidad {i}") for c, d in u["comandos"])
    secciones.append(f'''
<section class="unit" id="unidad{i}" style="--c:{u["color"]}">
  <div class="section-heading">
    <div>
      <span class="eyebrow">UNIDAD {i:02d}</span>
      <h2>{escape(u["titulo"])}</h2>
      <p class="desc">{escape(u["desc"])}</p>
    </div>
    <div class="chips"><span class="count">{len(u["comandos"])} comandos</span><span class="count">{len(caps)} capturas</span></div>
  </div>
  <div class="cmdblock"><h3 class="sub">Comandos de la unidad</h3><div class="command-grid">{cards}</div></div>
  <h3 class="sub">Capturas de pantalla</h3>
  <div class="gallery">{"".join(caps) if caps else '<p class="vacio">No hay capturas disponibles.</p>'}</div>
</section>''')

html = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Linux Lab | Portafolio</title>
<style>
:root{--bg:#080d18;--panel:#101a2b;--panel2:#142238;--text:#e8f0ff;--muted:#91a3bd;--accent:#55e6c1;--blue:#65a9ff;--border:rgba(145,163,189,.16)}
*{box-sizing:border-box}[hidden]{display:none!important}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,"Segoe UI",system-ui,Arial,sans-serif;line-height:1.6;background-image:radial-gradient(900px 420px at 85% -5%,#1d3b6a40,transparent),radial-gradient(700px 380px at 0% 20%,#55e6c115,transparent);background-repeat:no-repeat}
a{color:inherit;text-decoration:none}header{position:sticky;top:0;z-index:10;background:rgba(8,13,24,.88);backdrop-filter:blur(15px);border-bottom:1px solid var(--border)}
.nav{max-width:1180px;margin:auto;padding:14px 24px;display:flex;align-items:center;justify-content:space-between;gap:20px}
.logo{font-size:19px;font-weight:800;letter-spacing:1px}.logo span{color:var(--accent)}nav{display:flex;gap:6px;flex-wrap:wrap}
nav a{font-size:13px;color:var(--muted);padding:6px 12px;border-radius:999px;border:1px solid transparent;transition:.2s}
nav a:hover{color:var(--text);background:var(--panel)}nav a.on{color:var(--accent);border-color:#55e6c144;background:#55e6c112}
.hero{max-width:1180px;margin:auto;padding:90px 24px 70px;display:grid;grid-template-columns:1.4fr .8fr;gap:45px;align-items:center}
.eyebrow{font-size:11px;letter-spacing:3px;color:var(--c,var(--accent));font-weight:800}
h1{font-size:clamp(42px,7vw,76px);line-height:1.04;margin:18px 0}
h1 span{background:linear-gradient(90deg,#55e6c1,#65a9ff,#b794ff);-webkit-background-clip:text;background-clip:text;color:transparent}
.hero p{max-width:620px;color:var(--muted);font-size:17px}
.autor{display:inline-block;margin-top:14px;padding:6px 14px;border:1px solid var(--border);border-radius:999px;font-size:13px;color:var(--text);background:var(--panel)}
.hero-card{background:linear-gradient(145deg,#142941,#0d1728);border:1px solid var(--border);border-radius:22px;padding:28px;box-shadow:0 25px 70px #0005}
.terminal{background:#070c14;border-radius:13px;padding:20px;font-family:Consolas,"Courier New",monospace;color:#b8c9dc;font-size:13px}
.terminal .green{color:var(--accent)}.terminal .blue{color:var(--blue)}
.cursor{animation:blink 1s steps(2) infinite}@keyframes blink{50%{opacity:0}}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:20px}
.stat{background:#ffffff08;padding:15px;border-radius:12px}.stat strong{display:block;font-size:25px;color:var(--accent)}.stat small{color:var(--muted)}
main{max-width:1180px;margin:auto;padding:0 24px}
.finder{position:sticky;top:62px;z-index:9;padding:14px 0;background:linear-gradient(var(--bg) 75%,transparent)}
.search{width:100%;padding:16px 20px;border:1px solid var(--border);background:var(--panel);border-radius:12px;color:var(--text);font-size:15px;outline:none}
.search:focus{border-color:var(--accent)}#resultados{display:block;min-height:20px;color:var(--muted);font-size:13px;margin:6px 4px 0}
.unit{padding:50px 0 40px;border-top:1px solid var(--border);scroll-margin-top:130px}
.section-heading{display:flex;justify-content:space-between;align-items:flex-end;gap:20px;margin-bottom:10px;flex-wrap:wrap}
h2{font-size:32px;margin:5px 0}.desc{color:var(--muted);margin:0;max-width:640px}.chips{display:flex;gap:8px;flex-wrap:wrap}
.count{color:var(--c);font-size:13px;border:1px solid color-mix(in srgb,var(--c) 45%,transparent);background:color-mix(in srgb,var(--c) 10%,transparent);padding:7px 13px;border-radius:30px;white-space:nowrap}
.sub{margin:30px 0 14px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--muted)}
.command-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}
.cmd{background:var(--panel);padding:18px;border:1px solid var(--border);border-left:3px solid var(--c);border-radius:14px;min-width:0;display:flex;flex-direction:column}
.tag{font-size:10px;color:var(--c);text-transform:uppercase;letter-spacing:1.5px}
.cmd code{display:block;color:var(--blue);font-family:Consolas,"Courier New",monospace;font-size:14px;margin:12px 0;overflow-wrap:anywhere}
.cmd p{color:var(--muted);font-size:13px;margin:0 0 14px;flex:1}
button{align-self:flex-start;background:#55e6c118;color:var(--accent);border:1px solid #55e6c144;padding:8px 13px;border-radius:8px;cursor:pointer;font:inherit;font-size:13px}
button:hover{background:#55e6c12e}.gallery{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.evidence{display:block;background:var(--panel);border:1px solid var(--border);border-radius:14px;overflow:hidden;transition:.25s}
.evidence:hover{transform:translateY(-5px);border-color:var(--c)}
.evidence img{width:100%;aspect-ratio:16/10;object-fit:contain;display:block;background:#05080f;cursor:zoom-in}
.evidence span{display:block;padding:11px 12px;color:var(--muted);font-size:12px;overflow-wrap:anywhere}.vacio{color:var(--muted);font-style:italic}
footer{margin-top:50px;padding:35px 24px;text-align:center;border-top:1px solid var(--border);color:var(--muted);font-size:12px}
#top{position:fixed;right:20px;bottom:20px;width:44px;height:44px;border-radius:50%;background:var(--panel);border:1px solid var(--border);display:grid;place-items:center;color:var(--accent);opacity:0;pointer-events:none;transition:.2s;z-index:12}
#top.on{opacity:1;pointer-events:auto}#toast{position:fixed;left:50%;bottom:28px;transform:translate(-50%,20px);background:var(--accent);color:#04231c;padding:9px 18px;border-radius:999px;font-size:13px;font-weight:700;opacity:0;pointer-events:none;transition:.25s;z-index:60}
#toast.on{opacity:1;transform:translate(-50%,0)}#lb{position:fixed;inset:0;background:rgba(3,6,12,.94);display:none;align-items:center;justify-content:center;flex-direction:column;z-index:50;padding:20px}
#lb.on{display:flex}#lb img{max-width:94vw;max-height:80vh;border-radius:10px;box-shadow:0 20px 60px #000}
#lbtxt{color:#cbd5e1;font-size:13px;margin:14px 0 4px;text-align:center}#lbhelp{color:var(--muted);font-size:12px}
.lbbtn{position:absolute;top:50%;transform:translateY(-50%);background:#ffffff14;border:1px solid var(--border);color:#fff;width:46px;height:46px;border-radius:50%;font-size:20px;display:grid;place-items:center;padding:0}
#lbprev{left:16px}#lbnext{right:16px}#lbclose{position:absolute;top:16px;right:16px;transform:none}
@media(max-width:900px){.hero{grid-template-columns:1fr;padding-top:55px}.gallery,.command-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.finder{top:98px}}
@media(max-width:520px){.nav{align-items:flex-start;flex-direction:column;gap:8px}.gallery,.command-grid{grid-template-columns:1fr}.stats{grid-template-columns:1fr}.finder{top:120px}}
</style>
</head>
<body>
<header><div class="nav"><a class="logo" href="#inicio">LINUX<span>_LAB</span></a><nav><a href="#inicio">Inicio</a><a href="#unidad1">Unidad 1</a><a href="#unidad2">Unidad 2</a><a href="#unidad3">Unidad 3</a><a href="#unidad4">Unidad 4</a></nav></div></header>
<section class="hero" id="inicio">
 <div><span class="eyebrow">LINUX • ADMINISTRACIÓN • TERMINAL</span><h1>Explorando el<br><span>universo Linux.</span></h1>
 <p>Portafolio académico de prácticas, comandos y evidencias realizadas durante el curso.</p>
 <span class="autor">__AUTOR__</span></div>
 <div class="hero-card"><div class="terminal"><div><span class="green">kali@proyecto-linux</span>:~$ whoami</div><div>hectoremiliano</div><br><div><span class="green">kali@proyecto-linux</span>:~$ <span class="blue">ls</span></div><div>UNIDAD1/ UNIDAD2/ UNIDAD3/ UNIDAD4/</div><br><div><span class="green">kali@proyecto-linux</span>:~$ <span class="cursor blue">_</span></div></div>
 <div class="stats"><div class="stat"><strong>04</strong><small>Unidades</small></div><div class="stat"><strong>__NCMD__</strong><small>Comandos</small></div><div class="stat"><strong>__NCAP__</strong><small>Capturas</small></div></div></div>
</section>
<main><div class="finder"><input class="search" id="busqueda" type="search" placeholder="Buscar en todos los comandos..."><span id="resultados"></span></div>__UNIDADES__</main>
<footer>LINUX_LAB · Portafolio académico · Generado el __FECHA__</footer>
<a id="top" href="#inicio">↑</a><div id="toast">¡Comando copiado!</div>
<div id="lb"><button class="lbbtn" id="lbclose" type="button">✕</button><button class="lbbtn" id="lbprev" type="button">‹</button><img id="lbimg" alt=""><button class="lbbtn" id="lbnext" type="button">›</button><div id="lbtxt"></div><div id="lbhelp">← → para navegar · Esc para cerrar</div></div>
<script>
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
$('#busqueda').addEventListener('input',function(){const q=this.value.trim().toLowerCase();let n=0;$$('.cmd').forEach(c=>{const ok=!q||c.dataset.search.includes(q);c.hidden=!ok;if(ok)n++;});$$('.cmdblock').forEach(b=>{b.hidden=!!q&&!b.querySelector('.cmd:not([hidden])');});$('#resultados').textContent=q?(n?n+' resultado(s)':'No se encontraron comandos.'):'';});
let tt;function aviso(m){const t=$('#toast');t.textContent=m;t.classList.add('on');clearTimeout(tt);tt=setTimeout(()=>t.classList.remove('on'),1400);}
function respaldo(texto){const a=document.createElement('textarea');a.value=texto;a.style.cssText='position:fixed;opacity:0';document.body.appendChild(a);a.select();let ok=false;try{ok=document.execCommand('copy');}catch(e){}a.remove();aviso(ok?'¡Comando copiado!':'No se pudo copiar');}
document.addEventListener('click',e=>{const b=e.target.closest('button[data-command]');if(!b)return;const t=b.dataset.command;if(navigator.clipboard&&window.isSecureContext){navigator.clipboard.writeText(t).then(()=>aviso('¡Comando copiado!'),()=>respaldo(t));}else respaldo(t);});
const imgs=$$('.evidence');let idx=0;const lb=$('#lb'),lbi=$('#lbimg'),lbt=$('#lbtxt');
function abrir(n){idx=(n+imgs.length)%imgs.length;const a=imgs[idx];lbi.src=a.href;lbt.textContent=a.dataset.caption+' · '+(idx+1)+' / '+imgs.length;lb.classList.add('on');}
function cerrar(){lb.classList.remove('on');}imgs.forEach((a,n)=>a.addEventListener('click',e=>{e.preventDefault();abrir(n);}));
$('#lbprev').addEventListener('click',e=>{e.stopPropagation();abrir(idx-1);});$('#lbnext').addEventListener('click',e=>{e.stopPropagation();abrir(idx+1);});$('#lbclose').addEventListener('click',cerrar);
lb.addEventListener('click',e=>{if(e.target===lb)cerrar();});document.addEventListener('keydown',e=>{if(!lb.classList.contains('on'))return;if(e.key==='Escape')cerrar();if(e.key==='ArrowRight')abrir(idx+1);if(e.key==='ArrowLeft')abrir(idx-1);});
const links=$$('nav a');const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting)links.forEach(l=>l.classList.toggle('on',l.getAttribute('href')==='#'+e.target.id));}),{rootMargin:'-45% 0px -50% 0px'});
$$('#inicio, main section[id]').forEach(s=>io.observe(s));addEventListener('scroll',()=>$('#top').classList.toggle('on',scrollY>600),{passive:true});
</script>
</body>
</html>"""

html = (html.replace("__AUTOR__", escape(AUTOR))
            .replace("__NCMD__", str(total_cmds))
            .replace("__NCAP__", str(total_caps))
            .replace("__FECHA__", datetime.now().strftime("%d/%m/%Y %H:%M"))
            .replace("__UNIDADES__", "\n".join(secciones)))

ROOT.mkdir(parents=True, exist_ok=True)
(ROOT / "index.html").write_text(html, encoding="utf-8")
shutil.chown(ROOT, user="www-data", group="www-data")
for ruta in ROOT.rglob("*"):
    shutil.chown(ruta, user="www-data", group="www-data")

print("Página actualizada en /var/www/proyecto.linux:")
for i, u in enumerate(UNIDADES, 1):
    n = len(list((EVIDENCIAS / u["key"]).rglob("*"))) if (EVIDENCIAS / u["key"]).exists() else 0
    print(f"  Unidad {i}: {len(u['comandos'])} comandos, {n} capturas")
