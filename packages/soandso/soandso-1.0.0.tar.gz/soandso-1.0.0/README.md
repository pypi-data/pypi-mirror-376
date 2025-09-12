# soandso

A delightfully arbitrary collection of Python utilities that do things, other things, and something else entirely.

## Installation
```bash
pip install soandso
```

## Usage
```python
from soandso import do_a_thing, do_another_thing, do_something_else
from soandso import make_it_fancy, count_stuff, generate_nonsense

# Do a thing
result = do_a_thing("laundry")
print(result)  # "Successfully did laundry! ✨"

# Do another thing with intensity
result = do_another_thing(8)
print(result)  # {'thing_done': True, 'intensity_level': 8, ...}

# Do something else with a list
items = ["apple", "banana", "cherry"]
result = do_something_else(items)
print(result)  # ["🎭 apple (processed)", ...]

# Make text fancy
fancy = make_it_fancy("hello world", "sparkles")
print(fancy)  # "✨ ⭐ HELLO WORLD ⭐ ✨"

# Count stuff
counts = count_stuff("hello world")
print(counts)  # {'total': 11, 'without_spaces': 10, ...}

# Generate nonsense
nonsense = generate_nonsense(5)
print(nonsense)  # "flibber jabberwocky snurfle blimp woosh"
```

