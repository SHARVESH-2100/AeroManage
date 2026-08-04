-- AeroManage — database schema
-- College mini-project for the Database Management Systems (DBMS) course.
--
-- Usage:
--   mysql -u root -p < schema.sql
--
-- Recreates the `aero` database and loads a small sample dataset.

DROP DATABASE IF EXISTS aero;
CREATE DATABASE aero;
USE aero;

-- ---------------------------------------------------------------------------
-- Aircraft fleet
-- ---------------------------------------------------------------------------
CREATE TABLE fleet (
    aircraft_id   INT AUTO_INCREMENT PRIMARY KEY,
    aircraft_name VARCHAR(100) NOT NULL,
    range_km      INT NOT NULL,
    fuel_capacity INT NOT NULL,
    status        ENUM('Available', 'Busy') NOT NULL DEFAULT 'Available'
);

-- ---------------------------------------------------------------------------
-- Pilots (each pilot may be assigned to a single aircraft)
-- ---------------------------------------------------------------------------
CREATE TABLE pilots (
    pilot_id         INT AUTO_INCREMENT PRIMARY KEY,
    pilot_name       VARCHAR(100) NOT NULL,
    pilot_rank       VARCHAR(50),
    experience_years INT,
    aircraft_id      INT NULL,
    status           ENUM('Available', 'On Mission') NOT NULL DEFAULT 'Available',
    CONSTRAINT fk_pilots_fleet
        FOREIGN KEY (aircraft_id) REFERENCES fleet (aircraft_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- Missions (links one aircraft and one pilot)
-- ---------------------------------------------------------------------------
CREATE TABLE missions (
    mission_id   INT AUTO_INCREMENT PRIMARY KEY,
    mission_name VARCHAR(120) NOT NULL,
    distance_km  INT NOT NULL,
    aircraft_id  INT NULL,
    pilot_id     INT NULL,
    status       ENUM('Planned', 'Completed') NOT NULL DEFAULT 'Planned',
    CONSTRAINT fk_missions_fleet
        FOREIGN KEY (aircraft_id) REFERENCES fleet (aircraft_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    CONSTRAINT fk_missions_pilots
        FOREIGN KEY (pilot_id) REFERENCES pilots (pilot_id)
        ON DELETE SET NULL
        ON UPDATE CASCADE
);

-- ---------------------------------------------------------------------------
-- Sample data
-- ---------------------------------------------------------------------------
INSERT INTO fleet (aircraft_name, range_km, fuel_capacity, status) VALUES
    ('Boeing 737',  5600, 26000, 'Available'),
    ('Airbus A320', 6100, 24210, 'Available'),
    ('Cessna 172',  1272,   212, 'Busy');

INSERT INTO pilots (pilot_name, pilot_rank, experience_years, aircraft_id, status) VALUES
    ('Arjun Rao',  'Captain',       12, 1, 'Available'),
    ('Meera Nair', 'First Officer',  6, 2, 'Available'),
    ('Vikram Shah','Captain',       15, 3, 'On Mission');

INSERT INTO missions (mission_name, distance_km, aircraft_id, pilot_id, status) VALUES
    ('Coastal Survey',     420, 3, 3, 'Planned'),
    ('Cargo Run - North', 1180, 1, 1, 'Completed');
