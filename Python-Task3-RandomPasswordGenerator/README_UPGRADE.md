# Random Password Generator — Upgrade Notes

## What is improved
- Password generation lives in `password_engine.py`, independently testable from Tkinter.
- Uses Python's `secrets` module.
- Validates length and character-group choices.
- Guarantees at least one character from each selected group.
- Provides a documented entropy estimate and a clearly labelled heuristic.

## Run tests
```powershell
python -m unittest -v test_password_engine.py
```

## Integration note
Keep the current GUI while testing. Replace its generation logic with `PasswordOptions(...)` and `generate_password(options)` only after the unit tests pass. Avoid displaying saved passwords in history by default; consider reveal-on-demand, a clear-history button, and making clipboard copying an explicit user action.
