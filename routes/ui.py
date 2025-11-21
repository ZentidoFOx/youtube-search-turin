from flask import Blueprint

bp = Blueprint("ui", __name__)

@bp.get("/ui")
def ui():
    return """
<!doctype html>
<html>
<head>
<meta charset=\"utf-8\">
<title>YouTube Tools</title>
<style>
body{font-family:system-ui,Arial;margin:20px}h1{font-size:20px}input,button,select{padding:8px;margin:4px}#info,#mp4,#mp3{margin-top:12px}code{background:#f4f4f4;padding:2px 4px;border-radius:4px}
.row{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.card{border:1px solid #ddd;padding:10px;border-radius:8px;margin:6px 0}
.thumb{max-width:240px;border-radius:6px}
</style>
</head>
<body>
<h1>YouTube Tools</h1>
<div class=\"row\">
<input id=\"vid\" placeholder=\"Video ID\" style=\"width:240px\"> 
<button onclick=\"loadInfo()\">Info</button>
<button onclick=\"listMp4()\">MP4</button>
<button onclick=\"listMp3()\">MP3</button>
<select id=\"client\"><option value=\"\">client</option><option>android</option></select>
<select id=\"browser\"><option value=\"\">browser</option><option>chrome</option><option>firefox</option><option>edge</option></select>
<input id=\"profile\" placeholder=\"profile\" style=\"width:160px\">
</div>
<div id=\"info\"></div>
<div id=\"mp4\"></div>
<div id=\"mp3\"></div>
<script>
const g=(id)=>document.getElementById(id);
function qstr(){
 const c=g('client').value;const b=g('browser').value;const p=g('profile').value;let qs='';
 if(c) qs+='&client='+encodeURIComponent(c);
 if(b) qs+='&browser='+encodeURIComponent(b);
 if(p) qs+='&profile='+encodeURIComponent(p);
 return qs;
}
async function loadInfo(){
 const id=g('vid').value.trim(); if(!id){alert('Ingresa ID'); return}
 const r=await fetch('/info?id='+encodeURIComponent(id)); const j=await r.json();
 g('info').innerHTML='<div class="card">'+
 '<div><b>'+ (j.title||'') +'</b></div>'+
 (j.thumbHigh?('<img class="thumb" src="'+j.thumbHigh+'">'):'')+
 '<div>duración: <code>'+ (j.duration||'') +'</code></div>'+
 '<div>views: <code>'+ (j.viewCount||'') +'</code></div>'+
 '</div>';
}
async function listMp4(){
 const id=g('vid').value.trim(); if(!id){alert('Ingresa ID'); return}
 const r=await fetch('/download?id='+encodeURIComponent(id)+'&formt=mp4'+qstr()); const j=await r.json();
 const items=(j.mp4||[]).map(x=>'<div class="card">'+
 '<div><b>'+ (x.quality||'') +'</b></div>'+
 (x.url?('<div>direct: <a href="'+x.url+'" target="_blank">abrir</a></div>'):'')+
 (x.downloadUrl?('<div>server: <a href="'+x.downloadUrl+'" target="_blank">descargar</a></div>'):'')+
 '</div>').join('');
 g('mp4').innerHTML='<h3>MP4</h3>'+items;
}
async function listMp3(){
 const id=g('vid').value.trim(); if(!id){alert('Ingresa ID'); return}
 const r=await fetch('/download?id='+encodeURIComponent(id)+'&formt=mp3'); const j=await r.json();
 const items=(j.mp3||[]).map(x=>'<div class="card">'+
 '<div><b>'+ (x.quality||'') +' kbps</b></div>'+
 '<div><a href="'+x.url+'" target="_blank">descargar</a></div>'+
 '</div>').join('');
 g('mp3').innerHTML='<h3>MP3</h3>'+items;
}
</script>
</body>
</html>
"""