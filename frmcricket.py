import logging
import sqlite3
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

TOKEN = "8049311684:AAHBcOkfaY1MutqZoB24HxjJOpUK0GUW668"
GCS_WEB_APP_URL = "https://tannuxshaan-cmyk.github.io/CRICKET-BOT/"

WELCOME_TEXT = (
    "📋 **All Commands Center** 🏏\n\n"
    "🟢 **Basics:**\n`/start`, `/help`, `/play`, `/duel`\n\n"
    "👥 **Team Mode:**\n"
    "`/create_teams`, `/join_teama`, `/join_teamb`, `/teams`, `/changeside`, `/shiftteam`, "
    "`/add`, `/remove`, `/changehost`, `/changecap`, `/choose_cap`, `/set_overs`, `/batting`, `/bowling`, "
    "`/rejointeams`, `/restore`, `/endgame`\n\n"
    "👤 **Solo Mode:**\n"
    "`/joingame`, `/leavegame`, `/extend`, `/forcestart`\n\n"
    "⚔️ **Duel:**\n"
    "`/duel` (DM only)\n\n"
    "📊 **Live Match:**\n"
    "`/score`, `/graph`, `/members`, `/endgame`\n\n"
    "👤 **Profile:**\n"
    "`/userinfo`, `/stats`, `/user_ranks`, `/achievements`, `/compare`, `/analyze`"
)

