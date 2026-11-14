# Food Picture 01

This is a fresh Codex rebuild for the make.fun food-picture-01 entry. The bundled `food.jpg` is original AI-generated food artwork created outside the Codex coding session.

The repository includes `food.jpg`; you may replace it with original artwork saved as `food.jpg` or `food.png`. Run:

```sh
python3 main.py
```

The program copies the selected file byte for byte to `/output/entry.png`. Set `MAKEFUN_OUTPUT_DIR` to use another output directory. JPEG bytes under the `entry.png` filename are permitted. The entrypoint checks the file signature, dimensions (at most 1024 by 1024), and size (at most 1 MiB) before writing.

This repository makes no claim of submission or winning.
