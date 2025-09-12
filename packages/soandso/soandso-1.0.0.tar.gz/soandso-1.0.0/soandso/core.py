"""
Core functionality for the soandso package
"""

import random
import time
from typing import Any, List, Dict


def do_a_thing(thing: str = "mysterious task") -> str:
    """
    Does a thing. What thing? That's up to interpretation.
    
    Args:
        thing (str): The thing to do (default: "mysterious task")
        
    Returns:
        str: A confirmation that the thing was done
        
    Example:
        >>> do_a_thing("laundry")
        "Successfully did laundry! ✨"
    """
    emojis = ["✨", "🎯", "🚀", "⚡", "🎉", "💫", "🔥"]
    return f"Successfully did {thing}! {random.choice(emojis)}"


def do_another_thing(intensity: int = 5) -> Dict[str, Any]:
    """
    Does another thing, but with measurable intensity.
    
    Args:
        intensity (int): How intensely to do the thing (1-10)
        
    Returns:
        dict: Results of doing the thing
        
    Example:
        >>> do_another_thing(8)
        {'thing_done': True, 'intensity_level': 8, 'satisfaction': 'high', 'time_taken': 0.8}
    """
    intensity = max(1, min(10, intensity))  # Clamp between 1-10
    
    satisfaction_levels = {
        range(1, 4): "low",
        range(4, 7): "medium", 
        range(7, 11): "high"
    }
    
    satisfaction = next(level for r, level in satisfaction_levels.items() if intensity in r)
    time_taken = intensity * 0.1
    
    time.sleep(min(0.1, time_taken))
    
    return {
        "thing_done": True,
        "intensity_level": intensity,
        "satisfaction": satisfaction,
        "time_taken": time_taken,
        "bonus_points": intensity * 10 if intensity >= 8 else 0
    }


def do_something_else(items: List[str], shuffle: bool = True) -> List[str]:
    """
    Does something else entirely with a list of items.
    
    Args:
        items (List[str]): Items to do something with
        shuffle (bool): Whether to shuffle the items first
        
    Returns:
        List[str]: The items, but with something done to them
        
    Example:
        >>> do_something_else(["apple", "banana"])
        ["🎭 apple (processed)", "🎭 banana (processed)"]
    """
    if not items:
        return ["Nothing to do something else with! 🤷‍♂️"]
    
    processed_items = items.copy()
    
    if shuffle:
        random.shuffle(processed_items)
    
    # Do something mysterious to each item
    result = []
    for item in processed_items:
        processed = f"🎭 {item} (processed)"
        result.append(processed)
    
    return result