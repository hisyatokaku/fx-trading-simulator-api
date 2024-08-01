drop table if exists RATE;

create table RATE
(
    CURRENCY varchar(255) not null,
    DATE_D date not null,
    RATE float8
);

