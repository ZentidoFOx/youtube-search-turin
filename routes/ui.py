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
body{font-family:system-ui,Arial;margin:20px}h1{font-size:20px}input,button{padding:8px;margin:4px}#info{margin-top:12px}code{background:#f4f4f4;padding:2px 4px;border-radius:4px}
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
</div>
<div id=\"info\"></div>
<script>
const g=(id)=>document.getElementById(id);
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
</script>
</body>
</html>
"""