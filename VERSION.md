
# RUN
pip install -r requirements.txt



# RECOVERY
git log --oneline -n 5

Copy-Item .env $env:TEMP\.env.backup
git reset --hard 80f714fc
git clean -fd
Copy-Item $env:TEMP\.env.backup .env -Force
git push origin master --force
python run.py

# UPDATE
git add .
git commit -m "v0.0.5 - обновлен README.md"
git push


# DEV LOG
v0.0.1 - Настройка кликов
v0.0.2 - добавлен setup для каждой из папок
v0.0.3 - добавлена и проверенна автоматизация
v0.0.4 - полностью проверенная автоматизация, сахранение перед переносом на laptopmini
v0.0.5 - обновлен README.md