from datetime import datetime, timedelta

def format_signal_text(sig: dict):
    # convert UTC to EAT (UTC+3) for display
    eat = datetime.utcnow() + timedelta(hours=3)
    return (
        f"*{sig['pair']}* — {sig['interval']}\n"
        f"Signal: *{sig['signal']}*\n"
        f"Entry: `{sig['entry']:.5f}`\n"
        f"Stop: `{sig['stop']:.5f}`\n"
        f"TP: `{sig['tp']:.5f}`\n"
        f"Confidence: `{sig['confidence']:.1f}%`\n"
        f"Time (EAT): {eat.strftime('%H:%M')}"
    )