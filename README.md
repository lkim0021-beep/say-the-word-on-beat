# Say the Word on Beat Generator

A local Windows prototype for making rhythm-card videos from your own pictures, words and music. Built with Python, Pillow, a browser interface and FFmpeg. The interface is currently in Russian.

## Features

- 1920×1080 MP4 export, 30 fps, H.264 video and AAC audio.
- Eight cards in a 4×2 grid: sequential reveal, beat-based highlighting and a small pulse.
- Easy, Normal, Hard, Expert and Insane levels with configurable beats per card.
- Countdown, level titles and optional fade transitions.
- Paper, Night and Candy themes, custom backgrounds, accent colors and two moving stickers.
- Audio preview, pause and timeline seeking.
- Local processing: media is sent to the app on your computer, not to an external service.

## Windows quick start

1. Install **Python 3.11 or newer** from [python.org](https://www.python.org/downloads/windows/). Enable **Add python.exe to PATH**.
2. Download this repository using **Code → Download ZIP** and extract it.
3. Double-click **START.cmd**. The first launch creates `.venv` and downloads dependencies, including an FFmpeg build through imageio-ffmpeg. Internet access is needed for this installation.
4. Open **http://127.0.0.1:8766** if your browser does not open automatically. Keep the terminal window open.
5. Click **Заполнить тестовыми файлами** to try original generated demo assets, then **Подготовить предпросмотр** and **Смотреть с музыкой**.
6. Click **Экспорт MP4**, wait for completion and select **Скачать MP4**.

For your own project, load eight PNG/JPEG/WebP images, enter their words and choose browser-compatible audio such as WAV or MP3. Transparent PNG stickers are supported. Close the terminal window to stop the server.

Manual setup in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Timing

BPM is manual; the tap button estimates it from your clicks. The offset is the start position in the original audio, including the countdown. Grid mode has a three-beat countdown, a two-beat title per level, eight reveals and eight highlights per level. At 120 BPM the defaults produce 10.5 seconds for Easy or 36.5 seconds for all five levels. Boundaries are rounded to the nearest 30 fps frame.

The same eight cards repeat on each level. Multiple rounds and different card combinations within a level are not implemented yet. Short audio is padded with silence during export.

## Current limits

This is an early prototype, not a hosted production service. Windows and its Arial font are currently required. There is no automatic beat detection, project save/load, export cancellation or direct CapCut integration. Browser text rendering may differ slightly from exported text. Changing inputs requires preparing the preview again; refreshing the page clears selections.

The server binds only to `127.0.0.1`. Do not expose it to the internet or forward its port. It has no multi-user authentication. Uploaded copies and rendered videos remain in `data/`; delete unwanted job folders when the app is stopped. The upload request limit is 150 MiB including JSON/base64 overhead (roughly 110 MiB of files). One export runs at a time.

## Development and testing

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests create temporary media, check timing, transitions, transparent stickers and a short real FFmpeg export. CI is configured for Windows. A successful local test is not evidence that hosted CI has run.

Contributions and genuine user feedback are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and [ROADMAP.md](ROADMAP.md).

## License and media

Original project code is available under the [MIT License](LICENSE). See [THIRD_PARTY.md](THIRD_PARTY.md) for dependencies. FFmpeg binaries, uploaded files and reference videos are **not included** in this repository. Demo cards and metronome audio are generated locally from project code. Use media you are permitted to use and distribute.

This project was developed with assistance from Codex. It is independent and is not endorsed by OpenAI. It currently requires no OpenAI API key or paid AI service to generate videos.

## Кратко по-русски

Установите Python 3.11+, распакуйте проект и запустите `START.cmd`. В первый раз установятся зависимости. Затем откройте http://127.0.0.1:8766. Загрузите музыку и 8 картинок, задайте BPM, выберите оформление, подготовьте предпросмотр и экспортируйте MP4. Для теста есть кнопка «Заполнить тестовыми файлами». Это ранняя версия: сохранения проекта и автоматического распознавания битов пока нет.
