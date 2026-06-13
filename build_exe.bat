uv sync
uvx pyinstaller --onefile --nowindow --clean --paths .\.venv\Lib\site-packages\ --add-data "icon.ico;." --icon "icon.ico" --noconsole --name "RL Music Muter" .\main.py