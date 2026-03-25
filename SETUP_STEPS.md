
<!-- -------get pc with windows---------------------- -->
For 1 strategy only, need 1 PC with "any windows"
<!-- -------on windows server------------------------ -->
enable remote desktop in "Remote Desctop Settings"
inside CMD, check ip using "ipconfig" example 10.0.0.26
<!-- -------use master PC to connect via RDP--------- -->
connect to ip using "RDP"
<!-- -------config windows server-------------------- -->
turn off windows updates in windows settings
turn off windows notifications in windows settings
turn off sleep mode in windows settings
move "start menu" to left, inside windows settings
<!-- -------config browser--------------------------- -->
save bookmark https://pancakeswap.finance/prediction?token=BNB&chain=bsc
install metamask extention https://metamask.io/download
pin metamask extention to browser
<!-- -------install project--------------------------- -->
create folder on desktop with all files of the project
open project folder using cmd
winget install -e --id Python.Python.3.11
after python instalation, open new cmd tab to make installation complete
python.exe -m pip install --upgrade pip
pip install -r requirements.txt
after python instalation, open new cmd tab to make installation complete
<!-- -------config strategy--------------------------- -->
open project SETTINGS.py in notepad and config strategy settings
<!-- -------config clicks--------------------------- -->
open "BACKEND\Y_DATA\B_flow.yaml"
config each one who have "monitor=" using "python BACKEND/setup.py" for each one 
copy result from "PIXEL_CONFIG" to each one of them
<!-- -------run project--------------------------- -->
in cmd run project "python run.py"
<!-- ------- make sure all works before leave -->
before you leave it alone 
make sure it collecting winnings
just wait until you see all works fine
then you can leave this windows user alone
<!-- -------you can go to sleep------------------- -->





