### Training Data for make_set

#### Case1

##### kql

Event 
| summarize UniqueComputers = make_set(Computer, 128) by EventID

##### spl

index="main" source="WinEventLog:Security" 
| stats values(host) as UniqueComputers by EventCode

#### Case2

##### kql

Event 
| summarize UniqueIPAddresses = make_set(IpAddress, 128) by Account

##### spl

index="main" source="WinEventLog:Security" 
| stats values(IpAddress) as UniqueIPAddresses by Account

#### Case3

##### kql

Event 
| summarize UniqueWorkstations = make_set(WorkstationName, 128) by EventID

##### spl

index="main" source="WinEventLog:Security" 
| stats values(WorkstationName) as UniqueWorkstations by EventCode

#### Case4

##### kql

Event 
| summarize UniqueAccounts = make_set(Account, 128) by Computer

##### spl

index="main" source="WinEventLog:Security" 
| stats values(Account) as UniqueAccounts by host

#### Case5

##### kql

Event 
| summarize UniqueProcesses = make_set(Process, 128) by EventID

##### spl

index="main" source="WinEventLog:Security" 
| stats values(Process) as UniqueProcesses by EventCode

#### Case6

##### kql

Event 
| summarize UniqueEventIDs = make_set(EventID, 128), TotalEvents = count() by Account

##### spl

index="main" source="WinEventLog:Security" 
| stats values(EventCode) as UniqueEventIDs, count as TotalEvents by Account

#### Case7

##### kql

Event 
| summarize UniqueIPAddresses = make_set(IpAddress, 128) by LogonTypeName

##### spl

index="main" source="WinEventLog:Security" 
| stats values(IpAddress) as UniqueIPAddresses by LogonTypeName

#### Case8

##### kql

Event 
| where EventID == 4625 
| summarize UniqueReasons = make_set(Reason, 128), FailureCount = count() by EventID

##### spl

index="main" source="WinEventLog:Security" EventCode=4625 
| stats values(Reason) as UniqueReasons, count as FailureCount by EventCode

#### Case9

##### kql

Event 
| summarize UniqueComputers = make_set(Computer, 128), UniqueIPAddresses = make_set(IpAddress, 128) by EventID

##### spl

index="main" source="WinEventLog:Security" 
| stats values(host) as UniqueComputers, values(IpAddress) as UniqueIPAddresses by EventCode

#### Case10

##### kql

Event 
| summarize UniqueWorkstations = make_set(WorkstationName, 128), TotalCount = count() by Account

##### spl

index="main" source="WinEventLog:Security" 
| stats values(WorkstationName) as UniqueWorkstations, count as TotalCount by Account

