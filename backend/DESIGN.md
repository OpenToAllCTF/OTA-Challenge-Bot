
#### abstract DAO describes the serializations supported by the backend

```python
class CtfDao:
    pass

class ChallengeDao:
    pass
```

#### concrete DAO implement serialization described by abstract DAO


#### application receives handle to backend at startup


#### ctf/challenge objects are initialized with instance of concrete dao

#### backend receives serialized DAO and persists it
                    ┌───> PostgreSQL
+---------+         ├───> Redis
| Backend |>────────┼───> Pickle
+---------+         └───> ...

