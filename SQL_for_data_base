CREATE TABLE "table" (
  "id" SERIAL NOT NULL UNIQUE,
  "name" TEXT NOT NULL,
  -- Описание таблицы
  "discription" TEXT,
  "owner" INTEGER NOT NULL,
  -- Время и дата создания таблицы.
  "data_creat" TIMESTAMPTZ NOT NULL,
  PRIMARY KEY("id")
);

COMMENT ON COLUMN "table".discription IS 'Описание таблицы';
COMMENT ON COLUMN "table".data_creat IS 'Время и дата создания таблицы.';


CREATE TABLE "users" (
  "id" SERIAL NOT NULL UNIQUE,
  -- ID пользователя в приложении.
  "id_user" BIGINT NOT NULL UNIQUE,
  "user_name" VARCHAR(100) UNIQUE,
  "username" VARCHAR(100),
  "platform" INTEGER NOT NULL,
  "data" TIMESTAMPTZ NOT NULL,
  "user_surname" VARCHAR(100) UNIQUE,
  PRIMARY KEY("id")
);
COMMENT ON COLUMN "users".id_user IS 'ID пользователя в приложении.';


CREATE TABLE "records" (
  "id" SERIAL NOT NULL UNIQUE,
  "id_table" INTEGER NOT NULL,
  "id_name" INTEGER NOT NULL,
  "data" TIMESTAMPTZ NOT NULL,
  PRIMARY KEY("id")
);


CREATE TABLE "platforms" (
  "id" SERIAL NOT NULL UNIQUE,
  "name" VARCHAR(20) NOT NULL,
  PRIMARY KEY("id")
);


ALTER TABLE "records"
ADD FOREIGN KEY("id_table") REFERENCES "table"("id")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "users"
ADD FOREIGN KEY("platform") REFERENCES "platforms"("id")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "table"
ADD FOREIGN KEY("owner") REFERENCES "users"("id")
ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE "records"
ADD FOREIGN KEY("id_name") REFERENCES "users"("id")
ON UPDATE NO ACTION ON DELETE NO ACTION;

ALTER TABLE "table"
ADD COLUMN show_participants BOOLEAN DEFAULT FALSE;
-- Обновление существующих строк, установка значения FALSE
UPDATE "table"
SET show_participants = false ;

alter table "table" add column notification BOOLEAN default false;