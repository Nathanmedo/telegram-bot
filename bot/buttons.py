from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .currency import CURRENCY_FLAGS, TRENDING_CURRENCIES


def generate_currency_buttons():
    buttons = []
    for currency in TRENDING_CURRENCIES:
        flag = CURRENCY_FLAGS.get(currency, "")
        buttons.append([InlineKeyboardButton(
            f"{flag} {currency}", callback_data=f"currency:{currency}")])

    buttons.append([InlineKeyboardButton(
        "Back", callback_data="settings:back")])

    return InlineKeyboardMarkup(buttons)


START_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("💰 Deposit", callback_data="deposit"),
        InlineKeyboardButton("📤 Withdraw", callback_data="withdraw")
    ],
    [
        InlineKeyboardButton("⛏️ Trade", callback_data="mine"),
        InlineKeyboardButton("🤖 Upgrade", callback_data="upgrade")
    ],
    [
        InlineKeyboardButton("⚙️ Settings", callback_data="settings"),
        InlineKeyboardButton("ℹ️ About", callback_data="about")
    ]
])

HELP_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('🏘 Home', callback_data='home'),
        InlineKeyboardButton('About 🔰', callback_data='about'),
        InlineKeyboardButton('Settings ⚙️', callback_data='settings')
    ],
    [
        InlineKeyboardButton('Close ✖️', callback_data='close')
    ]
])

ABOUT_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('🏘 Home', callback_data='home'),
        InlineKeyboardButton('Help 🆘', callback_data='help'),
        InlineKeyboardButton('Settings ⚙️', callback_data='settings')
    ],
    [
        InlineKeyboardButton('Close ✖️', callback_data='close')
    ]
])

SETTINGS_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("Change Currency", callback_data="settings:change_currency")
    ],
    [
        InlineKeyboardButton("Close", callback_data="settings:close")
    ]
])

CURRENCY_BUTTONS = generate_currency_buttons()

CLOSE_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton('Close', callback_data='close')]
])

MINING_BUTTONS = InlineKeyboardMarkup([
    [InlineKeyboardButton("⛏️ Start Trading", callback_data="mine")]
])

DEPOSIT_BUTTONS = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("BTC", callback_data="deposit_btc"),
        InlineKeyboardButton("ETH", callback_data="deposit_eth"),
        InlineKeyboardButton("DOGE", callback_data="deposit_doge")
    ],
    [
        InlineKeyboardButton("LTC", callback_data="deposit_ltc"),
        InlineKeyboardButton("DASH", callback_data="deposit_dash"),
        InlineKeyboardButton("ETC", callback_data="deposit_etc")
    ],
    [
        InlineKeyboardButton("BCH", callback_data="deposit_bch"),
        InlineKeyboardButton("SOL", callback_data="deposit_sol"),
        InlineKeyboardButton("⭐️ Stars", callback_data="deposit_stars")
    ],
    [InlineKeyboardButton("❌ Cancel", callback_data="deposit_cancel")]
])

DEPOSIT_CONFIRM_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ Deposit Completed", callback_data="deposit_complete")]
])
