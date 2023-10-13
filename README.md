### Environmental Variables
```
API_TOKEN=
SQL_HOST=
SQL_USER=
SQL_PORT=
SQL_DATABASE=
SQL_PASSWORD=
```

### Database (_PostgreSQL_)
#### Users
```
create table users
(
    user_id      bigint not null,
    upscaled     boolean default false,
    username     text,
    user_name    text,
    user_surname text,
    admin        boolean default false,
    alias        jsonb[]
);
```
#### orthoepy_problems
```
create table orthoepy_problems
(
    word    text              not null,
    counter integer default 0 not null
);
```