### Training Data for strcat

#### Case1

##### kql

Event 
| extend FullMessage = strcat("EventID: ", tostring(EventID), " | Computer: ", Computer)

##### spl

index="main" source="WinEventLog:Security" 
| eval FullMessage="EventID: " . EventCode . " | Computer: " . host

#### Case2

##### kql

Event 
| extend LogDetails = strcat("User: ", Account, ", Workstation: ", WorkstationName, ", Status: ", Reason)

##### spl

index="main" source="WinEventLog:Security" 
| eval LogDetails="User: " . Account . ", Workstation: " . WorkstationName . ", Status: " . Reason

#### Case3

##### kql

Event 
| extend StatusMessage = strcat("LogonType: ", tostring(LogonTypeName), ", FailureReason: ", tostring(column_ifexists("FailureReason", "Unknown")))

##### spl

index="main" source="WinEventLog:Security" 
| eval StatusMessage="LogonType: " . LogonTypeName . ", FailureReason: " . coalesce(FailureReason, "Unknown")

#### Case4

##### kql

Event 
| extend IP_Host = strcat("IP: ", IpAddress, " - Host: ", Computer)

##### spl

index="main" source="WinEventLog:Security" 
| eval IP_Host="IP: " . IpAddress . " - Host: " . host

#### Case5

##### kql

Event 
| extend TimeDetails = strcat("StartTime: ", tostring(StartTime), " - EndTime: ", tostring(EndTime))

##### spl

index="main" source="WinEventLog:Security" 
| eval TimeDetails="StartTime: " . strftime(StartTime, "%Y-%m-%d %H:%M:%S") . " - EndTime: " . strftime(EndTime, "%Y-%m-%d %H:%M:%S")

#### Case6

##### kql

Event 
| extend FullInfo = strcat("Event: ", tostring(EventID), ", Source: ", EventSourceName, ", Computer: ", Computer)

##### spl

index="main" source="WinEventLog:Security" 
| eval FullInfo="Event: " . EventCode . ", Source: " . EventSourceName . ", Computer: " . host

#### Case7

##### kql

Event 
| where EventID == 4625 
| extend LogFailure = strcat("Account: ", Account, " - Workstation: ", WorkstationName, " - Reason: ", Reason)

##### spl

index="main" source="WinEventLog:Security" EventCode=4625 
| eval LogFailure="Account: " . Account . " - Workstation: " . WorkstationName . " - Reason: " . Reason

#### Case8

##### kql

Event 
| extend LogSummary = strcat("User ", Account, " logged in from ", Computer, " at ", tostring(TimeGenerated))

##### spl

index="main" source="WinEventLog:Security" 
| eval LogSummary="User " . Account . " logged in from " . host . " at " . strftime(_time, "%Y-%m-%d %H:%M:%S")

#### Case9

##### kql

Event 
| where EventID == 1102 
| extend AlertMessage = strcat("Security log cleared on ", Computer, " by user ", Account)

##### spl

index="main" source="WinEventLog:Security" EventCode=1102 
| eval AlertMessage="Security log cleared on " . host . " by user " . Account

#### Case10

##### kql

Event 
| where EventID == 4672 
| extend PrivilegedAccess = strcat("User ", Account, " obtained privileged access on ", Computer, " using process ", Process)

##### spl

index="main" source="WinEventLog:Security" EventCode=4672 
| eval PrivilegedAccess="User " . Account . " obtained privileged access on " . host . " using process " . Process

