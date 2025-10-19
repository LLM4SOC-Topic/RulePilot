### Training Data for Join

#### Case 1

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 4625
| summarize CountToday = count() by EventID, Computer
| join kind=leftouter (
    Event
    | where TimeGenerated between (ago(3d) .. ago(1d))
    | where EventID == 4625
    | summarize CountPrev7day = count() by EventID, Computer
) on EventID, Computer

##### spl

index="main" source="WinEventLog:Security" EventCode=4625
| where _time >= relative_time(now(), "-1d")
| stats count as CountToday by EventCode, host
| join type=left EventCode host [
    search index="main" source="WinEventLog:Security" EventCode=4625
    | where _time >= relative_time(now(), "-3d") AND _time < relative_time(now(), "-1d")
    | stats count as CountPrev7day by EventCode, host
]

#### Case 2

##### kql

Event | where TimeGenerated >= ago(1d) 
| where EventID == 4625 
| summarize CountToday = count() by EventID, Computer 
| join kind=inner (   
 Event   
 | where TimeGenerated between (ago(3d) .. ago(1d))  
 | where EventID == 4625   
 | summarize CountPrev7day = count() by EventID, Computer )
 on EventID, Computer



##### spl

index="main" source="WinEventLog:Security" EventCode=4625
| where _time >= relative_time(now(), "-1d")
| stats count as CountToday by EventCode, host
| join type=inner EventCode host [
    search index="main" source="WinEventLog:Security" EventCode=4625
    | where _time >= relative_time(now(), "-3d") AND _time < relative_time(now(), "-1d")
    | stats count as CountPrev7day by EventCode, host
]



#### Case 3

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 4625
| summarize CountToday = count() by EventID, Computer
| join kind=leftouter (
    SecurityEvent
    | where TimeGenerated between (ago(3d) .. ago(1d))
    | where EventID == 4625
    | summarize CountPrev7day = count() by EventID, Computer
) on $left.EventID == $right.EventID, Computer 



##### spl

index="main" source="WinEventLog:Security" EventCode=4625
| where _time >= relative_time(now(), "-1d")
| stats count as CountToday by EventCode, host
| join type=left left=L right=R where L.EventCode=R.EventCode [
    search index="main" source="WinEventLog:Security" EventCode=4625
    | where _time >= relative_time(now(), "-3d") AND _time < relative_time(now(), "-1d")
    | stats count as CountPrev7day by EventCode, host
]



#### Case 4

##### kql

Event
| where TimeGenerated between(datetime("2025-02-18T05:30:00Z") .. datetime("2025-02-18T06:00:00Z"))
| project TimeGenerated,EventID,Computer
| join (
Event
| where TimeGenerated between(datetime("2025-02-18T05:45:00Z") .. datetime("2025-02-18T06:15:00Z"))
| project TimeGenerated,EventID,Computer
)on TimeGenerated,EventID,Computer

##### spl

index="main" source="WinEventLog:Security"
| where _time >= strptime("2025-02-18T05:30:00Z", "%Y-%m-%dT%H:%M:%SZ") 
    AND _time <= strptime("2025-02-18T06:00:00Z", "%Y-%m-%dT%H:%M:%SZ")
| table _time EventCode host
| join type=inner _time EventCode host [
    search index="main" source="WinEventLog:Security"
    | where _time >= strptime("2025-02-18T05:45:00Z", "%Y-%m-%dT%H:%M:%SZ") 
        AND _time <= strptime("2025-02-18T06:15:00Z", "%Y-%m-%dT%H:%M:%SZ")
    | table _time EventCode host
]



#### Case 5

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 4625
| join kind=inner (
    Event
    | where TimeGenerated >= ago(3d)
    | where EventID == 4625
) on EventID, Computer

##### spl

index="main" source="WinEventLog:Security" EventCode=4625
| where _time >= relative_time(now(), "-1d")
| join type=inner max=0 EventCode host [
    search index="main" source="WinEventLog:Security" EventCode=4625
    | where _time >= relative_time(now(), "-3d")
]



