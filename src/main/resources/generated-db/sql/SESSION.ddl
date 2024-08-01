drop table if exists SESSION;

create table SESSION
(
    id int not null,
    USER_ID varchar(255),
    START_DATE date,
    C_DATE date,
    END_DATE date,
    IS_COMPLETE boolean,
    SCENARIO varchar(255) not null,
    JPY_AMOUNT float8
);

