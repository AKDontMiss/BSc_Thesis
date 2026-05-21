# Install openHistorian
1) Download `openHistorian.Installs.zip` from https://github.com/GridProtectionAlliance/openHistorian/releases/

2) Unzip the folder and run the installation wizard

# Install VPN-server
1) Download the Windows 64-bit MSI installer from https://openvpn.net/community-downloads/
2) Run the installation file and select Customize
3) Enable installation of "EasyRSA 3 Certificate Management Scripts"
4) Click "Install Now"
5) After the installation, open PowerShell with **administrative privileges**
6) Go to "C:\Program Files\OpenVPN\bin" and generate a TA-key (this key is secret)
    
    ```Powershell
    cd "C:\Program Files\OpenVPN\bin"
    ./openvpn.exe --genkey secret ta.key
    ```
7) Genrate server keys. Go to "C:\Program Files\OpenVPN\easy-rsa" and start the easy-rsa console 
    ```Powershell
    cd "C:\Program Files\OpenVPN\easy-rsa"
    .\EasyRSA-Start.bat
    ```
    a) In the console, initiate the PKI

        ./easyrsa init-pki
    
    b) Build the CA-certificate and select a safe password

        ./easyrsa build-ca
    
    c) Generate server certificate. You have to enter the CA password to sign the server certificate

        ./easyrsa build-server-full server nopass

    d) Generate Diffie–Hellman parameters
    
        ./easyrsa gen-dh
## Enable VPN server
1) Copy `server.ovpn` from this repository to `C:\Program Files\OpenVPN\config-auto\`
2) Press Win+R and run `services.msc`
3) Right click on `OpenVPNService` and open properties.
4) Click start
5) Change the startup type to Automatic to enable automatic startup on reboot. Save the settings and close
6) Press Win+R and run `firewall.cpl`
7) Open Advanced settings
8) Select inbound rules
9) Add new rule, allow UDP port 47777

## Generate client keys
1) Copy `generate_conf.bat` and `client.conf` to "C:\Program Files\OpenVPN\easy-rsa\"
2) Ensure that the IP-address in `client.conf` is correct
2) Open PowerShell with **administrative privileges**
3) Go to "C:\Program Files\OpenVPN\easy-rsa" and start the easy-rsa console 
    ```Powershell
    cd "C:\Program Files\OpenVPN\easy-rsa"
    .\EasyRSA-Start.bat
    ```
4) Generate a client certificate for pmu XXX. You have to enter the CA password to sign the client certificate.
    ```
    ./easyrsa build-client-full OpenPMU-KTH-XXX nopass
    ```
5) Close the easy-rsa shell
    ```
    exit
    ```
6) Generate the .ovpn client file for OpenPMU-KTH-XXX with the `generate_conf`-script
    ```PowerShell
        .\generate_conf.bat OpenPMU-KTH-XXX
    ```
7) Move the created .ovpn file to the client. The file should be kept secret since it contains the private client key and the TA key.



# Enable HTTPS security
1) Download nginx for windows, http://nginx.org/en/docs/windows.html (nginx-1.22.1.zip)

2) Unzip the file where you want it, for example (D:\nginx-1.22.1)

3) Download certbot windows 64 installer
https://certbot.eff.org/instructions?ws=nginx&os=windows
https://dl.eff.org/certbot-beta-installer-win_amd64.exe 

4) Open PowerShell and generate a ssl-certificate, run
    ```bash
    certbot certonly --standalone
    ```
    and follow the instructions
5) Copy the `nginx.conf` file from this repository and replace the nginx config file, for example (D:\nginx-1.22.1\nginx-1.22.1\conf\nginx.conf)

6) Ensure that the path to the ssl certificate is correct, for example
    ```
    ssl_certificate      C:\Certbot\live\opal3.ee.kth.se\fullchain.pem;
    ssl_certificate_key  C:\Certbot\live\opal3.ee.kth.se\privkey.pem;
    ```
