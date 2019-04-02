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

INSERT INTO System_Options (option_name, option_value) VALUES('SCALE_DATA_PIN','24');
INSERT INTO System_Options (option_name, option_value) VALUES('SCALE_CLOCK_PIN','25');
INSERT INTO System_Options (option_name, option_value) VALUES('SCALE_CHANNEL','A');
INSERT INTO System_Options (option_name, option_value) VALUES('SCALE_GAIN','64');
INSERT INTO System_Options (option_name, option_value) VALUES('LID_SWITCH_PIN','14');
INSERT INTO System_Options (option_name, option_value) VALUES('LID_OPEN_PIN','15');
INSERT INTO System_Options (option_name, option_value) VALUES('LID_CLOSE_PIN','18');
INSERT INTO System_Options (option_name, option_value) VALUES('LIGHT_PIN','8');
INSERT INTO System_Options (option_name, option_value) VALUES('FAN_PIN','7');
INSERT INTO System_Options (option_name, option_value) VALUES('LED_PIN','12');
INSERT INTO System_Options (option_name, option_value) VALUES('WATCHDOG_SLEEP_TIMER','15');
INSERT INTO System_Options (option_name, option_value) VALUES('LID_SLEEP_TIMER','5');
INSERT INTO System_Options (option_name, option_value) VALUES('CLEANING_LED','true');
INSERT INTO System_Options (option_name, option_value) VALUES('NUM_MEASUREMENTS','5');
INSERT INTO System_Options (option_name, option_value) VALUES('TARE','');
INSERT INTO System_Options (option_name, option_value) VALUES('BC_TRIGGER_PIN','23');
INSERT INTO System_Options (option_name, option_value) VALUES('BARCODE_SCANNER_PATH','/dev/hidraw0');
INSERT INTO System_Options (option_name, option_value) VALUES('HOME_SERVER_URL','http://3.95.208.70:5000');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_UVC_HOUR','');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_UVC_MINUTE','');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_UVC_HOUR','');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_UVC_MINUTE','');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_FAN_HOUR','');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_FAN_MINUTE','');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_FAN_HOUR','');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_FAN_MINUTE','');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_BOTH_HOUR','');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_BOTH_MINUTE','');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_BOTH_HOUR','');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_BOTH_MINUTE','');
INSERT INTO System_Options (option_name, option_value) VALUES('PHONE_HOME_SLEEP','30');
INSERT INTO System_Options (option_name, option_value) VALUES('BROADCAST_SLEEP','30');
INSERT INTO System_Options (option_name, option_value) VALUES('LONG_CYCLE_SLEEP','600');
INSERT INTO System_Options (option_name, option_value) VALUES('SHORT_CYCLE_SLEEP','180');
INSERT INTO System_Options (option_name, option_value) VALUES('PI_BROADCAST_PORT','10001');
INSERT INTO System_Options (option_name, option_value) VALUES('CONVERSION_FACTOR','');
INSERT INTO System_Options (option_name, option_value) VALUES('UPLOAD_FAILURE_LIMIT','2');
