@ECHO OFF            

echo Getting Process ID
                                                                  
FOR /F %%T IN ('Wmic process where^(CommandLine like "%%manage.py runserver%%"^)get ProcessId^|more +1') DO (
SET /A ProcessId=%%T) &GOTO SkipLine                                                   
:SkipLine                                                                              
echo Stopping ProcessId = %ProcessId%   

taskkill /F /PID %ProcessId% /t