-- MySQL Workbench Forward Engineering

SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------

-- -----------------------------------------------------
-- Schema mydb
-- -----------------------------------------------------
CREATE SCHEMA IF NOT EXISTS `mydb` DEFAULT CHARACTER SET utf8 ;
USE `mydb` ;

-- -----------------------------------------------------
-- Table `mydb`.`member`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`member` (
  `member_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(15) NULL,
  `email` VARCHAR(100) NOT NULL,
  PRIMARY KEY (`member_id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`memberships`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`memberships` (
  `membership_id` INT NOT NULL AUTO_INCREMENT,
  `membership_name` ENUM('Bronze', 'Silver', 'Gold', 'Platinum') NOT NULL,
  `price` DECIMAL(10,2) NOT NULL,
  `duration_months` INT NOT NULL,
  PRIMARY KEY (`membership_id`),
  UNIQUE INDEX `membership_name_UNIQUE` (`membership_name` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`staff`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`staff` (
  `staff_id` INT NOT NULL AUTO_INCREMENT,
  `name` VARCHAR(100) NOT NULL,
  `phone_number` VARCHAR(15) NULL,
  `email` VARCHAR(100) NOT NULL,
  `hire_date` DATE NOT NULL,
  `salary` DECIMAL(7,2) NOT NULL,
  `status` ENUM('Active', 'Inactive') NOT NULL DEFAULT 'Active',
  `role` VARCHAR(20) NOT NULL,
  `last_day` DATE NULL DEFAULT NULL,
  PRIMARY KEY (`staff_id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE,
  UNIQUE INDEX `phone_number_UNIQUE` (`phone_number` ASC) VISIBLE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`trainers`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`trainers` (
  `staff_id` INT NOT NULL,
  `certification` VARCHAR(100) NULL,
  PRIMARY KEY (`staff_id`),
  INDEX `fk_trainers_staff1_idx` (`staff_id` ASC) VISIBLE,
  CONSTRAINT `fk_trainers_staff1`
    FOREIGN KEY (`staff_id`)
    REFERENCES `mydb`.`staff` (`staff_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`class_type`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`class_type` (
  `class_type_id` INT NOT NULL AUTO_INCREMENT,
  `class_name` VARCHAR(100) NULL,
  `difficulty_level` VARCHAR(20) NULL,
  PRIMARY KEY (`class_type_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`classes`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`classes` (
  `class_id` INT NOT NULL AUTO_INCREMENT,
  `scheduled_time` DATETIME NULL,
  `duration_minutes` INT NULL,
  `capacity` INT NULL,
  `trainers_staff_id` INT NOT NULL,
  `class_type_id` INT NOT NULL,
  PRIMARY KEY (`class_id`),
  INDEX `fk_classes_trainers1_idx` (`trainers_staff_id` ASC) VISIBLE,
  INDEX `fk_classes_class_type1_idx` (`class_type_id` ASC) VISIBLE,
  CONSTRAINT `fk_classes_trainers1`
    FOREIGN KEY (`trainers_staff_id`)
    REFERENCES `mydb`.`trainers` (`staff_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_classes_class_type1`
    FOREIGN KEY (`class_type_id`)
    REFERENCES `mydb`.`class_type` (`class_type_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`member_membership`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`member_membership` (
  `member_membership_id` INT NOT NULL AUTO_INCREMENT,
  `member_id` INT NOT NULL,
  `membership_id` INT NOT NULL,
  `start_date` DATE NOT NULL,
  `end_date` DATE NULL,
  INDEX `fk_member_has_memberships_memberships1_idx` (`membership_id` ASC) VISIBLE,
  INDEX `fk_member_has_memberships_member1_idx` (`member_id` ASC) VISIBLE,
  PRIMARY KEY (`member_membership_id`),
  CONSTRAINT `fk_member_has_memberships_member1`
    FOREIGN KEY (`member_id`)
    REFERENCES `mydb`.`member` (`member_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_member_has_memberships_memberships1`
    FOREIGN KEY (`membership_id`)
    REFERENCES `mydb`.`memberships` (`membership_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`class_enrollment`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`class_enrollment` (
  `class_enrollment_id` INT NOT NULL AUTO_INCREMENT,
  `class_id` INT NOT NULL,
  `member_id` INT NOT NULL,
  `signup_date` DATE NULL,
  `attendance_status` ENUM('registered', 'attended', 'missed', 'cancelled') NOT NULL,
  INDEX `fk_classes_has_member_member1_idx` (`member_id` ASC) VISIBLE,
  INDEX `fk_classes_has_member_classes1_idx` (`class_id` ASC) VISIBLE,
  PRIMARY KEY (`class_enrollment_id`),
  UNIQUE INDEX `uq_class_member` (`class_id`, `member_id`),
  CONSTRAINT `fk_classes_has_member_classes1`
    FOREIGN KEY (`class_id`)
    REFERENCES `mydb`.`classes` (`class_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_classes_has_member_member1`
    FOREIGN KEY (`member_id`)
    REFERENCES `mydb`.`member` (`member_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`payments`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`payments` (
  `payment_id` INT NOT NULL AUTO_INCREMENT,
  `member_id` INT NOT NULL,
  `amount` DECIMAL(8,2) NOT NULL,
  `payment_date` DATE NULL,
  `payment_method` VARCHAR(50) NOT NULL,
  `status` ENUM('pending', 'completed', 'failed', 'refunded') NULL,
  `payment_type` ENUM('membership', 'class') NOT NULL,
  `member_membership_id` INT NULL,
  `class_enrollment_id` INT NULL,
  INDEX `fk_payments_member1_idx` (`member_id` ASC) VISIBLE,
  PRIMARY KEY (`payment_id`),
  INDEX `fk_payments_member_membership1_idx` USING BTREE (`member_membership_id`) VISIBLE,
  INDEX `fk_payments_class_enrollment1_idx` (`class_enrollment_id` ASC) VISIBLE,
  CONSTRAINT `fk_payments_member1`
    FOREIGN KEY (`member_id`)
    REFERENCES `mydb`.`member` (`member_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_payments_member_membership1`
    FOREIGN KEY (`member_membership_id`)
    REFERENCES `mydb`.`member_membership` (`member_membership_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_payments_class_enrollment1`
    FOREIGN KEY (`class_enrollment_id`)
    REFERENCES `mydb`.`class_enrollment` (`class_enrollment_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `chk_payment_ref` CHECK (
    (member_membership_id IS NOT NULL AND class_enrollment_id IS NULL)
    OR
    (member_membership_id IS NULL AND class_enrollment_id IS NOT NULL)
  ))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`equipment`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`equipment` (
  `equipment_id` INT NOT NULL AUTO_INCREMENT,
  `equipment_name` VARCHAR(45) NOT NULL,
  `purchase_date` DATE NOT NULL,
  PRIMARY KEY (`equipment_id`))
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `mydb`.`maintenance`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`maintenance` (
  `maintenance_id` INT NOT NULL AUTO_INCREMENT,
  `equipment_id` INT NOT NULL,
  `maintenance_date` DATE NOT NULL,
  `staff_id` INT NOT NULL,
  PRIMARY KEY (`maintenance_id`),
  INDEX `fk_maintenance_equipment1_idx` (`equipment_id` ASC) VISIBLE,
  INDEX `fk_maintenance_staff1_idx` (`staff_id` ASC) VISIBLE,
  CONSTRAINT `fk_maintenance_equipment1`
    FOREIGN KEY (`equipment_id`)
    REFERENCES `mydb`.`equipment` (`equipment_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION,
  CONSTRAINT `fk_maintenance_staff1`
    FOREIGN KEY (`staff_id`)
    REFERENCES `mydb`.`staff` (`staff_id`)
    ON DELETE NO ACTION
    ON UPDATE NO ACTION)
ENGINE = InnoDB;


SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
