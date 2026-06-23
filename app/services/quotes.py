import random

QUOTES = {
    "fitness": [
        "The body achieves what the mind believes.",
        "No pain, no gain. Shut up and train.",
        "Your body can stand almost anything. It's your mind you have to convince.",
        "The only bad workout is the one that didn't happen.",
        "Sweat is just fat crying.",
        "Train insane or remain the same.",
        "The clock is ticking. Are you becoming the person you want to be?",
        "One year from now you'll wish you had started today.",
        "Strive for progress, not perfection.",
        "Your future self is watching you right now through your memories.",
        "The difference between try and triumph is just a little umph.",
        "Don't wish for it. Work for it.",
        "Push yourself because no one else is going to do it for you.",
        "Success starts with self-discipline.",
        "The pain you feel today will be the strength you feel tomorrow.",
    ],
    "finance": [
        "Do not save what is left after spending. Spend what is left after saving.",
        "A penny saved is a penny earned.",
        "Financial freedom is available to those who learn about it and work for it.",
        "The secret to wealth is simple: spend less than you make and invest the rest.",
        "Rich people have small TVs and big libraries. Poor people have big TVs and small libraries.",
        "Don't tell me what you value. Show me your budget and I'll tell you.",
        "You must gain control over your money or the lack of it will forever control you.",
        "An investment in knowledge pays the best interest.",
        "It's not your salary that makes you rich. It's your spending habits.",
        "Every pound you save is a vote for your future self.",
    ],
    "career": [
        "Opportunities don't happen. You create them.",
        "The secret of getting ahead is getting started.",
        "Don't watch the clock. Do what it does — keep going.",
        "Success is not in what you have, but who you are.",
        "Hard work beats talent when talent doesn't work hard.",
        "The only place where success comes before work is in the dictionary.",
        "If you are not willing to risk the usual, you will have to settle for the ordinary.",
        "Great things never come from comfort zones.",
        "Dream big. Start small. Act now.",
        "Your time is limited. Don't waste it living someone else's life.",
    ],
    "wellness": [
        "You can't pour from an empty cup. Take care of yourself first.",
        "Mental health is not a destination but a process.",
        "Almost everything will work again if you unplug it for a few minutes — including you.",
        "Self-care is not selfish. You cannot serve from an empty vessel.",
        "The mind is everything. What you think, you become.",
        "Be gentle with yourself. You are a child of the universe.",
        "Progress is progress no matter how small.",
        "You don't have to be positive all the time. It's perfectly okay to feel sad, angry, annoyed.",
        "Healing is not linear.",
        "Take it one day at a time.",
    ],
    "general": [
        "If you always do what you've always done, you'll always get what you've always got.",
        "The man who moves a mountain begins by carrying away small stones.",
        "A year from now you may wish you had started today.",
        "You don't have to be great to start, but you have to start to be great.",
        "Discipline is choosing between what you want now and what you want most.",
        "Small daily improvements over time lead to stunning results.",
        "The secret of your future is hidden in your daily routine.",
        "Success is the sum of small efforts repeated day in and day out.",
        "We are what we repeatedly do. Excellence, then, is not an act, but a habit.",
        "Either you run the day or the day runs you.",
        "You are one decision away from a completely different life.",
        "Don't count the days. Make the days count.",
        "The two most important days in your life are the day you're born and the day you find out why.",
        "It always seems impossible until it's done.",
        "Done is better than perfect.",
        "Start where you are. Use what you have. Do what you can.",
        "The hard days are what make you stronger.",
        "Believe you can and you're halfway there.",
        "Act as if what you do makes a difference. It does.",
        "What you get by achieving your goals is not as important as what you become.",
    ],
}

MOTIVATION_IMAGES = {
    "fitness": [
        "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=800",
        "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=800",
        "https://images.unsplash.com/photo-1583454110551-21f2fa2afe61?w=800",
        "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=800",
        "https://images.unsplash.com/photo-1526506118085-60ce8714f8c5?w=800",
    ],
    "finance": [
        "https://images.unsplash.com/photo-1579621970563-ebec7560ff3e?w=800",
        "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?w=800",
        "https://images.unsplash.com/photo-1559526324-4b87b5e36e44?w=800",
    ],
    "career": [
        "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=800",
        "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=800",
        "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=800",
    ],
    "wellness": [
        "https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=800",
        "https://images.unsplash.com/photo-1545389336-cf090694435e?w=800",
        "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=800",
    ],
    "general": [
        "https://images.unsplash.com/photo-1499728603263-13726abce5fd?w=800",
        "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?w=800",
        "https://images.unsplash.com/photo-1488190211105-8b0e65b80b4e?w=800",
        "https://images.unsplash.com/photo-1464820453369-31d2c0b651af?w=800",
    ],
}


def get_quote(category: str, exclude_recent: list = None) -> str:
    pool = QUOTES.get(category, QUOTES["general"]) + QUOTES["general"]
    available = [q for q in pool if q not in (exclude_recent or [])]
    if not available:
        available = pool
    return random.choice(available)


def get_motivation_image(category: str) -> str:
    images = MOTIVATION_IMAGES.get(category, MOTIVATION_IMAGES["general"])
    return random.choice(images)
