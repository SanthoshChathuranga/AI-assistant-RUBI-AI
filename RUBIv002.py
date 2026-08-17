from tkinter import *
from PIL import Image, ImageTk
import requests
from io import BytesIO
import speech_recognition as sr
import pyttsx3
import datetime
import webbrowser
import threading
import math
import re

#   TEXT TO SPEECH

def text_to_speech(text):
    engine = pyttsx3.init()
    rate = engine.getProperty('rate')
    engine.setProperty('rate', rate - 70)   # slow down a little
    engine.say(text)
    engine.runAndWait()

# ============================================================
#   SPEECH TO TEXT
# ============================================================

def speech_to_text():
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=5)
        voice_data = r.recognize_google(audio)
        return voice_data
    except sr.WaitTimeoutError:
        return "timeout"
    except sr.UnknownValueError:
        return "unknown"
    except sr.RequestError:
        return "request_error"
    except Exception as e:
        return f"error: {e}"

# ============================================================
#   GOOGLE SEARCH FALLBACK
# ============================================================

def google_search(query):
    """Search Google and return a short summary using DuckDuckGo instant answer API (no key needed)."""
    try:
        api_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1&skip_disambig=1"
        resp = requests.get(api_url, timeout=5)
        data = resp.json()

        # Try AbstractText first
        if data.get("AbstractText"):
            return data["AbstractText"]

        # Try RelatedTopics
        topics = data.get("RelatedTopics", [])
        if topics and isinstance(topics[0], dict) and topics[0].get("Text"):
            return topics[0]["Text"]

        # Fallback: open Google in browser
        webbrowser.open(f"https://www.google.com/search?q={requests.utils.quote(query)}")
        return f"Opening Google search for: {query}"

    except Exception as e:
        webbrowser.open(f"https://www.google.com/search?q={requests.utils.quote(query)}")
        return f"Opening Google search for: {query}"


# ============================================================
#   CALCULATOR
# ============================================================

def calculate(user_data):
    """Extract and evaluate a math expression from natural language input."""
    # Replace words with symbols
    expr = user_data.lower()
    expr = expr.replace("plus", "+").replace("add", "+")
    expr = expr.replace("minus", "-").replace("subtract", "-")
    expr = expr.replace("times", "*").replace("multiplied by", "*").replace("multiply", "*")
    expr = expr.replace("divided by", "/").replace("divide", "/").replace("over", "/")
    expr = expr.replace("power", "**").replace("to the power of", "**").replace("squared", "**2").replace("cubed", "**3")
    expr = expr.replace("square root of", "math.sqrt(") .replace("sqrt", "math.sqrt(")
    expr = expr.replace("pi", str(math.pi))
    expr = expr.replace("x", "*")  # common shorthand

    # Close any unclosed math.sqrt( parentheses
    open_count = expr.count("math.sqrt(")
    if open_count > 0:
        expr = expr + ")" * open_count

    # Keep only safe characters
    safe = re.sub(r"[^0-9+\-*/().% mathsqr]", "", expr)
    safe = safe.strip()

    try:
        result = eval(safe, {"__builtins__": {}}, {"math": math})
        # Round if float result is clean
        if isinstance(result, float) and result == int(result):
            result = int(result)
        elif isinstance(result, float):
            result = round(result, 6)
        return f"The answer is {result}"
    except Exception:
        return None

def is_math_query(text):
    """Return True if the input looks like a math/calculation request."""
    math_keywords = [
        "calculate", "what is", "how much is", "compute", "solve",
        "plus", "minus", "times", "divided by", "multiplied by",
        "square root", "sqrt", "power of", "squared", "cubed",
        "percent", "%"
    ]
    math_pattern = re.search(r"[0-9].*[+\-*/^]|[+\-*/^].*[0-9]", text)
    has_keyword = any(kw in text.lower() for kw in math_keywords)
    has_digits = bool(re.search(r"\d", text))
    return (has_keyword and has_digits) or math_pattern is not None

