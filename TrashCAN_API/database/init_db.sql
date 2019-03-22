CREATE TABLE System_Options (
	system_option_id integer PRIMARY KEY AUTOINCREMENT,
	option_name varchar,
	option_value varchar
);

CREATE TABLE System_Option_Changes (
	system_option_change_id integer PRIMARY KEY AUTOINCREMENT,
	system_option_id integer,
	timestamp datetime DEFAULT CURRENT_TIMESTAMP,
	change_type varchar,
	option_name varchar,
	Old_option_name varchar,
	option_value varchar,
	Old_option_value varchar
);

CREATE TABLE Barcode (
	barcode_id varchar,
	timestamp datetime DEFAULT CURRENT_TIMESTAMP,
	barcode varchar
);

CREATE TABLE Weight (
	weight_id varchar,
	timestamp datetime DEFAULT CURRENT_TIMESTAMP,
	weight integer,
	weight_raw varchar
);

CREATE TRIGGER trg_System_Options_Delete AFTER DELETE ON System_Options
BEGIN
  INSERT INTO System_Option_Changes (system_option_id,change_type,Old_option_name,Old_option_value)
  SELECT Old.system_option_id,'D',Old.option_name,Old.option_value;
END;

CREATE TRIGGER trg_System_Options_Insert AFTER INSERT ON System_Options
BEGIN
  INSERT INTO System_Option_Changes (system_option_id,change_type,option_name,option_value)
  SELECT New.system_option_id,'I',New.option_name,New.option_value;
END;

CREATE TRIGGER trg_System_Options_Update AFTER UPDATE ON System_Options
BEGIN
  INSERT INTO System_Option_Changes (system_option_id,change_type,option_name,Old_option_name,option_value,Old_option_value)
  SELECT New.system_option_id,'U',New.option_name,Old.option_name,New.option_value,Old.option_value;
END;