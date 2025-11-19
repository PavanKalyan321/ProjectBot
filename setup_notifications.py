"""
Setup Mobile Notifications
Configure Telegram, Discord, or Pushover for alerts
"""

def setup_telegram():
    print("🤖 TELEGRAM SETUP")
    print("1. Message @BotFather on Telegram")
    print("2. Create new bot: /newbot")
    print("3. Get your bot token")
    print("4. Start chat with your bot")
    print("5. Get chat ID from: https://api.telegram.org/bot<TOKEN>/getUpdates")
    
    token = input("\nEnter bot token: ").strip()
    chat_id = input("Enter chat ID: ").strip()
    
    return f"""
# Add to bot_modular.py main():
bot.mobile_notifier.setup_telegram("{token}", "{chat_id}")
"""

def setup_discord():
    print("💬 DISCORD SETUP")
    print("1. Go to Discord server settings")
    print("2. Integrations > Webhooks")
    print("3. Create webhook")
    print("4. Copy webhook URL")
    
    webhook = input("\nEnter webhook URL: ").strip()
    
    return f"""
# Add to bot_modular.py main():
bot.mobile_notifier.setup_discord("{webhook}")
"""

def setup_pushover():
    print("📱 PUSHOVER SETUP")
    print("1. Sign up at pushover.net")
    print("2. Create application")
    print("3. Get app token and user key")
    
    token = input("\nEnter app token: ").strip()
    user = input("Enter user key: ").strip()
    
    return f"""
# Add to bot_modular.py main():
bot.mobile_notifier.setup_pushover("{token}", "{user}")
"""

def main():
    print("="*50)
    print("📱 MOBILE NOTIFICATIONS SETUP")
    print("="*50)
    
    print("\nChoose notification method:")
    print("1. Telegram (Free)")
    print("2. Discord (Free)")
    print("3. Pushover ($5 one-time)")
    
    choice = input("\nChoice (1/2/3): ").strip()
    
    if choice == "1":
        code = setup_telegram()
    elif choice == "2":
        code = setup_discord()
    elif choice == "3":
        code = setup_pushover()
    else:
        print("Invalid choice")
        return
    
    print("\n" + "="*50)
    print("✅ SETUP COMPLETE!")
    print("="*50)
    print("\nAdd this code to your bot:")
    print(code)
    print("\nYou'll receive alerts when high multiplier sequences are predicted!")

if __name__ == "__main__":
    main()