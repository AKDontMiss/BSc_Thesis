@echo off
set config_file="client.conf"
set output_file=%1.ovpn
type %config_file% > %output_file%
echo ^<ca^> >> %output_file%
type pki\ca.crt >> %output_file%
echo ^</ca^> >> %output_file%
echo ^<tls-auth^> >> %output_file%
type ..\bin\ta.key >> %output_file%
echo ^</tls-auth^> >> %output_file%
echo ^<cert^> >> %output_file%
type pki\issued\%1.crt >> %output_file%
echo ^</cert^> >> %output_file%
echo ^<key^> >> %output_file%
type pki\private\%1.key >> %output_file%
echo ^</key^> >> %output_file%
@echo off
echo Generated:
echo %output_file%
