-- MySQL dump 10.13  Distrib 8.0.44, for Win64 (x86_64)
--
-- Host: localhost    Database: food_system
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `allocation`
--

DROP TABLE IF EXISTS `allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `allocation` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `donation_id` int NOT NULL,
  `item_no` int NOT NULL,
  `request_id` int NOT NULL,
  `allocated_quantity` int NOT NULL,
  `status` enum('Accepted','Completed','Cancelled') DEFAULT 'Accepted',
  `allocation_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`allocation_id`),
  UNIQUE KEY `uq_alloc_once` (`donation_id`,`item_no`,`request_id`,`status`),
  KEY `request_id` (`request_id`),
  CONSTRAINT `allocation_ibfk_2` FOREIGN KEY (`request_id`) REFERENCES `request` (`request_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `fk_allocation_food_item` FOREIGN KEY (`donation_id`, `item_no`) REFERENCES `food_item` (`donation_id`, `item_no`),
  CONSTRAINT `chk_alloc_qty` CHECK ((`allocated_quantity` > 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `donor_profile`
--

DROP TABLE IF EXISTS `donor_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `donor_profile` (
  `person_id` int NOT NULL,
  `donor_category` enum('Hotel','Hostel','Event','Individual') NOT NULL DEFAULT 'Individual',
  `status` enum('Active','Inactive') DEFAULT 'Active',
  PRIMARY KEY (`person_id`),
  CONSTRAINT `donor_profile_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `food_donation`
--

DROP TABLE IF EXISTS `food_donation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `food_donation` (
  `donation_id` int NOT NULL AUTO_INCREMENT,
  `donor_user_id` int DEFAULT NULL,
  `donor_temp_id` char(36) DEFAULT NULL,
  `total_quantity` int NOT NULL,
  `remaining_quantity` int NOT NULL,
  `pincode` char(6) NOT NULL,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `donation_token` char(36) NOT NULL,
  `status` enum('Open','PartiallyAllocated','Completed','Expired') NOT NULL DEFAULT 'Open',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`donation_id`),
  UNIQUE KEY `donation_token` (`donation_token`),
  KEY `donor_user_id` (`donor_user_id`),
  KEY `donor_temp_id` (`donor_temp_id`),
  CONSTRAINT `food_donation_ibfk_1` FOREIGN KEY (`donor_user_id`) REFERENCES `registered_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `food_donation_ibfk_2` FOREIGN KEY (`donor_temp_id`) REFERENCES `temporary_user` (`temp_user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_donation_coords` CHECK (((`latitude` is not null) and (`longitude` is not null))),
  CONSTRAINT `chk_donation_qty` CHECK (((`total_quantity` > 0) and (`remaining_quantity` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `food_item`
--

DROP TABLE IF EXISTS `food_item`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `food_item` (
  `donation_id` int NOT NULL,
  `item_no` int NOT NULL,
  `food_name` varchar(120) NOT NULL,
  `food_category` varchar(80) DEFAULT NULL,
  `quantity` int NOT NULL,
  `remaining_quantity` int NOT NULL,
  `meal_type` enum('Breakfast','Lunch','Dinner','Any') NOT NULL DEFAULT 'Any',
  `cooked_time` datetime NOT NULL,
  `safe_until` datetime NOT NULL,
  PRIMARY KEY (`donation_id`,`item_no`),
  KEY `idx_item_safe_until` (`safe_until`),
  KEY `idx_food_item_safe` (`safe_until`,`remaining_quantity`),
  CONSTRAINT `food_item_ibfk_1` FOREIGN KEY (`donation_id`) REFERENCES `food_donation` (`donation_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_item_qty` CHECK (((`quantity` > 0) and (`remaining_quantity` >= 0))),
  CONSTRAINT `chk_item_time` CHECK ((`safe_until` > `cooked_time`))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `person`
--

DROP TABLE IF EXISTS `person`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `person` (
  `person_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `phone` varchar(20) NOT NULL,
  `pincode` char(6) NOT NULL,
  `latitude` double DEFAULT NULL,
  `longitude` double DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`person_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `pincode_geo`
--

DROP TABLE IF EXISTS `pincode_geo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `pincode_geo` (
  `pincode` char(6) NOT NULL,
  `district` varchar(80) DEFAULT NULL,
  `state` varchar(80) DEFAULT NULL,
  `latitude` decimal(9,6) NOT NULL,
  `longitude` decimal(9,6) NOT NULL,
  PRIMARY KEY (`pincode`),
  KEY `idx_state` (`state`),
  KEY `idx_district` (`district`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `receiver_profile`
--

DROP TABLE IF EXISTS `receiver_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `receiver_profile` (
  `person_id` int NOT NULL,
  `receiver_category` enum('ChildrenHome','OldAgeHome','NGO','Other') NOT NULL DEFAULT 'NGO',
  `status` enum('Active','Inactive') NOT NULL DEFAULT 'Active',
  `priority_level` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`person_id`),
  CONSTRAINT `receiver_profile_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_priority_level` CHECK ((`priority_level` in (1,2,3)))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `registered_user`
--

DROP TABLE IF EXISTS `registered_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `registered_user` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `person_id` int NOT NULL,
  `username` varchar(60) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('Donor','Receiver') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `person_id` (`person_id`),
  UNIQUE KEY `username` (`username`),
  CONSTRAINT `registered_user_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `request`
--

DROP TABLE IF EXISTS `request`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `request` (
  `request_id` int NOT NULL AUTO_INCREMENT,
  `receiver_user_id` int DEFAULT NULL,
  `receiver_temp_id` char(36) DEFAULT NULL,
  `required_date` date NOT NULL,
  `meal_preference` enum('Breakfast','Lunch','Dinner','Any') NOT NULL DEFAULT 'Any',
  `total_quantity_requested` int NOT NULL,
  `quantity_allocated` int NOT NULL DEFAULT '0',
  `remaining_required` int NOT NULL,
  `urgency_level` enum('High','Medium','Low') NOT NULL DEFAULT 'Medium',
  `partial_flag` tinyint(1) NOT NULL DEFAULT '0',
  `priority_score` int NOT NULL DEFAULT '0',
  `status` enum('Pending','Partial','Fulfilled','Cancelled') NOT NULL DEFAULT 'Pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`request_id`),
  KEY `receiver_user_id` (`receiver_user_id`),
  KEY `receiver_temp_id` (`receiver_temp_id`),
  KEY `idx_request_match` (`required_date`,`status`,`remaining_required`),
  CONSTRAINT `request_ibfk_1` FOREIGN KEY (`receiver_user_id`) REFERENCES `registered_user` (`user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `request_ibfk_2` FOREIGN KEY (`receiver_temp_id`) REFERENCES `temporary_user` (`temp_user_id`) ON DELETE RESTRICT ON UPDATE CASCADE,
  CONSTRAINT `chk_req_qty` CHECK (((`total_quantity_requested` > 0) and (`remaining_required` >= 0)))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `temporary_user`
--

DROP TABLE IF EXISTS `temporary_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `temporary_user` (
  `temp_user_id` char(36) NOT NULL,
  `person_id` int NOT NULL,
  `tracking_id` varchar(30) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`temp_user_id`),
  UNIQUE KEY `person_id` (`person_id`),
  UNIQUE KEY `tracking_id` (`tracking_id`),
  CONSTRAINT `temporary_user_ibfk_1` FOREIGN KEY (`person_id`) REFERENCES `person` (`person_id`) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-10-21  9:59:18
