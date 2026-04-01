# feature/keyboard-builder

Adds a fluent `Keyboard` builder for composing inline/reply button layouts
in a readable, chainable style.

## Import

```python
from telethon import Keyboard
# or
from telethon.tl.custom import Keyboard
```

## Row-by-row layout

```python
keyboard = (
    Keyboard()
    .row(Keyboard.inline("Yes", b"yes"), Keyboard.inline("No", b"no"))
    .row(Keyboard.inline("Cancel", b"cancel"))
    .build()
)
await client.send_message(chat, "Choose:", buttons=keyboard)
```

## Auto-grid layout

Reflow a flat list into rows of N columns automatically:

```python
fruits = ["Apple", "Banana", "Cherry", "Date", "Elderberry"]
keyboard = Keyboard().columns(
    [Keyboard.inline(f, f.lower().encode()) for f in fruits],
    cols=2,
).build()
```

## Manual append + row break

```python
kb = Keyboard()
for i in range(1, 7):
    kb.add(Keyboard.inline(str(i), str(i).encode()))
    if i % 3 == 0:
        kb.end_row()
keyboard = kb.build()
```

## Static helpers

| Method | Returns |
|---|---|
| `Keyboard.inline(text, data)` | Inline callback button with `bytes` payload |
| `Keyboard.text(label)` | Reply keyboard text button |

## `.build()` return value

`list[list[Button]]` — accepted by Telethon's `buttons=` parameter everywhere:
`send_message`, `edit_message`, `respond`, etc.

## Method chaining

All builder methods return `self`:

```python
keyboard = Keyboard().row(...).row(...).build()
```
