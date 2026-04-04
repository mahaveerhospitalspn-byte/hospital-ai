Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd C:\Users\admin\Desktop\Hospital_AI && streamlit run app.py", 0
Set WshShell = Nothing