https://t.me/StudyPomogator_bot
### Environment Variables
```
API_TOKEN=
SQL_HOST=
SQL_USER=
SQL_PORT=
SQL_DATABASE=
SQL_PASSWORD=
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
VISIONAI_API=
OPENAI_API=
WOLFRAM_API=
GIGACHAT_API=
DEEP_TRANSLATE_API=
UCHUS_COOKIES=
```

### Database (_PostgreSQL_)
#### Users
```
create table users
(
    user_id       bigint not null,
    upscaled      boolean default false,
    username      text,
    user_name     text,
    user_surname  text,
    admin         boolean default false,
    aliases       jsonb   default '{}'::jsonb,
    ai_access     boolean default false,
    openai_tokens integer default 0
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

#### uchus_online
```
create table public.uchus_online
(
    user_id        bigint not null,
    min_complexity integer   default 0,
    max_complexity integer   default 100,
    complexity_asc boolean   default true,
    done           integer[] default '{}'::integer[]
);
```
