from http.server import HTTPServer, BaseHTTPRequestHandler
import webbrowser
import threading

HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EPIC CRYSTAL</title>
<style>
*{box-sizing:border-box}
body{
 margin:0;background:#090c12;color:#e8edf5;
 font-family:Arial,sans-serif;padding:20px;
}
.container{max-width:700px;margin:auto}
.header{padding:20px 0}
.logo{font-size:32px;font-weight:900;letter-spacing:2px}
.logo span{color:#ff8b32}
.subtitle{color:#7e8a9c;font-size:12px;letter-spacing:3px}
.panel{
 background:#141a24;border:1px solid #222c3b;
 border-radius:16px;padding:22px;margin-top:15px;
}
label{display:block;color:#8c9aad;font-size:12px;
 margin:18px 0 8px;font-weight:bold}
input,select{
 width:100%;padding:14px;background:#202938;
 border:1px solid #303d50;border-radius:9px;
 color:white;font-size:14px
}
button{
 width:100%;padding:16px;border:0;border-radius:10px;
 font-size:15px;font-weight:bold;margin-top:20px;
 cursor:pointer
}
.render{background:#ff8b32;color:#111}
.secondary{background:#202938;color:white}
.status{color:#50d890;text-align:center;margin-top:18px}
.footer{text-align:center;color:#667386;font-size:11px;margin:25px}
</style>
</head>
<body>
<div class="container">
 <div class="header">
  <div class="logo"><span>EPIC</span> CRYSTAL</div>
  <div class="subtitle">VIDEO RENDER ENGINE</div>
 </div>

 <div class="panel">
  <label>SELECT MEDIA</label>
  <input type="file" id="media" accept="video/*,audio/*">

  <label>RESOLUTION</label>
  <select id="resolution">
   <option>960x540</option>
   <option>1280x720</option>
   <option selected>1920x1080</option>
   <option>3840x2160</option>
  </select>

  <label>FRAME RATE</label>
  <select id="fps">
   <option>24</option>
   <option selected>30</option>
   <option>60</option>
  </select>

  <label>ENGINE</label>
  <input value="EPIC CRYSTAL CORE" disabled>

  <button class="render" onclick="render()">▶ START RENDER</button>
  <button class="secondary" onclick="alert('Render output folder will be connected to the engine.')">OPEN OUTPUT</button>

  <div class="status" id="status">● ENGINE INTERFACE READY</div>
 </div>
 <div class="footer">EPIC CRYSTAL • LOCAL INTERFACE</div>
</div>
<script>
function render(){
 const f=document.getElementById('media').files[0];
 if(!f){
  document.getElementById('status').textContent='Select a media file first';
  return;
 }
 document.getElementById('status').textContent=
 'Media selected: '+f.name+' | Engine connection pending';
}
</script>
</body>
</html>
"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type","text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def log_message(self,*args):
        pass

server = HTTPServer(("127.0.0.1",8765),Handler)

def open_browser():
    webbrowser.open("http://127.0.0.1:8765")

threading.Timer(1,open_browser).start()

print("EPIC CRYSTAL GUI running on http://127.0.0.1:8765")
server.serve_forever()