# ============================================================
#   ACTION HANDLER
# ============================================================

def action(user_data):
    if not user_data or user_data in ("timeout", "unknown", "request_error"):
        msg = {
            "timeout":       "I did not hear anything. Please try again.",
            "unknown":       "Sorry, I could not understand that.",
            "request_error": "Speech service error. Check your internet.",
        }.get(user_data, "Something went wrong. Please try again.")
        text_to_speech(msg)
        return msg

    user_data = user_data.lower()

    if "what is your name" in user_data:
        reply = "My name is RUBI, I'm buid by Santhosh Chathuranga. I'm developing AI Assistant"
    elif "hello" in user_data or "hi" in user_data:
        reply = "Hey! How can I help you?"
    elif "good morning" in user_data:
        reply = "Good morning, sir!"
    elif "good night" in user_data:
        reply = "Good night, sir! Take care."
    elif "what is the time" in user_data or "current time" in user_data:
        now = datetime.datetime.now()
        reply = f"The time is {now.hour} hours and {now.minute} minutes."
    elif "what is the date" in user_data or "today's date" in user_data:
        today = datetime.date.today()
        reply = f"Today is {today.strftime('%B %d, %Y')}."
    elif "play music" in user_data:
        webbrowser.open("https://www.youtube.com/results?search_query=music")
        reply = "Opening music on YouTube for you."
    elif "open youtube" in user_data:
        webbrowser.open("https://youtube.com/")
        reply = "YouTube is now open."
    elif "open google" in user_data:
        webbrowser.open("https://google.com")
        reply = "Google is now open."
    elif "open facebook" in user_data:
        webbrowser.open("https://facebook.com")
        reply = "Facebook is now open."
    elif "open instagram" in user_data:
        webbrowser.open("https://instagram.com")
        reply = "Instagram is now open."
    elif "shutdown" in user_data or "bye" in user_data:
        reply = "Goodbye, sir! Have a great day."
        text_to_speech(reply)
        root.after(1500, root.destroy)
        return reply
    elif is_math_query(user_data):
        result = calculate(user_data)
        if result:
            reply = result
        else:
            reply = "Sorry, I could not calculate that. Please try again."
    else:
        # ---- GOOGLE SEARCH FALLBACK ----
        reply = google_search(user_data)

    text_to_speech(reply)
    return reply

# ============================================================
#   TKINTER UI  (interface & images unchanged)
# ============================================================


# ============================================================
#   PASSWORD LOGIN
# ============================================================

def show_login():
    login = Tk()
    login.title("RUBI - Login")
    login.geometry("350x220")
    login.resizable(False, False)
    login.config(bg="#0d1a16")

    Label(login, text="RUBI", font=("comic sans ms", 22, "bold"), bg="#0d1a16", fg="#00fa9a").pack(pady=(25, 5))
    Label(login, text="Enter Password", font=("courier 10 bold"), bg="#0d1a16", fg="#ffffff").pack()

    pw_entry = Entry(login, show="*", justify=CENTER, font=("courier 12 bold"), bg="#00fa9a", fg="#0d1a16", width=20)
    pw_entry.pack(pady=10)
    pw_entry.focus()

    error_label = Label(login, text="", font=("courier 9"), bg="#0d1a16", fg="#ff4444")
    error_label.pack()

    result = {"ok": False}

    def check_password(event=None):
        if pw_entry.get() == "2005":
            result["ok"] = True
            login.destroy()
        else:
            error_label.config(text="Wrong password! Try again.")
            pw_entry.delete(0, END)

    pw_entry.bind("<Return>", check_password)

    Button(
        login, text="LOGIN",
        bg="#35A000", fg="white",
        font=("courier 10 bold"),
        padx=20, pady=6,
        borderwidth=3, relief=SOLID,
        command=check_password
    ).pack(pady=5)

    login.mainloop()
    return result["ok"]

