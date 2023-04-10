-- These are various queries to test the database. They do not reflect the type
-- of queries to be used in the final project, and are just for demonstration.

-- Which municipalities had more than 80,000 people in 2015?
SELECT Name, County, Pop
    FROM municipality
    NATURAL JOIN population
    WHERE Pop > 80000 AND Year = 2015;

-- Which municipalities lost over 1500 people from 2015 to 2020?
CREATE VIEW pop2015 AS
    SELECT MNo, Pop AS Pop2015
    FROM population
    WHERE Year = 2015;
CREATE VIEW pop2020 AS
    SELECT MNo, Pop AS Pop2020
    FROM population
    WHERE Year = 2020;
SELECT Name, County, Pop2015, Pop2020
    FROM municipality
    NATURAL JOIN pop2015
    NATURAL JOIN pop2020
    WHERE Pop2015 - Pop2020 > 1500;
DROP VIEW pop2015;
DROP VIEW pop2020;

-- Which municipality had the most CO2 emissions from commercial trucks, and
-- in which year?
SELECT Name, County, CO2, Year
    FROM municipality
    NATURAL JOIN on_road_vehicle
    WHERE Type = 'light commercial trucks'
    ORDER BY CO2 DESC
    LIMIT 1;

-- How about motor homes?
SELECT Name, County, CO2, Year
    FROM municipality
    NATURAL JOIN on_road_vehicle
    WHERE Type = 'motor home'
    ORDER BY CO2 DESC
    LIMIT 1;

-- In towns with more than 10,000 people in 2020, which had the greatest
-- percentage of people taking a bicycle to work?
SELECT Name, County, Percentage
    FROM municipality
    NATURAL JOIN population
    NATURAL JOIN means_of_transportation
    WHERE Type = 'bicycle' AND Pop > 10000 AND Year = 2020
    ORDER BY Percentage DESC
    LIMIT 1;

-- In towns with less than 10,000 people in 2015, which had the greatest
-- percentage of people taking a taxi to work?
SELECT Name, County, Percentage
    FROM municipality
    NATURAL JOIN population
    NATURAL JOIN means_of_transportation
    WHERE Type = 'taxicab' AND Pop < 10000 AND Year = 2015
    ORDER BY Percentage DESC
    LIMIT 1;

-- What's the breakdown of GHG emmissions by vehicle type in Ewing in 2015?
SELECT Type, CO2
    FROM municipality
    NATURAL JOIN on_road_vehicle
    WHERE Name = 'Ewing Township' AND Year = 2015;

-- Did any municipalities have less than 30% of people taking cars, trucks, or
-- vans to work in 2020?
SELECT Name, County, Percentage
    FROM municipality
    NATURAL JOIN means_of_transportation
    WHERE Type = 'car, truck, or van' AND Percentage < 30.0 AND Year = 2020;