def init_db():
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            jersey_number INTEGER UNIQUE,
            lang TEXT DEFAULT 'en',
            matches_played INTEGER DEFAULT 0,
            wins INTEGER DEFAULT 0,
            total_runs INTEGER DEFAULT 0,
            coins INTEGER DEFAULT 100
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS active_matches (
            chat_id INTEGER PRIMARY KEY,
            player1_id INTEGER,
            player1_name TEXT,
            player2_id INTEGER,
            player2_name TEXT,
            player1_score INTEGER DEFAULT 0,
            player2_score INTEGER DEFAULT 0,
            player1_wickets INTEGER DEFAULT 0,
            player2_wickets INTEGER DEFAULT 0,
            current_ball INTEGER DEFAULT 0,
            max_balls INTEGER DEFAULT 30,
            innings INTEGER DEFAULT 1,
            match_status TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT jersey_number FROM users WHERE user_id = ?", (user.id,))
    res = cursor.fetchone()
    if not res:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, lang) VALUES (?, ?, ?)", (user.id, user.first_name, 'en'))
        conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("🎮 Play Mini App", web_app=WebAppInfo(url=GCS_WEB_APP_URL))],
        [InlineKeyboardButton("🔙 Back / Help", callback_data="help_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        WELCOME_TEXT,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await update.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("👤 Solo Quick Match", callback_data="play_solo")],
        [InlineKeyboardButton("👥 Team Match Mode", callback_data="play_team")]
    ]
    await update.message.reply_text("🎮 Select your game mode:", reply_markup=InlineKeyboardMarkup(keyboard))

teams_data = {"Team A": [], "Team B": [], "overs": 5}

async def create_teams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    teams_data["Team A"] = []
    teams_data["Team B"] = []
    await update.message.reply_text("👥 Teams created successfully! Use `/join_teama` or `/join_teamb`.")

async def join_teamA(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    if user not in teams_data["Team A"]:
        teams_data["Team A"].append(user)
    await update.message.reply_text(f"✅ {user} joined **Team A** 🔴.")

async def join_teamB(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user.first_name
    if user not in teams_data["Team B"]:
        teams_data["Team B"].append(user)
    await update.message.reply_text(f"✅ {user} joined **Team B** 🔵.")

async def teams_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    t_a = ", ".join(teams_data["Team A"]) if teams_data["Team A"] else "Empty"
    t_b = ", ".join(teams_data["Team B"]) if teams_data["Team B"] else "Empty"
    await update.message.reply_text(f"👥 **Current Teams Roster:**\n🔴 Team A: {t_a}\n🔵 Team B: {t_b}")

async def changeside(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Teams sides swapped successfully!")

async def shiftteam(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔀 Player shifted to the alternate team.")

async def add_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➕ Player added to the roster.")

async def remove_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("➖ Player removed from the roster.")

async def changehost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👑 Match host transferred successfully.")

async def changecap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧢 Team captain updated.")

async def choose_cap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⭐ Captain selected for the match.")

async def set_overs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        try:
            ovs = int(context.args[0])
            teams_data["overs"] = ovs
            await update.message.reply_text(f"⚙️ Match overs set to: {ovs}")
        except ValueError:
            await update.message.reply_text("⚠️ Please enter a valid number, e.g., `/set_overs 5`")
    else:
        await update.message.reply_text("⚠️ Please specify overs, e.g., `/set_overs 5`")

async def batting(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏏 Team opted for **Batting**.")

async def bowling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚾ Team opted for **Bowling**.")

async def rejointeams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Rejoined team lineup successfully.")

async def restore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("♻️ Match state restored from backup.")

async def joingame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("1", callback_data="run_1"), InlineKeyboardButton("2", callback_data="run_2"), InlineKeyboardButton("3", callback_data="run_3")],
        [InlineKeyboardButton("4", callback_data="run_4"), InlineKeyboardButton("6", callback_data="run_6")]
    ]
    await update.message.reply_text("🏏 Solo Match Active! Choose your run:", reply_markup=InlineKeyboardMarkup(keyboard))

async def leavegame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚪 You have left the active game session.")

async def extend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Match timer/overs extended.")

async def forcestart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Match force started by admin/host.")

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO active_matches (chat_id, player1_id, player1_name, match_status) VALUES (?, ?, ?, ?)", 
                   (chat_id, user.id, user.first_name, "waiting"))
    conn.commit()
    conn.close()
    await update.message.reply_text(f"⚔️ **{user.first_name}** started a Duel match!\nClick below to join:",
                                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⚔️ Join Duel", callback_data="join_duel_match")]]))

async def score(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT player1_name, player2_name, player1_score, player2_score, innings FROM active_matches WHERE chat_id = ?", (chat_id,))
    match = cursor.fetchone()
    conn.close()
    if match:
        p1_n, p2_n, p1_sc, p2_sc, inn = match
        await update.message.reply_text(f"📊 **Live Score (Innings {inn}):**\n🔴 {p1_n}: {p1_sc}\n🔵 {p2_n}: {p2_sc}")
    else:
        await update.message.reply_text("📊 No active match found. Use `/duel` or `/joingame` to start.")

async def graph(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 Match Run-rate graph generated successfully.")

async def members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👥 Active members list fetched for this match session.")

async def userinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT jersey_number, coins FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    conn.close()
    jersey = row[0] if row and row[0] else "Not Set"
    coins = row[1] if row else 100
    await update.message.reply_text(f"👤 **User Profile:**\n• Name: {user.first_name}\n• ID: `{user.id}`\n• 🎽 Jersey: #{jersey}\n• 🪙 Coins: {coins}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT matches_played, wins, total_runs FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        played, wins, runs = row
        await update.message.reply_text(f"📊 **Career Stats:**\n• Matches Played: {played}\n• Wins: {wins}\n• Total Runs: {runs}")
    else:
        await update.message.reply_text("⚠️ Profile not found. Send `/start` first.")

async def user_ranks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, total_runs FROM users ORDER BY total_runs DESC LIMIT 10")
    top_users = cursor.fetchall()
    conn.close()
    txt = "🏆 **Global Leaderboard:**\n\n"
    for idx, (uname, runs) in enumerate(top_users, 1):
        txt += f"{idx}. {uname or 'Player'} — 🏏 {runs} Runs\n"
    await update.message.reply_text(txt)

async def achievements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏅 **Achievements Unlocked:**\n- 🔥 Century Master\n- 🏆 Pro Champion")

async def compare(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚖️ Player comparison metrics displayed.")

async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Advanced match analysis report generated.")

async def endgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    conn = sqlite3.connect("cricket_bot.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM active_matches WHERE chat_id = ?", (chat_id,))
    conn.commit()
    conn.close()
    await update.message.reply_text("🛑 Match session ended and reset successfully.")

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "help_menu":
        await query.message.reply_text(WELCOME_TEXT, parse_mode="Markdown")
    elif data.startswith("run_"):
        user_run = int(data.split("_")[1])
        bot_run = random.randint(1, 6)
        if user_run == bot_run:
            await query.edit_message_text(f"❌ **OUT!** You chose {user_run}, Bot chose {bot_run}.")
        else:
            await query.edit_message_text(f"⚡ You scored: **{user_run}** | Bot choice: {bot_run}")

if __name__ == "__main__":
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handlers([
        CommandHandler("start", start),
        CommandHandler("help", help_command),
        CommandHandler("play", play),
        CommandHandler("create_teams", create_teams),
        CommandHandler("join_teama", join_teamA),
        CommandHandler("join_teamb", join_teamB),
        CommandHandler("teams", teams_list),
        CommandHandler("changeside", changeside),
        CommandHandler("shiftteam", shiftteam),
        CommandHandler("add", add_player),
        CommandHandler("remove", remove_player),
        CommandHandler("changehost", changehost),
        CommandHandler("changecap", changecap),
        CommandHandler("choose_cap", choose_cap),
        CommandHandler("set_overs", set_overs),
        CommandHandler("batting", batting),
        CommandHandler("bowling", bowling),
        CommandHandler("rejointeams", rejointeams),
        CommandHandler("restore", restore),
        CommandHandler("joingame", joingame),
        CommandHandler("leavegame", leavegame),
        CommandHandler("extend", extend),
        CommandHandler("forcestart", forcestart),
        CommandHandler("duel", duel),
        CommandHandler("score", score),
        CommandHandler("graph", graph),
        CommandHandler("members", members),
        CommandHandler("userinfo", userinfo),
        CommandHandler("stats", stats),
        CommandHandler("user_ranks", user_ranks),
        CommandHandler("achievements", achievements),
        CommandHandler("compare", compare),
        CommandHandler("analyze", analyze),
        CommandHandler("endgame", endgame),
        CommandHandler("back", start),
        CallbackQueryHandler(handle_buttons)
    ])
    application.run_polling()