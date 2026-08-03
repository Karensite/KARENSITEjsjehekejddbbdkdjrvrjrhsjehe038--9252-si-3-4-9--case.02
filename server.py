from flask import Flask, request, jsonify
import requests
import json
import time
import uuid

API_KEY = "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"
MODEL = "google/gemma-4-26b-a4b-it:free"

app = Flask(__name__)

MEMORY_FILE = "memorycase.02.json"


def load_memory():
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if "conversations" not in data:
                data["conversations"] = {}
            if "active" not in data or data["active"] not in data["conversations"]:
                cid = "default"
                data["conversations"][cid] = {
                    "name": "گفتگو پیش‌فرض",
                    "created": time.time(),
                    "updated": time.time(),
                    "messages": []
                }
                data["active"] = cid
            return data
    except:
        cid = "default"
        return {
            "conversations": {
                cid: {
                    "name": "گفتگو پیش‌فرض",
                    "created": time.time(),
                    "updated": time.time(),
                    "messages": []
                }
            },
            "active": cid
        }


def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)


def internet_search(query):
    url = f"https://api.duckduckgo.com/?q={query}&format=json"
    r = requests.get(url)
    try:
        data = r.json()
        abstract = data.get("Abstract", "")
        if abstract:
            return abstract
        else:
            return "چیزی پیدا نشد."
    except:
        return "خطا در سرچ اینترنت."


def talk_to_model(prompt, conv):
    url = "https://openrouter.ai/api/v1/chat/completions"

    system_message = (
        "تو یک مدل هوش مصنوعی هستی که اسمش case.02 است. "
        "سازنده‌ات Karen Nasirpour است. "
        "خیلی مودب، خیلی خودمونی، خیلی سریع و دقیق جواب می‌دهی. "
        "اگر کاربر گفت 'سرچ ...'، نتیجهٔ سرچ اینترنت به تو داده می‌شود. "
        "اگر کاربر یا خودت بگویی 'حذف n پیام قبلی'، سرور چند پیام قبلی را حذف می‌کند."
    )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "KarenAI",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": system_message}]

    for m in conv["messages"][-10:]:
        messages.append({"role": m["role"], "content": m["content"]})

    messages.append({"role": "user", "content": prompt})

    data = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.2
    }

    r = requests.post(url, json=data, headers=headers)
    j = r.json()

    if "choices" not in j:
        return f"خطا از سرور: {j}"

    return j["choices"][0]["message"]["content"]


HTML_PAGE = """
<!DOCTYPE html>
<html lang="fa">
<head>
<meta charset="UTF-8">
<title>case.02 - Karen AI</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body { background:#111; color:#fff; font-family:sans-serif; padding:20px; }
#chatbox { width:100%; height:50vh; background:#222; padding:10px; overflow-y:auto; border-radius:10px; }
input { width:60%; padding:10px; border-radius:8px; border:none; }
button { padding:10px 15px; border:none; border-radius:8px; background:#0a84ff; color:white; margin:2px; }
select { padding:8px; border-radius:8px; }
@media (max-width:600px){
    input { width:55%; }
    #chatbox { height:45vh; }
}
</style>
</head>
<body>
<h2>case.02 — چت با هوش مصنوعی Karen</h2>

<div>
    <label>گفتگو فعال:</label>
    <select id="convSelect" onchange="changeConv()"></select>
    <button onclick="newConv()">گفتگوی جدید</button>
    <button onclick="renameConv()">تغییر نام</button>
    <button onclick="deleteConv()">حذف گفتگو</button>
</div>

<br>
<div id="chatbox"></div>
<br>
<input id="msg" placeholder="پیام را بنویس...">
<button onclick="send()">ارسال</button>

<script>
function loadConversations(){
    fetch("/conversations")
    .then(r => r.json())
    .then(d => {
        let sel = document.getElementById("convSelect");
        sel.innerHTML = "";
        d.list.forEach(c => {
            let opt = document.createElement("option");
            opt.value = c.id;
            opt.textContent = c.name;
            if (c.id === d.active){
                opt.selected = true;
            }
            sel.appendChild(opt);
        });
        loadChat();
    });
}

function loadChat(){
    fetch("/history")
    .then(r => r.json())
    .then(d => {
        let box = document.getElementById("chatbox");
        box.innerHTML = "";
        d.messages.forEach(m => {
            let who = (m.role === "user") ? "شما" : "case.02";
            box.innerHTML += "<div><b>" + who + ":</b> " + m.content + "</div>";
        });
        box.scrollTop = box.scrollHeight;
    });
}

function send(){
    let m = document.getElementById("msg").value;
    document.getElementById("msg").value = "";
    let box = document.getElementById("chatbox");
    box.innerHTML += "<div><b>شما:</b> " + m + "</div>";
    box.scrollTop = box.scrollHeight;

    fetch("/chat", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({message:m})
    })
    .then(r => r.json())
    .then(d => {
        box.innerHTML += "<div><b>case.02:</b> " + d.reply + "</div>";
        box.scrollTop = box.scrollHeight;
    });
}

function changeConv(){
    let id = document.getElementById("convSelect").value;
    fetch("/set_active", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({id:id})
    }).then(() => loadChat());
}

function newConv(){
    let name = prompt("نام گفتگو جدید:");
    if (!name) return;
    fetch("/new_conv", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({name:name})
    }).then(() => loadConversations());
}

function renameConv(){
    let id = document.getElementById("convSelect").value;
    let name = prompt("نام جدید گفتگو:");
    if (!name) return;
    fetch("/rename_conv", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({id:id, name:name})
    }).then(() => loadConversations());
}

function deleteConv(){
    let id = document.getElementById("convSelect").value;
    if (!confirm("این گفتگو حذف شود؟")) return;
    fetch("/delete_conv", {
        method:"POST",
        headers:{ "Content-Type":"application/json" },
        body: JSON.stringify({id:id})
    }).then(() => loadConversations());
}

window.onload = loadConversations;
</script>
</body>
</html>
"""


