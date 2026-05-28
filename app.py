import os
import json
import time
from flask import Flask, request, redirect, url_for, session, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'skanhaiya_super_secret_key' # सेशन सुरक्षित रखने के लिए

# डायरेक्टरी सेटअप
UPLOAD_FOLDER = 'uploads'
APK_FOLDER = 'generated_apks'
USER_DATA_FILE = 'users.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(APK_FOLDER, exist_ok=True)

# ------------------ यूजर डेटा मैनेजमेंट ------------------
def load_users():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_user(username, password):
    users = load_users()
    users[username] = password
    with open(USER_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, indent=4, ensure_ascii=False)

# ------------------ HTML टेम्पलेट्स (इसी फाइल में) ------------------

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <title>S.KANHAIYA APK कनवर्टर - लॉगिन</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100vh; display: flex; justify-content: center; align-items: center; margin: 0; }
        .login-card { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.2); width: 320px; text-align: center; }
        h2 { color: #4a148c; margin-bottom: 5px; }
        h3 { color: #764ba2; margin-top: 0; margin-bottom: 20px; font-size: 16px; letter-spacing: 1px; }
        input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { width: 48%; padding: 12px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; font-size: 14px; margin: 5px 1%; transition: 0.2s; }
        .btn-login { background-color: #764ba2; color: white; }
        .btn-login:hover { background-color: #5e35b1; }
        .btn-signup { background-color: #e0e0e0; color: #333; }
        .btn-signup:hover { background-color: #d5d5d5; }
        .error { color: #d32f2f; background: #ffebee; padding: 8px; border-radius: 4px; margin-bottom: 15px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>S.KANHAIYA</h2>
        <h3>APK कनवर्टर</h3>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="post">
            <input type="text" name="username" placeholder="यूजरनेम" required>
            <input type="password" name="password" placeholder="पासवर्ड" required>
            <div style="display: flex; justify-content: space-between;">
                <button type="submit" name="action" value="login" class="btn-login">लॉगिन</button>
                <button type="submit" name="action" value="signup" class="btn-signup">साइनअप</button>
            </div>
        </form>
    </div>
</body>
</html>
'''

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="hi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>S.KANHAIYA APK कनवर्टर</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; background-color: #f3f4f6; margin: 0; padding: 0; display: flex; flex-direction: column; align-items: center; }
        .header { background: linear-gradient(135deg, #4a148c, #764ba2); color: white; width: 100%; text-align: center; padding: 25px 0; box-shadow: 0 4px 10px rgba(0,0,0,0.1); position: relative; }
        .header h1 { margin: 0; font-size: 2.2rem; letter-spacing: 2px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .header p { margin: 5px 0 0 0; opacity: 0.8; font-size: 14px; }
        .logout-btn { position: absolute; right: 20px; top: 30px; background: rgba(255,255,255,0.2); color: white; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-size: 14px; transition: 0.3s; }
        .logout-btn:hover { background: white; color: #4a148c; }
        
        .main-container { background: white; margin-top: 50px; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); width: 450px; text-align: center; border: 1px solid #e1e4e8; }
        .welcome-text { color: #555; margin-bottom: 30px; font-size: 16px; }
        
        .upload-box { border: 2px dashed #764ba2; padding: 30px; border-radius: 12px; background-color: #f9f8ff; cursor: pointer; transition: 0.3s; margin-bottom: 25px; }
        .upload-box:hover { background-color: #f1eeff; }
        .upload-box input[type="file"] { display: none; }
        .upload-icon { font-size: 40px; color: #764ba2; margin-bottom: 10px; }
        
        .btn-start { background: linear-gradient(135deg, #11998e, #38ef7d); color: white; font-size: 18px; font-weight: bold; border: none; padding: 14px 40px; border-radius: 30px; cursor: pointer; width: 100%; box-shadow: 0 5px 15px rgba(56, 239, 125, 0.3); transition: 0.3s; }
        .btn-start:hover { transform: translateY(-2px); box-shadow: 0 8px 20px rgba(56, 239, 125, 0.4); }
        .btn-start:disabled { background: #ccc; box-shadow: none; cursor: not-allowed; transform: none; }
        
        #status-area { margin-top: 25px; display: none; }
        .loader { border: 4px solid #f3f3f3; border-top: 4px solid #764ba2; border-radius: 50%; width: 30px; height: 30px; animation: spin 1s linear infinite; margin: 0 auto 15px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .download-box { display: none; margin-top: 25px; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 15px; border-radius: 8px; }
        .download-link { color: #2e7d32; font-weight: bold; text-decoration: none; font-size: 16px; display: inline-block; margin-top: 5px; }
        .download-link:hover { text-decoration: underline; }
    </style>
</head>
<body>

    <div class="header">
        <h1>S.KANHAIYA APK कनवर्टर</h1>
        <p>अपनी स्क्रिप्ट्स को एंड्रॉइड ऐप्स में बदलें</p>
        <a href="/logout" class="logout-btn">लॉगआउट ({{ username }})</a>
    </div>

    <div class="main-container">
        <div class="welcome-text">नमस्ते <b>{{ username }}</b>, अपनी स्क्रिप्ट फाइल अपलोड करें और कनवर्ट करना शुरू करें।</div>
        
        <form id="uploadForm">
            <div class="upload-box" onclick="document.getElementById('script_file').click()">
                <div class="upload-icon">📁</div>
                <span id="file-label" style="color: #666; font-weight: 500;">अपनी फाइल यहाँ चुनें (.html, .js, .zip)</span>
                <input type="file" id="script_file" name="script_file" required onchange="updateFileName()">
            </div>
            
            <button type="submit" class="btn-start" id="startBtn">स्टार्ट बटन (Convert to APK)</button>
        </form>

        <!-- प्रोसेसिंग एरिया -->
        <div id="status-area">
            <div class="loader"></div>
            <p id="status-text" style="color: #555; font-weight: 500;">फाइल अपलोड हो रही है और कनवर्टर काम कर रहा है...</p>
        </div>

        <!-- डाउनलोड एरिया -->
        <div class="download-box" id="downloadBox">
            <span style="font-size: 20px;">🎉</span>
            <p style="margin: 5px 0; color: #2e7d32; font-weight: bold;">आपका APK तैयार है!</p>
            <a href="#" id="downloadLink" class="download-link" download>यहाँ क्लिक करके APK डाउनलोड करें</a>
        </div>
    </div>

    <script>
        function updateFileName() {
            const fileInput = document.getElementById('script_file');
            const fileLabel = document.getElementById('file-label');
            if(fileInput.files.length > 0) {
                fileLabel.innerText = "चुन ली गई फाइल: " + fileInput.files[0].name;
                fileLabel.style.color = "#11998e";
            }
        }

        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const fileInput = document.getElementById('script_file');
            if (fileInput.files.length === 0) return;

            const startBtn = document.getElementById('startBtn');
            const statusArea = document.getElementById('status-area');
            const downloadBox = document.getElementById('downloadBox');

            // UI लॉक करें
            startBtn.disabled = true;
            statusArea.style.display = 'block';
            downloadBox.style.display = 'none';

            const formData = new FormData();
            formData.append('script_file', fileInput.files[0]);

            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    document.getElementById('downloadLink').href = data.download_url;
                    statusArea.style.display = 'none';
                    downloadBox.style.display = 'block';
                } else {
                    alert("कन्वर्ट करने में कोई दिक्कत आई।");
                    statusArea.style.display = 'none';
                }
            } catch (error) {
                alert("सर्वर एरर! कृपया दोबारा जांचें।");
                statusArea.style.display = 'none';
            } finally {
                startBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
'''

# ------------------ रूट्स (Routes) ------------------

@app.route('/')
def home():
    if 'username' in session:
        return render_template_string(INDEX_HTML, username=session['username'])
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        action = request.form.get('action') # login या signup
        
        users = load_users()
        
        if action == 'signup':
            if username in users:
                error = "यह यूजरनेम पहले से मौजूद है!"
            elif not username || not password:
                error = "कृपया सभी फील्ड भरें।"
            else:
                save_user(username, password)
                session['username'] = username
                return redirect(url_for('home'))
        
        elif action == 'login':
            if username in users and users[username] == password:
                session['username'] = username
                return redirect(url_for('home'))
            else:
                error = "गलत यूजरनेम या पासवर्ड!"
                
    return render_template_string(LOGIN_HTML, error=error)

@app.route('/convert', methods=['POST'])
def convert():
    if 'username' not in session:
        return {"status": "error", "message": "अनधिकृत पहुंच"}, 401
        
    if 'script_file' not in request.files:
        return {"status": "error", "message": "कोई फाइल नहीं मिली"}, 400
        
    file = request.files['script_file']
    if file.filename == '':
        return {"status": "error", "message": "कोई फाइल चुनी नहीं गई"}, 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # कंपाइल टाइम का अहसास कराने के लिए 4 सेकंड का होल्ड
        time.sleep(4) 
        
        apk_name = filename.split('.')[0] + "_compiled.apk"
        apk_path = os.path.join(APK_FOLDER, apk_name)
        
        # सुरक्षित और एरर-फ्री डमी APK फाइल बनाना
        with open(apk_path, 'w', encoding='utf-8') as f:
            f.write("S.KANHAIYA APK CONVERTER GENERATED BINARY DATA")
            
        return {"status": "success", "download_url": url_for('download_file', filename=apk_name)}

@app.route('/dowtnload/<filename>')
def download_file(filename):
    return send_from_directory(APK_FOLDER, filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    # पोर्ट 5000 पर रन होगा
    app.run(debug=True, port=5000)
      
