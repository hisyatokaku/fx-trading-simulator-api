drop table if exists BALANCE;

create table BALANCE
(
    SESSION_ID int not null,
    DATE_D date not null,
    CURRENCY varchar(255) not null,
    AMOUNT float8
);

