# Data Structures

## Domain

A Domain is a KeyPage, with the following structure:

| Key name  | Key type   | refers to the                                                |
|-----------|------------|--------------------------------------------------------------|
| D_SELF    | KeyPageKey | keypage the key itself is contained in                       |
| D_STATE   | DataKey    | a number indicating the current process state                |
| D_TIME    | MeterKey   | meter from which the domain draws computing time             |
| D_MEMORY  | MeterKey   | meter from which the domain draws memory                     |
| D_IP      | DataKey    | current instruction pointer                                  |
| D_CODE    | PageKey    | code the domain uses                                         |
| D_POINTER | DataKey    |                                                              |
| D_STACK   | PageKey    | stack the domain uses for computation                        |
| D_DATA    | PageKey    | data the domain uses                                         |
| D_RECV    | ?          | optional, a key that points to data that has been sent to it |
