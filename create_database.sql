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
CREATE SCHEMA IF NOT EXISTS `mydb` ;
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
  UNIQUE INDEX `uq_class_member` (`class_id`,`member_id`),
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

USE `mydb` ;

-- -----------------------------------------------------
-- Placeholder table for view `mydb`.`active_memberships`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`active_memberships` (`member_id` INT, `name` INT, `email` INT, `membership_name` INT, `start_date` INT, `end_date` INT);

-- -----------------------------------------------------
-- Placeholder table for view `mydb`.`class_enrollment_summary`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`class_enrollment_summary` (`class_id` INT, `class_name` INT, `scheduled_time` INT, `capacity` INT, `enrolled_count` INT, `spots_remaining` INT);

-- -----------------------------------------------------
-- Placeholder table for view `mydb`.`member_payment_details`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `mydb`.`member_payment_details` (`member_name` INT, `payment_id` INT, `amount` INT, `payment_type` INT, `status` INT, `membership_name` INT, `class_name` INT);

-- -----------------------------------------------------
-- procedure enroll_member_in_class
-- -----------------------------------------------------

DELIMITER $$
USE `mydb`$$
CREATE PROCEDURE enroll_member_in_class (
    IN p_member_id INT,
    IN p_class_id INT
)
BEGIN
    DECLARE current_count INT;
    DECLARE max_capacity INT;
    DECLARE already_enrolled INT;

    -- Check if already enrolled
    SELECT COUNT(*) INTO already_enrolled
    FROM class_enrollment
    WHERE member_id = p_member_id AND class_id = p_class_id;

    IF already_enrolled > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Member already enrolled in this class';
    END IF;

    -- Get current enrollment count
    SELECT COUNT(*) INTO current_count
    FROM class_enrollment
    WHERE class_id = p_class_id;

    -- Get class capacity
    SELECT capacity INTO max_capacity
    FROM classes
    WHERE class_id = p_class_id;

    -- Check if class is full
    IF current_count >= max_capacity THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Class is full';
    ELSE
        -- Insert enrollment
        INSERT INTO class_enrollment (
            class_id,
            member_id,
            signup_date,
            attendance_status
        )
        VALUES (
            p_class_id,
            p_member_id,
            CURDATE(),
            'registered'
        );
    END IF;

END$$

DELIMITER ;

-- -----------------------------------------------------
-- procedure add_membership_payment
-- -----------------------------------------------------

DELIMITER $$
USE `mydb`$$
CREATE PROCEDURE add_membership_payment (
    IN p_member_id INT,
    IN p_membership_id INT,
    IN p_amount DECIMAL(8,2)
)
BEGIN
    DECLARE mm_id INT;

    -- Get active membership record
    SELECT member_membership_id INTO mm_id
    FROM member_membership
    WHERE member_id = p_member_id
      AND membership_id = p_membership_id
      AND (end_date IS NULL OR end_date >= CURDATE())
    LIMIT 1;

    IF mm_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No active membership found';
    ELSE
        INSERT INTO payments (
            member_id,
            amount,
            payment_date,
            payment_method,
            status,
            payment_type,
            member_membership_id
        )
        VALUES (
            p_member_id,
            p_amount,
            CURDATE(),
            'card',
            'completed',
            'membership',
            mm_id
        );
    END IF;

END;$$

DELIMITER ;

-- -----------------------------------------------------
-- View `mydb`.`active_memberships`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`active_memberships`;
USE `mydb`;
CREATE  OR REPLACE VIEW `active_memberships` AS
SELECT
	m.member_id,
	m.name,
    m.email,
    ms.membership_name,
    mm.start_date,
    mm.end_date
FROM 
	member m
JOIN member_membership mm ON m.member_id = mm.member_id
JOIN memberships ms ON mm.membership_id = ms.membership_id
WHERE mm.end_date IS NULL OR mm.end_date >= CURDATE();

-- -----------------------------------------------------
-- View `mydb`.`class_enrollment_summary`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`class_enrollment_summary`;
USE `mydb`;
CREATE  OR REPLACE VIEW `class_enrollment_summary` AS
SELECT
	c.class_id,
    ct.class_name,
    c.scheduled_time,
    c.capacity,
    COUNT(ce.member_id) AS enrolled_count,
    (c.capacity - COUNT(ce.member_id)) AS spots_remaining
FROM classes c
JOIN class_type ct ON c.class_type_id = ct.class_type_id
LEFT JOIN class_enrollment ce ON c.class_id = ce.class_id
GROUP BY c.class_id, ct.class_name, c.scheduled_time, c.capacity;

-- -----------------------------------------------------
-- View `mydb`.`member_payment_details`
-- -----------------------------------------------------
DROP TABLE IF EXISTS `mydb`.`member_payment_details`;
USE `mydb`;
CREATE  OR REPLACE VIEW `member_payment_details` AS
SELECT
	m.name AS member_name,
    p.payment_id,
    p.amount,
    p.payment_type,
    p.status,
    ms.membership_name,
    ct.class_name
FROM payments p
JOIN member m ON p.member_id = m.member_id
LEFT JOIN member_membership mm ON p.member_membership_id = mm.member_membership_id
LEFT JOIN memberships ms ON mm.membership_id = ms.membership_id
LEFT JOIN class_enrollment ce ON p.class_enrollment_id = ce.class_enrollment_id
LEFT JOIN classes c ON ce.class_id = c.class_id
LEFT JOIN class_type ct ON c.class_type_id = ct.class_type_id;

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;
