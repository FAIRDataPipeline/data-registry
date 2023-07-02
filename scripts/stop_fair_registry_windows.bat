@ECHO OFF            

echo Getting Process ID
                                                                  
FOR /F %%T IN ('wmic process where "commandline like '%%manage.py%%runserver%%'" get processid^|more +1') DO (
SET /A ProcessId=%%T) &GOTO SkipLine                                                   
:SkipLine                                                                              
echo Stopping ProcessId = %ProcessId%   

taskkill /F /PID %ProcessId% /t 2> nul