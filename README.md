
# Architecture

# Installation

The tool can be installed as follows

```bash
git clone git@github.com:RantaSec/wineventhound-poc.git
cd winevthound-poc
pip install -r requirements.txt
```

# Generate CSV for Computer SID Lookup

The PowerShell RSAT tools can be used to create a computer SID lookup csv.

```powershell
Get-ADComputer -Filter 'Enabled -eq "True" -and DNSHostName -like "*"' `
  | Select DNSHostName,SID `
  | Export-Csv -Path computerSids.csv
```


# Retrieve CSVs from SIEM

## admins.csv

Logons with an elevated token imply that the user is an administrator on the computer.

```spl
index=wineventlog EventID=4624 LogonType IN(2,4,5,8,9,10) TargetUserSid="S-1-5-21-*" 
| stats values(TargetUserSid) as Sessions by Computer
| Rename Computer as DNSHostName
```


## rdp.csv

Logons with a a logon type of 10 implies the user is logged onto the computer via RDP.

```
index=wineventlog EventID=4624 LogonType=10 TargetUserSid="S-1-5-21-*" 
| stats values(TargetUserSid) as RDP by Computer
| Rename Computer as DNSHostName
```


## sessions.csv

Logons with Logon types 2,4,5,8,9,10 imply that credentials on the host can be dumped.

```
index=wineventlog EventID=4624 LogonType IN(2,4,5,8,9,10) TargetUserSid="S-1-5-21-*" 
TargetUserSid!="S-1-5-18" TargetUserSid!="S-1-5-20" 
TargetUserSid!="S-1-5-90-0-35" TargetUserSid!="S-1-5-96-0-35"
| stats values(TargetUserSid) as Sessions by Computer
| Rename Computer as DNSHostName
```


# Usage

Put the `compterSid.csv`, `admins.csv` , `rdp.csv`, and `sessions.csv` in the same folder as winevthound and execute it:

```bash
python3 winevthound.py > computers.json  
```