@app.route("/")
def home():
    return HTML_PAGE


@app.route("/conversations")
def conversations():
    mem = load_memory()
    convs = []
    for cid, c in mem["conversations"].items():
        convs.append({"id": cid, "name": c.get("name", cid)})
    return jsonify({"list": convs, "active": mem["active"]})


@app.route("/history")
def history():
    mem = load_memory()
    cid = mem["active"]
    conv = mem["conversations"][cid]
    return jsonify({"messages": conv["messages"]})


@app.route("/set_active", methods=["POST"])
def set_active():
    mem = load_memory()
    cid = request.json.get("id")
    if cid in mem["conversations"]:
        mem["active"] = cid
        save_memory(mem)
    return jsonify({"ok": True})


@app.route("/new_conv", methods=["POST"])
def new_conv():
    mem = load_memory()
    name = request.json.get("name", "گفتگو جدید")
    cid = str(uuid.uuid4())
    mem["conversations"][cid] = {
        "name": name,
        "created": time.time(),
        "updated": time.time(),
        "messages": []
    }
    mem["active"] = cid
    save_memory(mem)
    return jsonify({"ok": True})


@app.route("/rename_conv", methods=["POST"])
def rename_conv():
    mem = load_memory()
    cid = request.json.get("id")
    name = request.json.get("name", "")
    if cid in mem["conversations"] and name:
        mem["conversations"][cid]["name"] = name
        mem["conversations"][cid]["updated"] = time.time()
        save_memory(mem)
    return jsonify({"ok": True})


@app.route("/delete_conv", methods=["POST"])
def delete_conv():
    mem = load_memory()
    cid = request.json.get("id")
    if cid in mem["conversations"]:
        del mem["conversations"][cid]
        if not mem["conversations"]:
            new_id = "default"
            mem["conversations"][new_id] = {
                "name": "گفتگو پیش‌فرض",
                "created": time.time(),
                "updated": time.time(),
                "messages": []
            }
            mem["active"] = new_id
        else:
            mem["active"] = list(mem["conversations"].keys())[0]
        save_memory(mem)
    return jsonify({"ok": True})


@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "")
    mem = load_memory()
    cid = mem["active"]
    conv = mem["conversations"][cid]

    if user_msg.startswith("سرچ "):
        query = user_msg.replace("سرچ ", "")
        result = internet_search(query)
        user_msg += f"\n\nنتیجه سرچ: {result}"

    if user_msg.startswith("حذف "):
        try:
            parts = user_msg.split()
            n = int(parts[1])
            delete_count = n * 2
            conv["messages"] = conv["messages"][:-delete_count] if delete_count <= len(conv["messages"]) else []
            mem["conversations"][cid] = conv
            save_memory(mem)
            return jsonify({"reply": f"{n} پیام قبلی حذف شد."})
        except:
            pass

    conv["messages"].append({
        "role": "user",
        "content": user_msg,
        "time": time.time()
    })

    reply = talk_to_model(user_msg, conv)

    conv["messages"].append({
        "role": "assistant",
        "content": reply,
        "time": time.time()
    })

    conv["updated"] = time.time()
    mem["conversations"][cid] = conv
    save_memory(mem)

    return jsonify({"reply": reply})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