#### Case 6

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 4688 
| summarize CountToday = count() by EventID, Computer
| join kind=leftouter (
    Event
    | where TimeGenerated between (ago(3d) .. ago(1d))
    | where EventID == 4688
    | summarize CountPrev7day = count() by EventID, Computer
) on EventID, Computer

##### spl

index="main" source="WinEventLog:Security" EventCode=4688
| where _time >= relative_time(now(), "-1d")
| stats count as CountToday by EventCode, host
| join type=left EventCode host [
    search index="main" source="WinEventLog:Security" EventCode=4688
    | where _time >= relative_time(now(), "-3d") AND _time < relative_time(now(), "-1d")
    | stats count as CountPrev7day by EventCode, host
]



#### Case 7

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 1102 
| summarize CountToday = count() by EventID, Computer
| join kind=inner (
    Event
    | where TimeGenerated between (ago(3d) .. ago(1d))
    | where EventID == 1102
    | summarize CountPrev7day = count() by EventID, Computer
) on EventID, Computer

##### spl

index="main" source="WinEventLog:Security" EventCode=1102
| where _time >= relative_time(now(), "-1d")
| stats count as CountToday by EventCode, host
| join type=inner EventCode host [
    search index="main" source="WinEventLog:Security" EventCode=1102
    | where _time >= relative_time(now(), "-3d") AND _time < relative_time(now(), "-1d")
    | stats count as CountPrev7day by EventCode, host
]



#### Case 8 

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 4624 
| summarize CountToday = count() by EventID, Computer
| join kind=leftouter (
    SecurityEvent
    | where TimeGenerated between (ago(3d) .. ago(1d))
    | where EventID == 4624
    | summarize CountPrev7day = count() by EventID, Computer
) on $left.EventID == $right.EventID, Computer

##### spl

index="main" source="WinEventLog:Security" EventCode=4624
| where _time >= relative_time(now(), "-1d")
| stats count as CountToday by EventCode, host
| join type=left left=L right=R where L.EventCode=R.EventCode [
    search index="main" source="WinEventLog:Security" EventCode=4624
    | where _time >= relative_time(now(), "-3d") AND _time < relative_time(now(), "-1d")
    | stats count as CountPrev7day by EventCode, host
]





#### Case 9

##### kql

Event
| where TimeGenerated between(datetime("2025-02-18T06:00:00Z") .. datetime("2025-02-18T06:30:00Z"))
| project TimeGenerated, EventID, Computer
| join (
    Event
    | where TimeGenerated between(datetime("2025-02-18T06:15:00Z") .. datetime("2025-02-18T06:45:00Z"))
    | project TimeGenerated, EventID, Computer
) on TimeGenerated, EventID, Computer

##### spl

index="main" source="WinEventLog:Security"
| where _time >= strptime("2025-02-18T06:00:00Z", "%Y-%m-%dT%H:%M:%SZ") 
    AND _time <= strptime("2025-02-18T06:30:00Z", "%Y-%m-%dT%H:%M:%SZ")
| table _time EventCode host
| join type=inner _time EventCode host [
    search index="main" source="WinEventLog:Security"
    | where _time >= strptime("2025-02-18T06:15:00Z", "%Y-%m-%dT%H:%M:%SZ") 
        AND _time <= strptime("2025-02-18T06:45:00Z", "%Y-%m-%dT%H:%M:%SZ")
    | table _time EventCode host
]





#### Case 10

##### kql

Event
| where TimeGenerated >= ago(1d)
| where EventID == 4672  
| join kind=inner (
    Event
    | where TimeGenerated >= ago(3d)
    | where EventID == 4672
) on EventID, Computer

##### spl

index="main" source="WinEventLog:Security" EventCode=4672
| where _time >= relative_time(now(), "-1d")
| join type=inner max=0 EventCode host [
    search index="main" source="WinEventLog:Security" EventCode=4672
    | where _time >= relative_time(now(), "-3d")
]







