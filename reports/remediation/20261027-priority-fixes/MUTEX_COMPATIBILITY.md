# Lifecycle mutex overload compatibility

The existing lock is still `Global\NUSANTARA-V1-Lifecycle`; the fallback does not create a second lock or change its ACL.

`probe_mutex_overload.ps1` creates a unique temporary mutex, chooses an available `OpenExisting` overload, then acquires/releases and disposes both handles:

| Runtime | Selected overload | Probe |
|---|---|---|
| Windows PowerShell 5.1.26100.9711 | `OpenExisting(string, MutexRights)` | PASS |
| PowerShell 7.6.5 / .NET 10 | `OpenExisting(string)` | PASS |

The temporary same-user probe validates method selection and basic acquire/release behavior. It does not reproduce the lifecycle mutex's production ACL or prove that a particular service identity can open that handle. The later supported service start passed overload resolution but remains blocked by the unresponsive listener on port 8000.

The `MutexRights` overload requests the selected access mask. In .NET 10, the one-argument Windows implementation uses the runtime's default mask, including `MAXIMUM_ALLOWED`, `SYNCHRONIZE`, and `MUTEX_MODIFY_STATE`; OS access checks remain in effect. See the [official .NET 10 implementation](https://raw.githubusercontent.com/dotnet/runtime/v10.0.0/src/libraries/System.Private.CoreLib/src/System/Threading/Mutex.Windows.cs) and [Mutex.OpenExisting documentation](https://learn.microsoft.com/en-us/dotnet/api/system.threading.mutex.openexisting).
