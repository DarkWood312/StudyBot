### AI на основе бесплатного [FutureForge API](https://api.futureforge.dev/docs#/). Выражаю отдельную благодарность автору за такой проект
### Environmental Variables
```
API_TOKEN=
SQL_HOST=
SQL_USER=
SQL_PORT=
SQL_DATABASE=
SQL_PASSWORD=
PROXY=
FUTUREFORGE_API=
WOLFRAM_API=
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
    aliases      jsonb[] default '{}'::jsonb[],
    ai_access    boolean default true
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

#### wordcloud_settings
```
create table wordcloud_settings
(
    user_id          bigint not null,
    background_color text             default 'white'::text,
    colormap         text             default 'viridis'::text,
    scale            double precision default 1,
    width            integer          default 1600,
    height           integer          default 800,
    min_font_size    integer          default 4,
    max_font_size    integer,
    max_words        integer          default 200
);
```