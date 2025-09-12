"""
Utility functions for the soandso package
"""

import random
import string
from typing import Any, Union


def make_it_fancy(text: str, style: str = "sparkles") -> str:
    """
    Makes any text fancy with decorative elements.
    
    Args:
        text (str): Text to make fancy
        style (str): Style of fanciness ("sparkles", "borders", "caps")
        
    Returns:
        str: Fancified text
        
    Example:
        >>> make_it_fancy("hello", "sparkles")
        "✨ ⭐ HELLO ⭐ ✨"
    """
    styles = {
        "sparkles": lambda t: f"✨ ⭐ {t.upper()} ⭐ ✨",
        "borders": lambda t: f"╔═══ {t} ═══╗",
        "caps": lambda t: f"🔥 {t.upper()} 🔥",
        "waves": lambda t: f"〜(￣▽￣)〜 {t} 〜(￣▽￣)〜"
    }
    
    if style not in styles:
        style = "sparkles"
    
    return styles[style](text)


def count_stuff(stuff: Any, what_to_count: str = "characters") -> dict:
    """
    Counts various aspects of stuff.
    
    Args:
        stuff (Any): The stuff to count
        what_to_count (str): What aspect to count
        
    Returns:
        dict: Counting results
        
    Example:
        >>> count_stuff("hello world", "characters")
        {'total': 11, 'without_spaces': 10, 'words': 2, 'unique_chars': 9}
    """
    stuff_str = str(stuff)
    
    counts = {
        "total": len(stuff_str),
        "without_spaces": len(stuff_str.replace(" ", "")),
        "words": len(stuff_str.split()) if stuff_str.strip() else 0,
        "unique_chars": len(set(stuff_str.lower())),
        "vowels": sum(1 for char in stuff_str.lower() if char in "aeiou"),
        "consonants": sum(1 for char in stuff_str.lower() if char.isalpha() and char not in "aeiou")
    }
    
    if what_to_count == "characters":
        return {k: v for k, v in counts.items() if "char" in k or k in ["total", "without_spaces", "unique_chars"]}
    elif what_to_count == "words":
        return {"words": counts["words"], "avg_word_length": counts["without_spaces"] / max(1, counts["words"])}
    else:
        return counts


def generate_nonsense(length: int = 10, include_numbers: bool = False) -> str:
    """
    Generates delightful nonsense text.
    
    Args:
        length (int): Length of nonsense to generate
        include_numbers (bool): Whether to include numbers
        
    Returns:
        str: Pure, unadulterated nonsense
        
    Example:
        >>> generate_nonsense(5)
        "flibber jabberwocky snurfle blimp woosh"
    """
    nonsense_words = [
        "flibber", "jabberwocky", "snurfle", "blimp", "woosh", "zibble",
        "plonk", "squish", "boing", "whiffle", "sproink", "glitch",
        "bonkers", "wiggle", "splendid", "nifty", "zippy", "groovy"
    ]
    
    result = []
    for _ in range(length):
        word = random.choice(nonsense_words)
        if include_numbers and random.random() < 0.3:
            word += str(random.randint(1, 99))
        result.append(word)
    
    return " ".join(result)