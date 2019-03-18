CREATE TABLE System_Option (
	system_option_id integer PRIMARY KEY AUTOINCREMENT,
	option_name varchar,
	option_value varchar
);

CREATE TRIGGER trg_System_Options_Delete AFTER DELETE ON System_Options
BEGIN
  INSERT INTO System_Option_Changes (system_option_id,change_type,old_option_name,old_option_value)
  SELECT system_option_id,'D',option_name,option_value
  FROM deleted
END

CREATE TRIGGER trg_System_Options_Insert AFTER INSERT ON System_Options
BEGIN
  INSERT INTO System_Option_Changes (system_option_id,change_type,old_option_name,old_option_value)
  SELECT system_option_id,'I',option_name,option_value
  FROM inserted
END

CREATE TRIGGER trg_System_Options_Update AFTER UPDATE ON System_Options
BEGIN
  INSERT INTO System_Option_Changes (system_option_id,change_type,option_name,old_option_name,option_value,old_option_value)
  SELECT system_option_id,'U',inserted.option_name,deleted.option_name,inserted.option_value,deleted.option_value
  FROM inserted INNER JOIN deleted ON deleted.system_option_id = inserted.system_option_id
END


CREATE TABLE System_Option_Changes (
	system_option_change_id integer PRIMARY KEY AUTOINCREMENT,
	system_option_id integer,
	timestamp datetime,
	change_type varchar,
	option_name varchar,
	old_option_name varchar,
	option_value varchar,
	old_option_value varchar
);

CREATE TABLE barcode (
	barcode_id varchar,
	timestamp datetime,
	barcode varchar
);

CREATE TABLE weight (
	weight_id varchar,
	timestamp datetime,
	weight integer,
	weight_raw varchar
);
