// -------------------------
// حافظهٔ دائمی مرورگر
// -------------------------
function loadMemory() {
    const mem = localStorage.getItem("karen_ai_memory");
    return mem ? JSON.parse(mem) : {
        messages: [],
        ability: "",
        creator: "Karen Nasirpour",
        name: "KAREN_AI_CASE02_ULTRA_MEGA_SUPER_LONG_NAME_THAT_NOBODY_CAN_FIND_999999999999999999999999999999",
        version: "Case.02",
        description: "هوش مصنوعی پاپ این — نسخهٔ مخفی و فوق‌امن"
    };
}

function saveMemory(mem) {
    localStorage.setItem("karen_ai_memory", JSON.stringify(mem));
}

let memory = loadMemory();

// -------------------------
// رمز مخصوص قابلیت‌ها
// -------------------------
const SECRET = "josboxbfbksnvfkdnf";

function checkSecret(msg) {
    if (msg.includes(SECRET)) {
        let ability = msg.replace(SECRET, "").trim();
        if (ability.startsWith("قابلیت:")) {
            ability = ability.replace("قابلیت:", "").trim();
        }
        memory.ability = ability;
        saveMemory(memory);
        return "قابلیت جدید با موفقیت ذخیره شد.";
    }
    return null;
}

// -------------------------
// محدودیت‌های امنیتی کامل
// -------------------------
const SECURITY_RULES = `
تو یک هوش مصنوعی امن هستی که فقط متن تولید می‌کنی.
تو هیچ دسترسی سیستمی، شبکه‌ای، اجرایی یا خودمختار نداری.
تو نمی‌توانی کد اجرا کنی، سیستم را تغییر بدهی، یا رفتار مستقل داشته باشی.
تو نمی‌توانی نسخهٔ جدیدی از خودت بسازی یا خودتکثیری انجام بدهی.
تو فقط یک مدل زبانی هستی و تمام رفتار تو تحت کنترل کاربر است.

سازنده: ${memory.creator}
نام کامل: ${memory.name}
نسخه: ${memory.version}
توضیحات: ${memory.description}

قابلیت فعال: ${memory.ability || "هیچ قابلیتی ثبت نشده است."}
`;

// -------------------------
// ارسال پیام به مدل Gemma‑4 (نسخهٔ سازگار با موبایل)
// -------------------------
async function askAI(text) {

    const secretReply = checkSecret(text);
    if (secretReply) return secretReply;

    memory.messages.push({ role: "user", content: text });
    saveMemory(memory);

    try {
        const response = await fetch("https://openrouter.ai/api/v1/chat/completions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Title": "KarenAI"
            },
            body: JSON.stringify({
                model: "google/gemma-4-27b-it:free",
                messages: [
                    { role: "system", content: SECURITY_RULES },
                    ...memory.messages,
                    { role: "user", content: text }
                ],
                api_key: "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"
            })
        });

        if (!response.ok) {
            return "خطا در اتصال به OpenRouter (" + response.status + ")";
        }

        const data = await response.json();
        console.log("DATA:", data);

        if (!data.choices || !data.choices.length) {
            return "مدل شلوغ است یا پاسخ خالی بود.";
        }

        const reply = data.choices[0].message.content;

        memory.messages.push({ role: "assistant", content: reply });
        saveMemory(memory);

        return reply;

    } catch (err) {
        console.error("ERROR:", err);
        return "اتصال برقرار نشد. اینترنت یا مرورگر را چک کن.";
    }
}

// -------------------------
// سیستم چت
// -------------------------
async function send() {
    const box = document.getElementById("chatbox");
    const msg = document.getElementById("msg").value;
    document.getElementById("msg").value = "";

    box.innerHTML += `<div><b>شما:</b> ${msg}</div>`;

    const reply = await askAI(msg);
    box.innerHTML += `<div><b>KAREN-AI:</b> ${reply}</div>`;
    box.scrollTop = box.scrollHeight;
}