# Run login first
if not show_login():
    import sys
    sys.exit()

root = Tk()
root.title("RUBU v001")
root.geometry("550x720")
root.resizable(False, False)
root.config(bg="#0d1a16")

# ---------- helper: update text widget ----------
def set_text(msg):
    text.config(state=NORMAL)
    text.delete("1.0", END)
    text.insert(END, msg)
    text.config(state=DISABLED)

# ---------- button callbacks ----------
def ask():
    set_text("Listening... please speak.")
    entry.delete(0, END)

    def _listen():
        voice = speech_to_text()
        entry.delete(0, END)
        entry.insert(0, voice if voice not in ("timeout","unknown","request_error") else "")
        reply = action(voice)
        set_text(reply)

    threading.Thread(target=_listen, daemon=True).start()

def del_text():
    entry.delete(0, END)
    text.config(state=NORMAL)
    text.delete("1.0", END)
    text.config(state=DISABLED)

def send(event=None):
    user_input = entry.get().strip()
    if not user_input:
        set_text("Please type something first.")
        return
    set_text("Thinking...")
    entry.delete(0, END)

    def _respond():
        reply = action(user_input)   # action() already calls text_to_speech inside
        set_text(reply)

    threading.Thread(target=_respond, daemon=True).start()

# ---------- layout ----------
frame = LabelFrame(root, padx=100, pady=7, borderwidth=3, relief="raised")
frame.config(bg="#0b0e0d")
frame.grid(row=0, column=1, padx=95, pady=10)

text_lable = Label(
    frame,
    text="RUBI",
    font=("comic sans ms", 14, "bold"),
    bg="#00fa9a"
)
text_lable.grid(row=0, column=0, padx=20, pady=10)

# ---- Google Drive image (unchanged) ----
file_id = "1AQ-PUQHT20vSgEgpqlgcyLuoF7HrVMCN"
url = f"https://drive.google.com/uc?export=download&id={file_id}"
try:
    response_img = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=8)
    img = Image.open(BytesIO(response_img.content))
    img = img.resize((150, 150))
    photo = ImageTk.PhotoImage(img)
    image_label = Label(frame, image=photo)
    image_label.image = photo
    image_label.grid(row=1, column=0, pady=20)
except Exception:
    Label(frame, text="[image]", bg="#0b0e0d", fg="#00fa9a").grid(row=1, column=0, pady=20)

# ---- text display (larger box with scrollbar & word wrap) ----
text_frame = Frame(root, bg="#0d1a16")
text_frame.place(x=55, y=295, width=435, height=185)

scrollbar = Scrollbar(text_frame)
scrollbar.pack(side=RIGHT, fill=Y)

text = Text(
    text_frame,
    font=('courier 10 bold'),
    bg="#00fa9a",
    fg="#0d1a16",
    wrap=WORD,                  # word wrap so long answers don't get cut
    relief=FLAT,
    padx=8,
    pady=6,
    yscrollcommand=scrollbar.set
)
text.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.config(command=text.yview)
text.config(state=DISABLED)

# ---- entry ----
entry = Entry(root, justify=CENTER, font=('courier 10 bold'))
entry.place(x=95, y=498, width=350, height=30)
entry.bind("<Return>", send)   # Enter key triggers send

# ---- buttons ----
Button1 = Button(root, text="ASK",    bg="#35A000", pady=16, padx=40, borderwidth=3, relief=SOLID, command=ask)
Button1.place(x=70,  y=550)

Button2 = Button(root, text="DELETE", bg="#35A000", pady=16, padx=40, borderwidth=3, relief=SOLID, command=del_text)
Button2.place(x=200, y=550)

Button3 = Button(root, text="SEND",   bg="#35A000", pady=16, padx=40, borderwidth=3, relief=SOLID, command=send)
Button3.place(x=350, y=550)

root.mainloop()